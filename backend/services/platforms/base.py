"""
Shared imports and base exception for platform integrations.
"""
import logging

logger = logging.getLogger(__name__)


class PlatformIntegrationError(Exception):
    """Custom exception for platform integration errors"""
    pass
