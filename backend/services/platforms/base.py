"""
Shared imports and base exception for platform integrations.
"""
import logging
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PlatformIntegrationError(Exception):
    """Custom exception for platform integration errors"""
    pass
