"""
Clase base abstracta para scrapers de precios de competidores.
Cada canal (amazon_es, pccomponentes, etc.) implementa esta interfaz.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Resultado de un scraping de producto individual."""
    product_name: str
    price: float
    currency: str = "EUR"
    original_price: Optional[float] = None  # Precio tachado
    url: Optional[str] = None
    ean: Optional[str] = None
    sku: Optional[str] = None
    seller: Optional[str] = None
    availability: str = "in_stock"  # in_stock, out_of_stock, limited
    image_url: Optional[str] = None


@dataclass
class SearchResult:
    """Resultado de una búsqueda de producto en un competidor."""
    products: List[ScrapedProduct] = field(default_factory=list)
    total_found: int = 0
    query: str = ""
    error: Optional[str] = None


class BaseScraper(ABC):
    """
    Interfaz base para todos los scrapers de precios.

    Cada scraper debe implementar al menos:
    - search_by_ean(): búsqueda por código EAN/GTIN
    - search_by_query(): búsqueda por texto libre (nombre, SKU)
    - parse_product_page(): extracción de datos de una página de producto
    """

    channel: str = "generic"
    display_name: str = "Genérico"

    @abstractmethod
    async def search_by_ean(self, ean: str) -> SearchResult:
        """Busca un producto por código EAN en el sitio del competidor."""
        ...

    @abstractmethod
    async def search_by_query(self, query: str) -> SearchResult:
        """Busca un producto por texto libre."""
        ...

    @abstractmethod
    async def parse_product_page(self, url: str) -> Optional[ScrapedProduct]:
        """Extrae datos de precio de una URL de producto específica."""
        ...

    async def search_product(
        self,
        ean: Optional[str] = None,
        sku: Optional[str] = None,
        name: Optional[str] = None,
    ) -> SearchResult:
        """
        Estrategia de búsqueda en cascada:
        1. Si hay EAN, buscar por EAN (más preciso)
        2. Si hay SKU, buscar por SKU
        3. Si hay nombre, buscar por nombre (menos preciso)
        """
        if ean:
            result = await self.search_by_ean(ean)
            if result.products:
                return result

        if sku:
            result = await self.search_by_query(sku)
            if result.products:
                return result

        if name:
            result = await self.search_by_query(name)
            return result

        return SearchResult(error="No se proporcionó EAN, SKU ni nombre para buscar")
