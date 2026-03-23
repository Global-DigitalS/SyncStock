"""
CRM client factory function and platform classification constants.
"""
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


def create_crm_client(platform: str, config: dict):
    """Factory function to create the appropriate CRM client based on platform"""
    if platform == "dolibarr":
        return DolibarrClient(api_url=config.get("api_url", ""), api_key=config.get("api_key", ""))
    elif platform == "odoo":
        return OdooClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    elif platform == "hubspot":
        return HubSpotClient(api_token=config.get("api_token", ""))
    elif platform == "salesforce":
        return SalesforceClient(
            api_url=config.get("api_url", ""),
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            api_token=config.get("api_token", "")
        )
    elif platform == "zoho":
        return ZohoClient(
            api_url=config.get("api_url", ""),
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            api_token=config.get("api_token", "")
        )
    elif platform == "pipedrive":
        return PipedriveClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    elif platform == "monday":
        return MondayClient(api_token=config.get("api_token", ""), board_id=config.get("board_id", ""))
    elif platform == "freshsales":
        return FreshsalesClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    return None


# Platforms that support full sync (products, suppliers, orders)
FULL_SYNC_PLATFORMS = {"dolibarr", "odoo"}
# Platforms that support basic sync (products only via generic pattern)
BASIC_SYNC_PLATFORMS = {"hubspot", "salesforce", "zoho", "pipedrive", "monday", "freshsales"}
