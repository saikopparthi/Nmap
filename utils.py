import re
import ipaddress
from typing import Dict


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_hostname(hostname: str) -> bool:
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def is_valid_target(target: str) -> bool:
    return is_valid_ip(target) or is_valid_hostname(target)


def sanitize_input(input_str: str) -> str:
    # Remove any characters that aren't alphanumeric, dots, hyphens, or colons (for IPv6)
    return re.sub(r'[^\w.\-:]', '', input_str)
