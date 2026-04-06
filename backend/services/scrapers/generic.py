"""
Scraper genérico basado en JSON-LD (Schema.org Product).
Funciona con cualquier tienda que implemente datos estructurados.
Fallback: extrae precios de microdata y meta tags OpenGraph.
"""
import json
import logging
import re

from bs4 import BeautifulSoup

from services.scrapers.base import BaseScraper, ScrapedProduct, SearchResult
from services.scrapers.http_client import scraper_client

logger = logging.getLogger(__name__)


def _clean_price(raw: str) -> float | None:
    """Limpia y convierte un string de precio a float."""
    if not raw:
        return None
    # Eliminar símbolos de moneda y espacios
    cleaned = re.sub(r"[€$£\s]", "", raw.strip())
    # Manejar formato europeo: 1.234,56 -> 1234.56
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return None


def _extract_jsonld_product(soup: BeautifulSoup) -> dict | None:
    """Extrae datos de producto desde JSON-LD (Schema.org)."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # Puede ser un objeto directo o un array
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                # Buscar Product directamente
                if item.get("@type") == "Product":
                    return item
                # Buscar dentro de @graph
                graph = item.get("@graph", [])
                for node in graph:
                    if isinstance(node, dict) and node.get("@type") == "Product":
                        return node
    return None


def _extract_price_from_jsonld(product: dict) -> float | None:
    """Extrae el precio de un objeto JSON-LD Product."""
    offers = product.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    # Intentar varios campos de precio
    for price_field in ("price", "lowPrice"):
        price = offers.get(price_field)
        if price is not None:
            try:
                return round(float(price), 2)
            except (ValueError, TypeError):
                continue

    return None


def _extract_from_meta(soup: BeautifulSoup) -> ScrapedProduct | None:
    """Fallback: extrae datos de meta tags OG y product."""
    price = None
    name = None

    # Meta tags de producto
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "") or meta.get("name", "")
        content = meta.get("content", "")

        if prop in ("og:title", "product:title"):
            name = content
        elif prop in ("product:price:amount", "og:price:amount"):
            price = _clean_price(content)

    if price and name:
        return ScrapedProduct(
            product_name=name,
            price=price,
        )
    return None


class GenericScraper(BaseScraper):
    """
    Scraper genérico que extrae precios usando datos estructurados.
    Funciona con tiendas que implementan JSON-LD Schema.org Product.
    """

    channel = "web_directa"
    display_name = "Web Directa (genérico)"

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    async def search_by_ean(self, ean: str) -> SearchResult:
        """El scraper genérico no soporta búsqueda; requiere URLs directas."""
        return SearchResult(query=ean, error="El scraper genérico no soporta búsqueda por EAN")

    async def search_by_query(self, query: str) -> SearchResult:
        """El scraper genérico no soporta búsqueda; requiere URLs directas."""
        return SearchResult(query=query, error="El scraper genérico no soporta búsqueda por texto")

    async def parse_product_page(self, url: str) -> ScrapedProduct | None:
        """
        Extrae datos de precio de una URL de producto.
        Estrategia en cascada:
        1. JSON-LD (Schema.org Product)
        2. Meta tags (OG/product)
        """
        html = await scraper_client.fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        # 1. Intentar JSON-LD
        jsonld = _extract_jsonld_product(soup)
        if jsonld:
            price = _extract_price_from_jsonld(jsonld)
            if price:
                name = jsonld.get("name", "")
                offers = jsonld.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                ean = jsonld.get("gtin13") or jsonld.get("gtin") or jsonld.get("gtin14")
                sku = jsonld.get("sku") or jsonld.get("mpn")

                availability_raw = offers.get("availability", "")
                if "InStock" in availability_raw:
                    availability = "in_stock"
                elif "OutOfStock" in availability_raw:
                    availability = "out_of_stock"
                elif "LimitedAvailability" in availability_raw:
                    availability = "limited"
                else:
                    availability = "in_stock"

                original_price = None
                high_price = offers.get("highPrice")
                if high_price:
                    try:
                        hp = float(high_price)
                        if hp > price:
                            original_price = hp
                    except (ValueError, TypeError):
                        pass

                return ScrapedProduct(
                    product_name=name,
                    price=price,
                    original_price=original_price,
                    currency=offers.get("priceCurrency", "EUR"),
                    url=url,
                    ean=ean,
                    sku=sku,
                    seller=offers.get("seller", {}).get("name") if isinstance(offers.get("seller"), dict) else None,
                    availability=availability,
                )

        # 2. Fallback: meta tags
        meta_product = _extract_from_meta(soup)
        if meta_product:
            meta_product.url = url
            return meta_product

        logger.info(f"No se pudieron extraer datos de producto de {url}")
        return None
