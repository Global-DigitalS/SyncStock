"""
Scraper para PCComponentes.com
Extrae precios usando JSON-LD y como fallback el DOM.
Soporta búsqueda por EAN y por texto.
"""
import json
import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from services.scrapers.base import BaseScraper, ScrapedProduct, SearchResult
from services.scrapers.generic import _clean_price, _extract_jsonld_product, _extract_price_from_jsonld
from services.scrapers.http_client import scraper_client

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.pccomponentes.com"
_SEARCH_URL = f"{_BASE_URL}/buscar/"


class PCComponentesScraper(BaseScraper):
    """Scraper especializado para pccomponentes.com"""

    channel = "pccomponentes"
    display_name = "PCComponentes"

    async def search_by_ean(self, ean: str) -> SearchResult:
        """Busca por EAN en PCComponentes."""
        return await self.search_by_query(ean)

    async def search_by_query(self, query: str) -> SearchResult:
        """Busca productos en PCComponentes."""
        url = f"{_SEARCH_URL}?query={quote_plus(query)}"
        html = await scraper_client.fetch(url)

        if not html:
            return SearchResult(query=query, error="No se pudo acceder a PCComponentes")

        soup = BeautifulSoup(html, "lxml")
        products = []

        # Extraer productos de los resultados de búsqueda
        # PCComponentes usa artículos con data attributes
        articles = soup.select("article[data-product-id], div.c-product-card")

        for article in articles[:10]:  # Limitar a 10 resultados
            try:
                product = self._parse_search_result(article)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parseando resultado de PCComponentes: {e}")
                continue

        # Si no encontramos con selectores, intentar JSON-LD de la página
        if not products:
            products = self._parse_search_jsonld(soup)

        return SearchResult(
            products=products,
            total_found=len(products),
            query=query,
        )

    def _parse_search_result(self, article) -> ScrapedProduct | None:
        """Parsea un artículo de resultado de búsqueda."""
        # Nombre
        name_el = article.select_one(
            "h3, .c-product-card__title, a[data-product-name], [class*='product-card__title']"
        )
        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            # Intentar data attribute
            name = article.get("data-product-name", "")
        if not name:
            return None

        # Precio
        price = None
        price_el = article.select_one(
            "[data-product-price], .c-product-card__price, [class*='price']"
        )
        if price_el:
            price_attr = price_el.get("data-product-price")
            if price_attr:
                price = _clean_price(price_attr)
            else:
                price = _clean_price(price_el.get_text())
        # Fallback: data attribute del artículo
        if not price:
            price = _clean_price(article.get("data-product-price", ""))
        if not price:
            return None

        # URL
        link = article.select_one("a[href]")
        url = None
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                url = f"{_BASE_URL}{href}"
            elif href.startswith("http"):
                url = href

        # Disponibilidad
        availability = "in_stock"
        avail_el = article.select_one("[class*='out-of-stock'], [class*='agotado']")
        if avail_el:
            availability = "out_of_stock"

        return ScrapedProduct(
            product_name=name,
            price=price,
            url=url,
            availability=availability,
        )

    def _parse_search_jsonld(self, soup: BeautifulSoup) -> list:
        """Intenta extraer productos desde JSON-LD en la página de búsqueda."""
        products = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue

                # ItemList con productos
                if item.get("@type") == "ItemList":
                    for elem in item.get("itemListElement", []):
                        prod_item = elem.get("item", elem)
                        if prod_item.get("@type") == "Product":
                            p = self._jsonld_to_product(prod_item)
                            if p:
                                products.append(p)

                # Producto individual
                elif item.get("@type") == "Product":
                    p = self._jsonld_to_product(item)
                    if p:
                        products.append(p)

        return products[:10]

    def _jsonld_to_product(self, item: dict) -> ScrapedProduct | None:
        """Convierte un item JSON-LD Product a ScrapedProduct."""
        name = item.get("name")
        offers = item.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        price = None
        for field in ("price", "lowPrice"):
            try:
                price = round(float(offers.get(field, "")), 2)
                break
            except (ValueError, TypeError):
                continue

        if not name or not price:
            return None

        url = item.get("url") or offers.get("url")
        ean = item.get("gtin13") or item.get("gtin")
        sku = item.get("sku")

        availability_raw = offers.get("availability", "")
        availability = "in_stock"
        if "OutOfStock" in availability_raw:
            availability = "out_of_stock"

        return ScrapedProduct(
            product_name=name,
            price=price,
            url=url,
            ean=ean,
            sku=sku,
            availability=availability,
            currency=offers.get("priceCurrency", "EUR"),
        )

    async def parse_product_page(self, url: str) -> ScrapedProduct | None:
        """Extrae datos de una página de producto de PCComponentes."""
        html = await scraper_client.fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        # 1. JSON-LD (más fiable)
        jsonld = _extract_jsonld_product(soup)
        if jsonld:
            price = _extract_price_from_jsonld(jsonld)
            if price:
                offers = jsonld.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                original_price = None
                # PCComponentes a veces muestra precio "antes"
                old_price_el = soup.select_one("[class*='old-price'], [class*='price--old'], del")
                if old_price_el:
                    original_price = _clean_price(old_price_el.get_text())

                availability_raw = offers.get("availability", "")
                availability = "in_stock"
                if "OutOfStock" in availability_raw:
                    availability = "out_of_stock"

                return ScrapedProduct(
                    product_name=jsonld.get("name", ""),
                    price=price,
                    original_price=original_price,
                    currency=offers.get("priceCurrency", "EUR"),
                    url=url,
                    ean=jsonld.get("gtin13") or jsonld.get("gtin"),
                    sku=jsonld.get("sku"),
                    availability=availability,
                )

        # 2. Fallback: parsear el DOM directamente
        name_el = soup.select_one("h1.pdp-title, h1[data-product-name], h1")
        price_el = soup.select_one(
            "[id='precio-main'], [data-product-price], .precioMain, [class*='pdp-price']"
        )

        if name_el and price_el:
            price = _clean_price(
                price_el.get("data-product-price", "") or price_el.get_text()
            )
            if price:
                return ScrapedProduct(
                    product_name=name_el.get_text(strip=True),
                    price=price,
                    url=url,
                )

        logger.info(f"No se pudieron extraer datos de PCComponentes: {url}")
        return None
