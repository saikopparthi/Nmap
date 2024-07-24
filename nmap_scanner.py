import shutil
import subprocess
import logging
from typing import Dict, Tuple
from interfaces import Scanner

logger = logging.getLogger(__name__)


class NmapScanner(Scanner):

    def __init__(self):
        self.nmap_path = shutil.which('nmap')
        if self.nmap_path is None:
            raise EnvironmentError("Nmap executable not found in $PATH.")
        logger.info(f"Nmap executable found at: {self.nmap_path}")

    def scan(self, target: str, options: Dict[str, str]) -> Tuple[str, str]:
        command = [self.nmap_path]

        for key, value in options.items():
            if value is None:
                command.append(key)
            else:
                command.extend([key, value])

        command.append(target)

        command_str = ' '.join(command)
        logger.info(f"Running Nmap command: {command_str}")

        try:
            result = subprocess.run(command,
                                    capture_output=True,
                                    text=True,
                                    timeout=300)  # 5-minute timeout
            logger.info(
                f"Nmap command completed with return code: {result.returncode}"
            )
            logger.info(f"Nmap stdout: {result.stdout}")
            logger.info(f"Nmap stderr: {result.stderr}")
            if result.returncode != 0:
                raise Exception(f"Nmap error: {result.stderr}")
            return result.stdout, command_str
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out after 5 minutes")
            raise Exception("Nmap scan timed out")
        except Exception as e:
            logger.error(f"Error during Nmap scan: {str(e)}")
            raise
