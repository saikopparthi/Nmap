from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class Scanner(ABC):

    @abstractmethod
    def scan(self, target: str, options: Dict[str, str]) -> Tuple[str, str]:
        pass


class ResultParser(ABC):

    @abstractmethod
    def parse(self, output: str) -> Dict:
        pass


class DatabaseOperations(ABC):

    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def save_scan_result(self, target: str, options: Dict[str, str],
                         result: str, command: str):
        pass

    @abstractmethod
    def get_recent_scans(self, target: str, limit: int = 5) -> List[Dict]:
        pass
