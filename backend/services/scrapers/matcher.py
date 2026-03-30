"""
Servicio de matching: empareja productos scrapeados con productos propios.

Estrategia en 3 capas con scoring de confianza:
  Capa 1 (40% peso): Match exacto por EAN → confianza 0.97
  Capa 2 (30% peso): Match por especificaciones IT (CPU/GPU/RAM/SSD)
  Capa 3 (30% peso): Fuzzy matching por nombre (Levenshtein/Jaro-Winkler)

Score final = 0.4*ean + 0.3*specs + 0.3*fuzzy
Umbral de aceptación automática: 0.85
"""
import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional, List, Tuple

from services.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

# Umbrales de confianza
HIGH_CONFIDENCE = 0.97    # Match exacto EAN
MEDIUM_CONFIDENCE = 0.75  # Match por SKU o specs
LOW_CONFIDENCE = 0.55     # Match fuzzy por nombre
AUTO_ACCEPT_THRESHOLD = 0.85  # Por encima se acepta automáticamente

# Pesos de cada capa para el score combinado
WEIGHT_EAN = 0.40
WEIGHT_SPECS = 0.30
WEIGHT_FUZZY = 0.30


@dataclass
class MatchResult:
    """Resultado de un intento de matching."""
    matched: bool = False
    confidence: float = 0.0
    matched_by: str = ""           # "ean", "sku", "specs", "fuzzy_name", "specs+fuzzy"
    product_id: Optional[str] = None
    product_sku: Optional[str] = None
    product_ean: Optional[str] = None
    product_name: Optional[str] = None
    needs_review: bool = False     # True si la confianza es baja
    match_details: str = ""        # Descripción de las capas usadas


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparación fuzzy."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_ean(ean: str) -> str:
    """Normaliza un EAN: solo dígitos, padding a 13."""
    if not ean:
        return ""
    digits = re.sub(r"\D", "", ean.strip())
    if len(digits) == 8:
        digits = "00000" + digits
    return digits


def _normalize_sku(sku: str) -> str:
    """Normaliza un SKU para comparación."""
    if not sku:
        return ""
    return re.sub(r"[\s\-_.]", "", sku.strip().upper())


# Palabras que deben coincidir para ser consideradas candidatas relevantes
_KEY_STOPWORDS = {
    "de", "la", "el", "en", "con", "para", "y", "o", "a", "un", "una",
    "los", "las", "the", "and", "or", "for", "with", "in", "on", "of"
}


def fuzzy_name_score(name_a: str, name_b: str) -> float:
    """
    Calcula la similitud entre dos nombres de producto.
    SequenceMatcher (60%) + palabras clave compartidas (40%).
    """
    a = _normalize_text(name_a)
    b = _normalize_text(name_b)

    if not a or not b:
        return 0.0

    base_score = SequenceMatcher(None, a, b).ratio()

    words_a = {w for w in a.split() if len(w) > 2 and w not in _KEY_STOPWORDS}
    words_b = {w for w in b.split() if len(w) > 2 and w not in _KEY_STOPWORDS}

    if words_a and words_b:
        common = words_a & words_b
        keyword_score = len(common) / max(len(words_a), len(words_b))
        return (base_score * 0.6) + (keyword_score * 0.4)

    return base_score


def _spec_layer_score(scraped_name: str, product_name: str) -> Tuple[float, str]:
    """
    Capa 2: Similitud por especificaciones técnicas IT.
    Importa spec_matcher aquí (evita circular al inicio del módulo).
    """
    try:
        from services.scrapers.spec_matcher import spec_similarity_score
        return spec_similarity_score(scraped_name, product_name)
    except Exception as e:
        logger.debug(f"spec_layer_score error: {e}")
        return 0.0, "spec_error"


async def match_product(
    scraped: ScrapedProduct,
    user_products: List[dict],
) -> MatchResult:
    """
    Intenta emparejar un producto scrapeado con la lista de productos del usuario.

    Estrategia en cascada:
    1. EAN exacto → devuelve inmediatamente con confianza 0.97
    2. SKU exacto → devuelve inmediatamente con confianza 0.75
    3. Score combinado (specs + fuzzy) para el resto

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
        # ── CAPA 1: EAN exacto ────────────────────────────────────────────────
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
                    match_details=f"EAN exacto: {scraped_ean}",
                )

        # ── CAPA 1b: SKU exacto ───────────────────────────────────────────────
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
                    match_details=f"SKU exacto: {scraped_sku}",
                )

        # ── CAPA 2+3: Score combinado Specs + Fuzzy ───────────────────────────
        if scraped_name:
            product_name = product.get("name", "")

            # Capa 2: Specs IT
            spec_score, spec_reason = _spec_layer_score(scraped_name, product_name)

            # Capa 3: Fuzzy name
            fuzzy_score = fuzzy_name_score(scraped_name, product_name)

            # Score combinado
            if spec_score > 0:
                # Tenemos specs: combinar
                combined = (spec_score * WEIGHT_SPECS + fuzzy_score * WEIGHT_FUZZY) / (WEIGHT_SPECS + WEIGHT_FUZZY)
                matched_by = "specs+fuzzy"
                details = f"specs={spec_score:.2f}({spec_reason}) fuzzy={fuzzy_score:.2f}"
            else:
                # Sin specs: solo fuzzy
                combined = fuzzy_score
                matched_by = "fuzzy_name"
                details = f"fuzzy={fuzzy_score:.2f}"

            if combined > best_match.confidence and combined >= LOW_CONFIDENCE:
                best_match = MatchResult(
                    matched=True,
                    confidence=round(combined, 3),
                    matched_by=matched_by,
                    product_id=product.get("id"),
                    product_sku=product.get("sku"),
                    product_ean=product.get("ean"),
                    product_name=product.get("name"),
                    needs_review=combined < AUTO_ACCEPT_THRESHOLD,
                    match_details=details,
                )

    return best_match
