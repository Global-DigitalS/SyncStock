"""
Multi-Platform eCommerce Integration Service
Supports: WooCommerce, PrestaShop, Shopify, Wix, Magento

This package provides platform client classes and a factory function.
All public symbols are re-exported here for backward compatibility:

    from services.platforms import get_platform_client
    from services.platforms import PrestaShopClient, ShopifyClient
    from services.platforms import MagentoClient, WixClient
    from services.platforms import PlatformIntegrationError
"""

from .base import PlatformIntegrationError
from .prestashop import PrestaShopClient
from .shopify_client import ShopifyClient
from .magento import MagentoClient
from .wix import WixClient
from .factory import get_platform_client

__all__ = [
    "PlatformIntegrationError",
    "PrestaShopClient",
    "ShopifyClient",
    "MagentoClient",
    "WixClient",
    "get_platform_client",
]
