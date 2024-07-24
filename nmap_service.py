from typing import List, Dict
from interfaces import Scanner, ResultParser, DatabaseOperations


class NmapService:

    def __init__(self, scanner: Scanner, result_parser: ResultParser,
                 db_manager: DatabaseOperations):
        self.scanner = scanner
        self.result_parser = result_parser
        self.db_manager = db_manager

    def run_scan(self, target: str, options: Dict[str, str]) -> str:
        result, command = self.scanner.scan(target, options)
        self.db_manager.save_scan_result(target, options, result, command)
        return result

    def get_recent_scans(self, target: str, limit: int = 5) -> List[Dict]:
        return self.db_manager.get_recent_scans(target, limit)

    def get_scan_changes(self, target: str) -> Dict:
        recent_scans = self.db_manager.get_recent_scans(target, 2)
        if len(recent_scans) < 2:
            return {"error": "Not enough scans to compare"}

        new_scan = self.result_parser.parse(recent_scans[0]["result"])
        old_scan = self.result_parser.parse(recent_scans[1]["result"])

        changes = {
            "ip_change": new_scan['ip'] != old_scan['ip'],
            "new_ip": new_scan['ip'],
            "old_ip": old_scan['ip'],
            "latency_change": new_scan['latency'] != old_scan['latency'],
            "new_latency": new_scan['latency'],
            "old_latency": old_scan['latency'],
            "os_change": new_scan['os_detection'] != old_scan['os_detection'],
            "new_os": new_scan['os_detection'],
            "old_os": old_scan['os_detection'],
            "newly_opened": [],
            "newly_closed": [],
            "changed_state": [],
            "changed_services": [],
            "script_changes": {}
        }

        self._compare_ports(new_scan, old_scan, changes)
        self._compare_scripts(new_scan, old_scan, changes)

        return changes

    def _compare_ports(self, new_scan: Dict, old_scan: Dict, changes: Dict):
        all_ports = set(new_scan['ports'].keys()) | set(
            old_scan['ports'].keys())

        for port in all_ports:
            new_port_info = new_scan['ports'].get(port)
            old_port_info = old_scan['ports'].get(port)

            if not old_port_info and new_port_info:
                changes['newly_opened'].append(
                    f"{port}: {new_port_info['service']}")
            elif not new_port_info and old_port_info:
                changes['newly_closed'].append(
                    f"{port}: {old_port_info['service']}")
            elif new_port_info and old_port_info:
                if new_port_info['state'] != old_port_info['state']:
                    changes['changed_state'].append(
                        f"{port}: {old_port_info['state']} -> {new_port_info['state']}"
                    )
                if new_port_info['service'] != old_port_info['service']:
                    changes['changed_services'].append(
                        f"{port}: {old_port_info['service']} -> {new_port_info['service']}"
                    )

    def _compare_scripts(self, new_scan: Dict, old_scan: Dict, changes: Dict):
        new_scripts = new_scan.get('script_results', {})
        old_scripts = old_scan.get('script_results', {})

        all_scripts = set(new_scripts.keys()) | set(old_scripts.keys())

        for script in all_scripts:
            if script not in old_scripts:
                changes['script_changes'][script] = "New script result"
            elif script not in new_scripts:
                changes['script_changes'][script] = "Script no longer present"
            elif new_scripts[script] != old_scripts[script]:
                changes['script_changes'][script] = "Script result changed"
