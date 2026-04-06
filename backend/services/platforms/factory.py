"""
Factory function for creating platform clients.
"""

from .magento import MagentoClient
from .prestashop import PrestaShopClient
from .shopify_client import ShopifyClient
from .wix import WixClient


def get_platform_client(config: dict):
    """Factory function to get the appropriate platform client"""
    platform = config.get('platform', 'woocommerce')

    if platform == 'prestashop':
        return PrestaShopClient(
            store_url=config.get('store_url', ''),
            api_key=config.get('api_key', '')
        )
    elif platform == 'shopify':
        return ShopifyClient(
            store_url=config.get('store_url', ''),
            access_token=config.get('access_token', ''),
            api_version=config.get('api_version', '2024-10')
        )
    elif platform == 'magento':
        return MagentoClient(
            store_url=config.get('store_url', ''),
            access_token=config.get('access_token', ''),
            store_code=config.get('store_code', 'default')
        )
    elif platform == 'wix':
        return WixClient(
            store_url=config.get('store_url', ''),
            api_key=config.get('api_key', ''),
            site_id=config.get('site_id', '')
        )
    else:
        # WooCommerce - return None to use existing implementation
        return None
