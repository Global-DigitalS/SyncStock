"""
Registro de scrapers por canal.
Importar get_scraper() para obtener el scraper adecuado para un canal.
"""
from typing import Optional

from services.scrapers.base import BaseScraper
from services.scrapers.generic import GenericScraper
from services.scrapers.pccomponentes import PCComponentesScraper


def get_scraper(channel: str, base_url: str = "") -> BaseScraper | None:
    """
    Devuelve la instancia de scraper apropiada para el canal.

    Args:
        channel: Identificador del canal (pccomponentes, web_directa, etc.)
        base_url: URL base del competidor (necesario para genérico)

    Returns:
        Instancia del scraper o None si no hay implementación.
    """
    scrapers = {
        "pccomponentes": PCComponentesScraper,
        # Futuros scrapers:
        # "amazon_es": AmazonEsScraper,
        # "mediamarkt": MediaMarktScraper,
    }

    scraper_class = scrapers.get(channel)
    if scraper_class:
        return scraper_class()

    # Fallback: scraper genérico para web_directa, otro y canales sin implementación específica
    return GenericScraper(base_url=base_url)
