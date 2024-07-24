import sqlite3
import json
from typing import List, Dict
from interfaces import DatabaseOperations


class SQLiteDatabase(DatabaseOperations):

    def __init__(self, db_name: str = 'nmap_scans.db'):
        self.db_name = db_name

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS scans
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          target TEXT,
                          options TEXT,
                          result TEXT,
                          parsed_result TEXT,
                          command TEXT,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()

    def save_scan_result(self, target: str, options: Dict[str, str],
                         result: str, parsed_result: Dict, command: str):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO scans (target, options, result, parsed_result, command) VALUES (?, ?, ?, ?, ?)",
                (target, json.dumps(options), result,
                 json.dumps(parsed_result), command))
            conn.commit()

    def get_recent_scans(self, target: str, limit: int = 5) -> List[Dict]:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, target, options, parsed_result, command, timestamp FROM scans WHERE target = ? ORDER BY timestamp DESC LIMIT ?",
                (target, limit))
            rows = c.fetchall()
        return [{
            "id": row[0],
            "target": row[1],
            "options": json.loads(row[2]),
            "result": json.loads(row[3]),
            "command": row[4],
            "timestamp": row[5]
        } for row in rows]
