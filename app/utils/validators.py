"""
URL validation and SSRF protection utilities.
"""

import ipaddress
import socket
from urllib.parse import urlparse


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a URL and check SSRF safety.
    Returns (is_valid, error_message).
    """
    url = url.strip()

    # Basic format check
    parsed = urlparse(url)

    # Scheme check
    if parsed.scheme not in ("http", "https"):
        return False, "Only http and https URLs are allowed."

    if not parsed.netloc or parsed.username is not None or parsed.password is not None:
        return False, "Invalid URL format."
    try:
        port = parsed.port
    except ValueError:
        return False, "Invalid URL port."
    expected_port = 80 if parsed.scheme == "http" else 443
    if port not in (None, expected_port):
        return False, "Only standard HTTP and HTTPS ports are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "Could not determine hostname from URL."

    # Block localhost / loopback by name
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return False, "Access to local addresses is not allowed."

    # Resolve hostname and check against private ranges (SSRF protection)
    try:
        resolved_ips = socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80))
    except (socket.gaierror, UnicodeError):
        return False, f"Could not resolve hostname: {hostname}"

    if not resolved_ips:
        return False, f"Could not resolve hostname: {hostname}"

    for info in resolved_ips:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
            if not ip.is_global:
                return False, "Access to private/internal addresses is not allowed."
        except ValueError:
            pass  # non-IP address, skip

    return True, ""
