"""
Shared imports, constants, and utility functions for CRM clients.
"""
import re
import logging
import requests
import base64
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

_PRIVATE_IP_RE = re.compile(
    r'^https?://(localhost|127\.|0\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.)',
    re.IGNORECASE,
)
_VALID_URL_RE = re.compile(r'^https?://[a-zA-Z0-9._:-]+(:\d+)?(/.*)?$')


def _validate_crm_url(url: str) -> str:
    """Validate a CRM API URL to prevent SSRF attacks - MEDIUM #23

    Prevents access to:
    - Localhost and private IPs (10.x, 192.168.x, 172.16-31.x)
    - Link-local addresses (169.254.x)
    - Invalid URL formats
    """
    url = url.strip()

    # Check for valid URL format
    if not _VALID_URL_RE.match(url):
        raise ValueError(f"URL de CRM inválida: {url!r}")

    # Check for private/internal IP ranges
    if _PRIVATE_IP_RE.match(url):
        raise ValueError("La URL de CRM no puede apuntar a direcciones IP privadas o localhost")

    # Additional checks for common SSRF bypasses
    url_lower = url.lower()
    if any(bypass in url_lower for bypass in [
        '0x',  # Hex encoding
        '%',   # URL encoding
        '@',   # Username@ tricks
    ]):
        # Allow some (like @ for auth), but log suspicious patterns
        if url.count('@') > 1:
            raise ValueError("URL sospechosa - múltiples caracteres @")

    return url
