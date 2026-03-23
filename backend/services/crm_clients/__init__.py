"""
CRM Client implementations for all supported platforms.
Dolibarr, Odoo, HubSpot, Salesforce, Zoho, Pipedrive, Monday, Freshsales.

This package re-exports everything for backward compatibility so that
existing imports like `from services.crm_clients import DolibarrClient`
continue to work unchanged.
"""
from .base import _validate_crm_url, _PRIVATE_IP_RE, _VALID_URL_RE
from .dolibarr import DolibarrClient
from .odoo import OdooClient
from .basic_clients import (
    HubSpotClient,
    SalesforceClient,
    ZohoClient,
    PipedriveClient,
    MondayClient,
    FreshsalesClient,
)
from .factory import create_crm_client, FULL_SYNC_PLATFORMS, BASIC_SYNC_PLATFORMS

__all__ = [
    # Base utilities
    "_validate_crm_url",
    "_PRIVATE_IP_RE",
    "_VALID_URL_RE",
    # Full-sync clients
    "DolibarrClient",
    "OdooClient",
    # Basic-sync clients
    "HubSpotClient",
    "SalesforceClient",
    "ZohoClient",
    "PipedriveClient",
    "MondayClient",
    "FreshsalesClient",
    # Factory
    "create_crm_client",
    "FULL_SYNC_PLATFORMS",
    "BASIC_SYNC_PLATFORMS",
]
