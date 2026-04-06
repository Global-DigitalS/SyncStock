"""
SKU Cache - Efficient lookup cache for product identification during sync

Optimizes:
- Bulk lookups of products by SKU instead of N individual queries
- In-memory caching of product metadata (price, stock)
- Chunk-based population from MongoDB
"""
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from services.database import db

logger = logging.getLogger(__name__)


@dataclass
class CachedProduct:
    """Cached product metadata"""
    id: str
    sku: str
    price: float = 0.0
    stock: int = 0
    category: str = ""
    brand: str = ""


class SKUCache:
    """
    In-memory cache for SKU → product lookup during sync operations.

    Dramatically reduces database queries by:
    1. Loading SKUs in batches instead of individually
    2. Caching product metadata (id, price, stock)
    3. Tracking which SKUs have been checked

    Memory usage: ~200 bytes per product
    With 1M products: ~200 MB (acceptable during sync)
    """

    def __init__(self, supplier_id: str, user_id: str):
        self.supplier_id = supplier_id
        self.user_id = user_id

        # Main cache: sku -> CachedProduct
        self.products: Dict[str, CachedProduct] = {}

        # Track which SKUs we've checked but don't exist
        self.missing_skus: Set[str] = set()

        # Stats
        self.hits = 0
        self.misses = 0
        self.db_fetches = 0

    async def populate_batch(self, skus: List[str]) -> int:
        """
        Load a batch of SKUs from MongoDB.

        Returns: Number of products loaded
        """
        if not skus:
            return 0

        # Filter out already-cached SKUs
        uncached_skus = [
            sku for sku in skus
            if sku not in self.products and sku not in self.missing_skus
        ]

        if not uncached_skus:
            return 0

        self.db_fetches += 1
        logger.debug(f"SKUCache: Fetching {len(uncached_skus)} uncached SKUs from DB")

        try:
            # SECURITY FIX: Limit unbounded query to prevent OOM
            # Fetch products with safeguard - if we're loading too many, something is wrong
            MAX_PRODUCTS_PER_BATCH = 100000

            docs = await db.products.find(
                {
                    "supplier_id": self.supplier_id,
                    "user_id": self.user_id,
                    "sku": {"$in": uncached_skus}
                },
                {
                    "id": 1,
                    "sku": 1,
                    "price": 1,
                    "stock": 1,
                    "category": 1,
                    "brand": 1,
                    "_id": 0
                }
            ).limit(MAX_PRODUCTS_PER_BATCH).to_list(MAX_PRODUCTS_PER_BATCH)

            if len(docs) >= MAX_PRODUCTS_PER_BATCH:
                logger.error(f"SKUCache: Retrieved {MAX_PRODUCTS_PER_BATCH}+ products, may be incomplete")

            # Cache results
            found_skus = set()
            for doc in docs:
                sku = doc.get("sku")
                cached = CachedProduct(
                    id=doc.get("id"),
                    sku=sku,
                    price=doc.get("price", 0.0),
                    stock=doc.get("stock", 0),
                    category=doc.get("category", ""),
                    brand=doc.get("brand", "")
                )
                self.products[sku] = cached
                found_skus.add(sku)

            # Mark missing SKUs
            for sku in uncached_skus:
                if sku not in found_skus:
                    self.missing_skus.add(sku)

            logger.debug(f"SKUCache: Loaded {len(found_skus)} products, {len(uncached_skus) - len(found_skus)} not found")
            return len(found_skus)

        except Exception as e:
            logger.error(f"Error populating SKU cache: {e}")
            return 0

    def get(self, sku: str) -> Optional[CachedProduct]:
        """
        Get a cached product by SKU.

        Returns: CachedProduct or None if not found
        """
        if sku in self.products:
            self.hits += 1
            return self.products[sku]

        if sku in self.missing_skus:
            self.misses += 1
            return None

        # Not cached yet
        return None

    def exists(self, sku: str) -> bool:
        """Check if a product exists (was found in previous fetches)"""
        return sku in self.products

    def get_price_stock(self, sku: str) -> tuple:
        """Get (price, stock) for a SKU"""
        product = self.get(sku)
        if product:
            return (product.price, product.stock)
        return (0.0, 0)

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_lookups = self.hits + self.misses
        hit_rate = (self.hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "cached_products": len(self.products),
            "missing_skus": len(self.missing_skus),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "db_fetches": self.db_fetches,
            "memory_mb": self._estimate_memory_mb()
        }

    def _estimate_memory_mb(self) -> float:
        """Estimate memory usage in MB"""
        # ~200 bytes per CachedProduct
        product_bytes = len(self.products) * 200
        # ~50 bytes per missing SKU
        missing_bytes = len(self.missing_skus) * 50
        total_mb = (product_bytes + missing_bytes) / (1024 * 1024)
        return round(total_mb, 2)

    def clear(self):
        """Clear the cache"""
        self.products.clear()
        self.missing_skus.clear()
        self.hits = 0
        self.misses = 0
        self.db_fetches = 0
