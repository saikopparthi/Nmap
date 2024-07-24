import re
from typing import Dict
from interfaces import ResultParser

class NmapResultParser(ResultParser):
    def parse(self, output: str) -> Dict:
        result = {
            'ip': None,
            'hostname': None,
            'ports': {},
            'os_detection': None,
            'latency': None,
            'script_results': {}
        }

        lines = output.split('\n')
        for line in lines:
            if 'Nmap scan report for' in line:
                parts = line.split()
                result['hostname'] = parts[4]
                result['ip'] = parts[5].strip('()') if len(parts) > 5 else parts[4]
            elif 'Host is up' in line:
                latency_match = re.search(r'\((.*?)\s+latency\)', line)
                result['latency'] = latency_match.group(1) if latency_match else None
            elif '/tcp' in line or '/udp' in line:
                parts = line.split()
                port, protocol = parts[0].split('/')
                state = parts[1]
                service = ' '.join(parts[2:]) if len(parts) > 2 else ''
                result['ports'][port] = {
                    'protocol': protocol,
                    'state': state,
                    'service': service
                }
            elif 'OS details:' in line:
                result['os_detection'] = line.split(':', 1)[1].strip()
            elif '|' in line:  # Script output
                script_name = line.split()[0].strip('|_')
                script_output = line.split(':', 1)[1].strip() if ':' in line else line.split('|', 1)[1].strip()
                result['script_results'][script_name] = script_output

        return resultf