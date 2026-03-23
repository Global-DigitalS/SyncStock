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
    r'^https?://(localhost|127\.|0\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)',
    re.IGNORECASE,
)
_VALID_URL_RE = re.compile(r'^https?://[a-zA-Z0-9._-]+(:\d+)?(/.*)?$')


def _validate_crm_url(url: str) -> str:
    """Validate a CRM API URL to prevent SSRF attacks."""
    url = url.strip()
    if not _VALID_URL_RE.match(url):
        raise ValueError(f"URL de CRM inválida: {url!r}")
    if _PRIVATE_IP_RE.match(url):
        raise ValueError("La URL de CRM no puede apuntar a direcciones IP privadas o localhost")
    return url
