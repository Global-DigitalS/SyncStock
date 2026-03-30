"""
Comparador de especificaciones técnicas IT entre dos productos.
Genera un score de similitud (0.0–1.0) basado en las especificaciones extraídas.

Pesos por componente:
  CPU:     modelo exacto=1.0, familia+gen=0.9, familia=0.7, brand=0.3
  GPU:     modelo exacto=1.0, familia+vram=0.9, familia=0.75, brand=0.3
  RAM:     cap+tipo+speed=1.0, cap+tipo=0.85, cap sola=0.6
  Storage: cap+tipo=1.0, cap sola=0.7
"""
import logging
import re
from typing import Optional, Tuple

from services.scrapers.spec_parser import ProductSpecs, spec_parser

logger = logging.getLogger(__name__)


def _clean_model(model: str) -> str:
    """Normaliza modelo eliminando variantes de marketing (fabricante/cooler).
    NO elimina sufijos técnicos como Ti, SUPER, XT, XTX que indican
    productos diferentes con especificaciones distintas."""
    if not model:
        return ""
    m = model.upper().strip()
    # Solo eliminar sufijos de fabricante/cooler que NO cambian el chip
    m = re.sub(r'\s*(OC|GAMING|STRIX|AORUS|EAGLE|VISION|WINDFORCE|TRIO)\b', '', m)
    return m.strip()


def compare_cpu(a: ProductSpecs, b: ProductSpecs) -> Tuple[float, str]:
    """
    Compara las especificaciones de CPU entre dos productos.

    Returns:
        (score, reason): score 0.0-1.0 y descripción de la coincidencia.
    """
    if not a.cpu_model and not a.cpu_family:
        return 0.0, "no_cpu_in_a"
    if not b.cpu_model and not b.cpu_family:
        return 0.0, "no_cpu_in_b"

    # Misma marca?
    if a.cpu_brand and b.cpu_brand and a.cpu_brand != b.cpu_brand:
        return 0.0, f"cpu_brand_mismatch ({a.cpu_brand} vs {b.cpu_brand})"

    # Modelo exacto
    if a.cpu_model and b.cpu_model:
        if a.cpu_model.upper() == b.cpu_model.upper():
            return 1.0, f"cpu_model_exact ({a.cpu_model})"

        # Modelos similares (ej: 5800X vs 5800X3D son DIFERENTES generaciones/SKUs)
        # Solo dar score alto si comparten prefijo principal
        base_a = re.sub(r'[A-Z]+$', '', a.cpu_model.upper())
        base_b = re.sub(r'[A-Z]+$', '', b.cpu_model.upper())
        if base_a == base_b and base_a:
            return 0.75, f"cpu_model_base_match ({base_a})"

    # Familia + generación
    if a.cpu_family and b.cpu_family:
        fam_match = a.cpu_family.upper() == b.cpu_family.upper()
        gen_match = (
            a.cpu_generation is not None and
            b.cpu_generation is not None and
            a.cpu_generation == b.cpu_generation
        )

        if fam_match and gen_match:
            return 0.85, f"cpu_family_gen ({a.cpu_family} gen{a.cpu_generation})"
        if fam_match:
            return 0.6, f"cpu_family ({a.cpu_family})"

    # Solo brand
    if a.cpu_brand and b.cpu_brand and a.cpu_brand == b.cpu_brand:
        return 0.3, f"cpu_brand ({a.cpu_brand})"

    return 0.0, "cpu_no_match"


def compare_gpu(a: ProductSpecs, b: ProductSpecs) -> Tuple[float, str]:
    """Compara especificaciones de GPU."""
    if not a.gpu_model and not a.gpu_family:
        return 0.0, "no_gpu_in_a"
    if not b.gpu_model and not b.gpu_family:
        return 0.0, "no_gpu_in_b"

    # Marca diferente = 0
    if a.gpu_brand and b.gpu_brand and a.gpu_brand != b.gpu_brand:
        return 0.0, f"gpu_brand_mismatch ({a.gpu_brand} vs {b.gpu_brand})"

    # Modelo exacto (limpiando sufijos de fábrica)
    if a.gpu_model and b.gpu_model:
        clean_a = _clean_model(a.gpu_model)
        clean_b = _clean_model(b.gpu_model)
        if clean_a == clean_b:
            # Mismo modelo: si tienen VRAM diferente, penalizar
            if a.gpu_vram_gb and b.gpu_vram_gb and a.gpu_vram_gb != b.gpu_vram_gb:
                return 0.7, f"gpu_model_vram_diff ({clean_a} {a.gpu_vram_gb}GB vs {b.gpu_vram_gb}GB)"
            return 1.0, f"gpu_model_exact ({clean_a})"

        # Familia + VRAM
        fam_a = f"{a.gpu_family}_{a.gpu_vram_gb}" if a.gpu_vram_gb else a.gpu_family
        fam_b = f"{b.gpu_family}_{b.gpu_vram_gb}" if b.gpu_vram_gb else b.gpu_family
        if fam_a and fam_b and fam_a == fam_b:
            return 0.8, f"gpu_family_vram ({fam_a})"

    # Familia sola
    if a.gpu_family and b.gpu_family and a.gpu_family.upper() == b.gpu_family.upper():
        return 0.6, f"gpu_family ({a.gpu_family})"

    # Solo brand
    if a.gpu_brand and b.gpu_brand and a.gpu_brand == b.gpu_brand:
        return 0.25, f"gpu_brand ({a.gpu_brand})"

    return 0.0, "gpu_no_match"


def compare_ram(a: ProductSpecs, b: ProductSpecs) -> Tuple[float, str]:
    """Compara especificaciones de RAM."""
    if not a.ram_gb and not a.ram_type:
        return 0.0, "no_ram_in_a"
    if not b.ram_gb and not b.ram_type:
        return 0.0, "no_ram_in_b"

    cap_match = a.ram_gb and b.ram_gb and a.ram_gb == b.ram_gb
    type_match = (
        a.ram_type and b.ram_type and
        a.ram_type.upper() == b.ram_type.upper()
    )
    speed_match = (
        a.ram_speed_mhz and b.ram_speed_mhz and
        a.ram_speed_mhz == b.ram_speed_mhz
    )

    if cap_match and type_match and speed_match:
        return 1.0, f"ram_full ({a.ram_gb}GB {a.ram_type} {a.ram_speed_mhz}MHz)"
    if cap_match and type_match:
        return 0.85, f"ram_cap_type ({a.ram_gb}GB {a.ram_type})"
    if cap_match:
        return 0.6, f"ram_cap ({a.ram_gb}GB)"
    if type_match:
        return 0.3, f"ram_type ({a.ram_type})"

    return 0.0, "ram_no_match"


def compare_storage(a: ProductSpecs, b: ProductSpecs) -> Tuple[float, str]:
    """Compara especificaciones de almacenamiento."""
    if not a.storage_gb and not a.storage_type:
        return 0.0, "no_storage_in_a"
    if not b.storage_gb and not b.storage_type:
        return 0.0, "no_storage_in_b"

    # Tolerancia: ±5% de capacidad (por ejemplo 960GB ≈ 1000GB)
    def cap_close(x: Optional[int], y: Optional[int]) -> bool:
        if not x or not y:
            return False
        diff = abs(x - y) / max(x, y)
        return diff <= 0.05

    cap_match = cap_close(a.storage_gb, b.storage_gb)
    type_match = (
        a.storage_type and b.storage_type and
        a.storage_type.upper() == b.storage_type.upper()
    )

    if cap_match and type_match:
        return 1.0, f"storage_full ({a.storage_gb}GB {a.storage_type})"
    if cap_match:
        return 0.7, f"storage_cap ({a.storage_gb}GB)"
    if type_match:
        return 0.3, f"storage_type ({a.storage_type})"

    return 0.0, "storage_no_match"


def spec_similarity_score(text_a: str, text_b: str) -> Tuple[float, str]:
    """
    Calcula el score de similitud entre dos nombres de producto
    basándose en sus especificaciones técnicas IT.

    Args:
        text_a: Nombre del producto A
        text_b: Nombre del producto B

    Returns:
        (score, reason): score 0.0-1.0 y descripción del match.
    """
    specs_a = spec_parser.parse(text_a)
    specs_b = spec_parser.parse(text_b)

    if not specs_a.has_specs() or not specs_b.has_specs():
        return 0.0, "no_specs_extracted"

    scores = []
    reasons = []

    # Comparar CPU si ambos tienen CPU
    if (specs_a.cpu_model or specs_a.cpu_family) and (specs_b.cpu_model or specs_b.cpu_family):
        cpu_score, cpu_reason = compare_cpu(specs_a, specs_b)
        scores.append(("cpu", cpu_score, 0.4))  # peso 40%
        reasons.append(f"cpu={cpu_score:.2f}({cpu_reason})")

    # Comparar GPU si ambos tienen GPU
    if (specs_a.gpu_model or specs_a.gpu_family) and (specs_b.gpu_model or specs_b.gpu_family):
        gpu_score, gpu_reason = compare_gpu(specs_a, specs_b)
        scores.append(("gpu", gpu_score, 0.4))
        reasons.append(f"gpu={gpu_score:.2f}({gpu_reason})")

    # Comparar RAM si ambos tienen RAM
    if (specs_a.ram_gb or specs_a.ram_type) and (specs_b.ram_gb or specs_b.ram_type):
        ram_score, ram_reason = compare_ram(specs_a, specs_b)
        scores.append(("ram", ram_score, 0.3))
        reasons.append(f"ram={ram_score:.2f}({ram_reason})")

    # Comparar Storage si ambos tienen Storage
    if (specs_a.storage_gb or specs_a.storage_type) and (specs_b.storage_gb or specs_b.storage_type):
        stor_score, stor_reason = compare_storage(specs_a, specs_b)
        scores.append(("storage", stor_score, 0.25))
        reasons.append(f"storage={stor_score:.2f}({stor_reason})")

    if not scores:
        return 0.0, "no_matching_categories"

    # Score ponderado normalizado
    total_weight = sum(w for _, _, w in scores)
    weighted_sum = sum(s * w for _, s, w in scores)
    final_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    reason = " | ".join(reasons)
    logger.debug(f"SpecMatch: {final_score:.3f} [{reason}]")
    return round(final_score, 3), reason
