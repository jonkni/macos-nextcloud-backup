"""Network connectivity checks."""

import socket
from urllib.parse import urlparse
from typing import Optional


def is_network_available(timeout: int = 5) -> bool:
    """Check if general network connectivity is available.

    Args:
        timeout: Timeout in seconds

    Returns:
        True if network is available
    """
    try:
        # Try to connect to common DNS servers
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except (socket.error, socket.timeout):
        return False


def can_reach_host(url: str, timeout: int = 10) -> bool:
    """Check if a specific host is reachable.

    Args:
        url: URL to check (e.g., https://share.educloud.no)
        timeout: Timeout in seconds

    Returns:
        True if host is reachable
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)

        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, socket.timeout, socket.gaierror):
        return False


def check_nextcloud_connectivity(nextcloud_url: str, timeout: int = 10) -> dict:
    """Check connectivity to Nextcloud instance.

    Args:
        nextcloud_url: Nextcloud base URL
        timeout: Timeout in seconds

    Returns:
        Dictionary with connectivity status
    """
    result = {
        'network_available': False,
        'nextcloud_reachable': False,
        'error': None,
    }

    # Check general network
    result['network_available'] = is_network_available(timeout=timeout)
    if not result['network_available']:
        result['error'] = 'No network connection'
        return result

    # Check Nextcloud specifically
    result['nextcloud_reachable'] = can_reach_host(nextcloud_url, timeout=timeout)
    if not result['nextcloud_reachable']:
        result['error'] = f'Cannot reach {nextcloud_url}'
        return result

    return result
