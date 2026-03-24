"""
Servicio de matching: empareja productos scrapeados con productos propios.
Estrategia en cascada con scoring de confianza.
"""
import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional, List

from services.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

# Umbrales de confianza
HIGH_CONFIDENCE = 0.95    # Match exacto (EAN)
MEDIUM_CONFIDENCE = 0.75  # Match por SKU
LOW_CONFIDENCE = 0.55     # Match fuzzy por nombre
AUTO_ACCEPT_THRESHOLD = 0.85  # Por encima de este umbral se acepta automáticamente


@dataclass
class MatchResult:
    """Resultado de un intento de matching."""
    matched: bool = False
    confidence: float = 0.0
    matched_by: str = ""  # "ean", "sku", "fuzzy_name"
    product_id: Optional[str] = None
    product_sku: Optional[str] = None
    product_ean: Optional[str] = None
    product_name: Optional[str] = None
    needs_review: bool = False  # True si la confianza es baja


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparación fuzzy."""
    if not text:
        return ""
    text = text.lower().strip()
    # Eliminar caracteres especiales excepto alfanuméricos y espacios
    text = re.sub(r"[^\w\s]", " ", text)
    # Colapsar espacios múltiples
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_ean(ean: str) -> str:
    """Normaliza un EAN: solo dígitos, padding a 13."""
    if not ean:
        return ""
    digits = re.sub(r"\D", "", ean.strip())
    # EAN-8 -> padding a 13
    if len(digits) == 8:
        digits = "00000" + digits
    return digits


def _normalize_sku(sku: str) -> str:
    """Normaliza un SKU para comparación."""
    if not sku:
        return ""
    return re.sub(r"[\s\-_.]", "", sku.strip().upper())


def fuzzy_name_score(name_a: str, name_b: str) -> float:
    """
    Calcula la similitud entre dos nombres de producto.
    Usa SequenceMatcher + bonificación por palabras clave compartidas.
    """
    a = _normalize_text(name_a)
    b = _normalize_text(name_b)

    if not a or not b:
        return 0.0

    # Score base: SequenceMatcher
    base_score = SequenceMatcher(None, a, b).ratio()

    # Bonificación por palabras clave compartidas
    words_a = set(a.split())
    words_b = set(b.split())

    # Filtrar palabras cortas/comunes
    stopwords = {"de", "la", "el", "en", "con", "para", "y", "o", "a", "un", "una", "los", "las"}
    words_a = {w for w in words_a if len(w) > 2 and w not in stopwords}
    words_b = {w for w in words_b if len(w) > 2 and w not in stopwords}

    if words_a and words_b:
        common = words_a & words_b
        keyword_score = len(common) / max(len(words_a), len(words_b))
        # Ponderar: 60% base + 40% keywords
        return (base_score * 0.6) + (keyword_score * 0.4)

    return base_score


async def match_product(
    scraped: ScrapedProduct,
    user_products: List[dict],
) -> MatchResult:
    """
    Intenta emparejar un producto scrapeado con la lista de productos del usuario.

    Estrategia en cascada:
    1. Match exacto por EAN (confianza 0.95+)
    2. Match por SKU normalizado (confianza 0.75+)
    3. Match fuzzy por nombre (confianza variable)

    Args:
        scraped: Producto scrapeado del competidor
        user_products: Lista de productos del usuario (dicts de MongoDB)

    Returns:
        MatchResult con la mejor coincidencia encontrada.
    """
    best_match = MatchResult()

    scraped_ean = _normalize_ean(scraped.ean or "")
    scraped_sku = _normalize_sku(scraped.sku or "")
    scraped_name = scraped.product_name or ""

    for product in user_products:
        # 1. Match por EAN
        if scraped_ean and len(scraped_ean) >= 8:
            product_ean = _normalize_ean(product.get("ean", ""))
            if product_ean and scraped_ean == product_ean:
                return MatchResult(
                    matched=True,
                    confidence=HIGH_CONFIDENCE,
                    matched_by="ean",
                    product_id=product.get("id"),
                    product_sku=product.get("sku"),
                    product_ean=product.get("ean"),
                    product_name=product.get("name"),
                    needs_review=False,
                )

        # 2. Match por SKU
        if scraped_sku:
            product_sku = _normalize_sku(product.get("sku", ""))
            if product_sku and scraped_sku == product_sku:
                return MatchResult(
                    matched=True,
                    confidence=MEDIUM_CONFIDENCE,
                    matched_by="sku",
                    product_id=product.get("id"),
                    product_sku=product.get("sku"),
                    product_ean=product.get("ean"),
                    product_name=product.get("name"),
                    needs_review=False,
                )

        # 3. Match fuzzy por nombre
        if scraped_name:
            product_name = product.get("name", "")
            score = fuzzy_name_score(scraped_name, product_name)
            if score > best_match.confidence and score >= LOW_CONFIDENCE:
                best_match = MatchResult(
                    matched=True,
                    confidence=round(score, 3),
                    matched_by="fuzzy_name",
                    product_id=product.get("id"),
                    product_sku=product.get("sku"),
                    product_ean=product.get("ean"),
                    product_name=product.get("name"),
                    needs_review=score < AUTO_ACCEPT_THRESHOLD,
                )

    return best_match
