"""
Analizador contextual de alertas de precios de competidores.

Enriquece las alertas genéricas ("precio bajó") con:
- Tendencia histórica (7/14/30 días)
- Volatilidad del precio
- Posición competitiva actual
- Impacto en margen
- Recomendación automática (repricing, esperar, ignorar)
"""
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    CRITICAL = "CRITICAL"  # Acción inmediata requerida
    WARNING = "WARNING"    # Atención recomendada
    INFO = "INFO"          # Informativo, sin urgencia


class TrendDirection(str, Enum):
    UPTREND = "UPTREND"     # Precios subiendo
    DOWNTREND = "DOWNTREND" # Precios bajando
    STABLE = "STABLE"       # Precios estables
    VOLATILE = "VOLATILE"   # Alta variación


class AlertAction(str, Enum):
    AUTO_REPRICE = "AUTO_REPRICE"    # Ajustar precio automáticamente
    WAIT = "WAIT"                    # Esperar antes de actuar
    IGNORE = "IGNORE"                # Sin acción, margen protegido
    MANUAL_REVIEW = "MANUAL_REVIEW"  # Revisión manual necesaria


@dataclass
class PriceContext:
    """Contexto completo para una alerta de precio."""
    # Cambio de precio
    old_price: float = 0.0
    new_price: float = 0.0
    delta_eur: float = 0.0
    delta_percent: float = 0.0

    # Tendencia
    trend: TrendDirection = TrendDirection.STABLE
    trend_days: int = 7           # Número de días analizados
    snapshots_analyzed: int = 0

    # Volatilidad
    volatility_percent: float = 0.0

    # Posición competitiva
    competitor_id: str = ""
    competitor_name: str = ""
    your_price: Optional[float] = None
    best_competitor_price: Optional[float] = None
    your_position: str = "unknown"  # "1st", "2nd", "3rd+", "most_expensive", "unknown"
    price_gap_eur: float = 0.0
    total_competitors_analyzed: int = 0

    # Impacto en margen
    your_cost: Optional[float] = None
    margin_current_percent: Optional[float] = None
    margin_if_copy_percent: Optional[float] = None
    margin_delta_pp: Optional[float] = None  # Puntos porcentuales de diferencia

    # Recomendación
    action: AlertAction = AlertAction.MANUAL_REVIEW
    suggested_price: Optional[float] = None
    action_reason: str = ""

    # Nivel de alerta
    alert_level: AlertLevel = AlertLevel.INFO


@dataclass
class EnrichedAlert:
    """Alerta enriquecida con contexto completo."""
    # IDs
    alert_id: str = ""
    user_id: str = ""
    sku: Optional[str] = None
    ean: Optional[str] = None

    # Contexto
    context: PriceContext = field(default_factory=PriceContext)

    # Mensaje formateado
    title: str = ""
    message_short: str = ""    # Para notificaciones push
    message_long: str = ""     # Para email/dashboard

    # Acciones disponibles
    available_actions: List[str] = field(default_factory=list)

    # Timestamp
    created_at: str = ""


async def analyze_price_alert(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    competitor_id: str,
    competitor_name: str,
    new_price: float,
    db,
) -> EnrichedAlert:
    """
    Analiza el contexto completo de un cambio de precio de competidor.

    Args:
        user_id: ID del usuario
        sku: SKU del producto
        ean: EAN del producto
        competitor_id: ID del competidor
        competitor_name: Nombre del competidor
        new_price: Nuevo precio detectado
        db: Instancia de base de datos Motor

    Returns:
        EnrichedAlert con contexto completo y recomendación.
    """
    now = datetime.now(timezone.utc)
    context = PriceContext(
        new_price=new_price,
        competitor_id=competitor_id,
        competitor_name=competitor_name,
    )

    # 1. Obtener histórico de precios
    snapshots = await _get_price_history(user_id, sku, ean, competitor_id, days=30, db=db)
    context.snapshots_analyzed = len(snapshots)

    # 2. Calcular cambio de precio respecto al anterior
    if snapshots:
        context.old_price = snapshots[0]["price"]  # El más reciente antes de ahora
        context.delta_eur = round(new_price - context.old_price, 2)
        if context.old_price > 0:
            context.delta_percent = round((context.delta_eur / context.old_price) * 100, 2)

    # 3. Analizar tendencia
    if len(snapshots) >= 3:
        context.trend, context.trend_days = _calculate_trend(snapshots, days=7)
        context.volatility_percent = _calculate_volatility(snapshots)

    # 4. Obtener nuestro precio
    my_product = await _get_my_product(user_id, sku, ean, db)
    if my_product:
        context.your_price = my_product.get("price")
        context.your_cost = my_product.get("cost")

    # 5. Calcular posición competitiva
    await _calculate_competitive_position(user_id, sku, ean, context, db)

    # 6. Calcular impacto en margen
    _calculate_margin_impact(context)

    # 7. Generar recomendación
    _generate_recommendation(context)

    # 8. Determinar nivel de alerta
    context.alert_level = _determine_alert_level(context)

    # 9. Formatear mensajes
    alert = _format_alert(user_id, sku, ean, context, now)

    return alert


async def _get_price_history(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    competitor_id: str,
    days: int,
    db,
) -> List[dict]:
    """Obtiene el histórico de snapshots ordenado del más reciente al más antiguo."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    query = {
        "user_id": user_id,
        "competitor_id": competitor_id,
        "scraped_at": {"$gte": cutoff},
    }
    or_cond = []
    if sku:
        or_cond.append({"sku": sku})
    if ean:
        or_cond.append({"ean": ean})
    if or_cond:
        query["$or"] = or_cond

    try:
        snapshots = await db.price_snapshots.find(
            query,
            {"_id": 0, "price": 1, "scraped_at": 1},
            sort=[("scraped_at", -1)],
        ).to_list(100)
        return snapshots
    except Exception as e:
        logger.debug(f"Error obteniendo histórico: {e}")
        return []


async def _get_my_product(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    db,
) -> Optional[dict]:
    """Obtiene los datos de nuestro producto."""
    query = {"user_id": user_id}
    if sku:
        query["sku"] = sku
    elif ean:
        query["ean"] = ean
    else:
        return None
    try:
        return await db.products.find_one(query, {"_id": 0, "price": 1, "cost": 1, "name": 1})
    except Exception:
        return None


async def _calculate_competitive_position(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    context: PriceContext,
    db,
) -> None:
    """Calcula la posición competitiva (1º, 2º, etc.) entre todos los competidores."""
    try:
        # Obtener último snapshot de CADA competidor
        match_stage = {"user_id": user_id}
        or_cond = []
        if sku:
            or_cond.append({"sku": sku})
        if ean:
            or_cond.append({"ean": ean})
        if or_cond:
            match_stage["$or"] = or_cond

        # Precio más reciente por competidor
        pipeline = [
            {"$match": match_stage},
            {"$sort": {"scraped_at": -1}},
            {"$group": {
                "_id": "$competitor_id",
                "price": {"$first": "$price"},
            }},
        ]
        competitor_prices = await db.price_snapshots.aggregate(pipeline).to_list(50)

        if not competitor_prices:
            return

        all_prices = [c["price"] for c in competitor_prices if c["price"] > 0]
        context.total_competitors_analyzed = len(all_prices)

        if all_prices:
            context.best_competitor_price = min(all_prices)

        # Posición de nuestro precio
        if context.your_price and all_prices:
            all_with_ours = sorted(all_prices + [context.your_price])
            our_pos = all_with_ours.index(context.your_price) + 1
            total = len(all_with_ours)

            if our_pos == 1:
                context.your_position = "1st"
            elif our_pos == 2:
                context.your_position = "2nd"
            elif our_pos == total:
                context.your_position = "most_expensive"
            else:
                context.your_position = f"{our_pos}th"

            # Gap con el más barato de los competidores (excluido nosotros)
            if context.best_competitor_price and context.your_price:
                context.price_gap_eur = round(context.your_price - context.best_competitor_price, 2)

    except Exception as e:
        logger.debug(f"Error calculando posición competitiva: {e}")


def _calculate_trend(snapshots: List[dict], days: int = 7) -> tuple:
    """
    Calcula la tendencia de precios usando regresión lineal simple.
    Returns: (TrendDirection, days_analyzed)
    """
    if len(snapshots) < 3:
        return TrendDirection.STABLE, 0

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    recent = [s for s in snapshots if s.get("scraped_at", "") >= cutoff.isoformat()]

    if len(recent) < 3:
        recent = snapshots[:min(10, len(snapshots))]

    prices = [s["price"] for s in recent if s.get("price", 0) > 0]
    if len(prices) < 2:
        return TrendDirection.STABLE, 0

    n = len(prices)
    # Regresión lineal simple: pendiente de precios sobre tiempo (índice)
    x_mean = (n - 1) / 2
    y_mean = sum(prices) / n
    numerator = sum((i - x_mean) * (prices[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator else 0

    # Slope relativo al precio promedio (para normalizar)
    relative_slope = (slope / y_mean) * 100 if y_mean > 0 else 0

    if abs(relative_slope) < 0.5:
        return TrendDirection.STABLE, days
    elif relative_slope > 0.5:
        return TrendDirection.UPTREND, days
    else:
        return TrendDirection.DOWNTREND, days


def _calculate_volatility(snapshots: List[dict]) -> float:
    """Calcula volatilidad como coeficiente de variación de los precios."""
    prices = [s["price"] for s in snapshots if s.get("price", 0) > 0]
    if len(prices) < 2:
        return 0.0

    mean = sum(prices) / len(prices)
    if mean == 0:
        return 0.0

    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)
    return round((std_dev / mean) * 100, 2)


def _calculate_margin_impact(context: PriceContext) -> None:
    """Calcula el impacto en margen si copiamos el precio del competidor."""
    if not context.your_price or context.your_price <= 0:
        return

    # Margen actual (si tenemos coste)
    if context.your_cost and context.your_cost > 0:
        context.margin_current_percent = round(
            ((context.your_price - context.your_cost) / context.your_price) * 100, 1
        )
        # Margen si copiamos el precio del competidor
        if context.best_competitor_price and context.best_competitor_price > context.your_cost:
            context.margin_if_copy_percent = round(
                ((context.best_competitor_price - context.your_cost) / context.best_competitor_price) * 100, 1
            )
            if context.margin_current_percent is not None:
                context.margin_delta_pp = round(
                    context.margin_if_copy_percent - context.margin_current_percent, 1
                )


def _generate_recommendation(context: PriceContext) -> None:
    """
    Genera la recomendación de acción basada en el contexto.

    Lógica:
    - Si estamos más caros Y tendencia bajista → esperar
    - Si estamos más caros Y competidor más barato significativamente → bajar precio
    - Si somos los más baratos → mantener (proteger margen)
    - Si margen muy bajo al copiar → no actuar automáticamente
    """
    # Sin datos de nuestro precio: revisión manual
    if not context.your_price:
        context.action = AlertAction.MANUAL_REVIEW
        context.action_reason = "Sin precio propio para comparar"
        return

    # Somos los más baratos: proteger margen
    if context.your_position == "1st":
        context.action = AlertAction.IGNORE
        context.action_reason = "Ya somos el más barato, proteger margen"
        return

    gap = context.price_gap_eur or 0

    # Competidor bajó precio y estamos por encima
    if context.delta_percent < -2 and gap > 0:
        # Verificar tendencia bajista → esperar
        if context.trend == TrendDirection.DOWNTREND:
            context.action = AlertAction.WAIT
            context.action_reason = (
                f"Tendencia bajista ({context.trend_days}d). "
                "Esperar para no bajar demasiado el precio."
            )
            return

        # Verificar que el margen al copiar siga siendo sano (>15%)
        if context.margin_if_copy_percent is not None and context.margin_if_copy_percent < 15:
            context.action = AlertAction.MANUAL_REVIEW
            context.action_reason = (
                f"Margen al copiar precio ({context.margin_if_copy_percent:.1f}%) demasiado bajo."
            )
            return

        # Recomendar bajar precio al -0.5% del competidor más barato
        if context.best_competitor_price:
            context.suggested_price = round(context.best_competitor_price * 0.995, 2)
            context.action = AlertAction.AUTO_REPRICE
            margin_note = (
                f" Margen → {context.margin_if_copy_percent:.1f}%"
                if context.margin_if_copy_percent else ""
            )
            context.action_reason = (
                f"Competidor {context.competitor_name} bajó {abs(context.delta_percent):.1f}%. "
                f"Bajar a €{context.suggested_price} (-0.5% del líder).{margin_note}"
            )
        return

    # Precio subió: posiblemente buena noticia
    if context.delta_percent > 2 and gap < 0:
        context.action = AlertAction.IGNORE
        context.action_reason = (
            f"Competidor subió precio {context.delta_percent:.1f}%. "
            "Nuestra posición mejora."
        )
        return

    # Default: revisión manual
    context.action = AlertAction.MANUAL_REVIEW
    context.action_reason = "Cambio menor, sin acción automática"


def _determine_alert_level(context: PriceContext) -> AlertLevel:
    """Determina el nivel de urgencia de la alerta."""
    if context.action == AlertAction.AUTO_REPRICE:
        if abs(context.delta_percent) >= 5 or (context.your_position == "most_expensive"):
            return AlertLevel.CRITICAL
        return AlertLevel.WARNING

    if abs(context.delta_percent) >= 10:
        return AlertLevel.CRITICAL
    if abs(context.delta_percent) >= 3 or context.action == AlertAction.WAIT:
        return AlertLevel.WARNING

    return AlertLevel.INFO


def _format_alert(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    context: PriceContext,
    now: datetime,
) -> EnrichedAlert:
    """Genera los mensajes de alerta formateados."""
    import uuid

    product_ref = sku or ean or "N/A"
    direction = "↓" if context.delta_eur < 0 else "↑"
    change_str = f"€{context.old_price:.2f} → €{context.new_price:.2f} ({direction}{abs(context.delta_percent):.1f}%)"

    # Mensaje corto (notificación push)
    level_icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}.get(context.alert_level.value, "⚪")
    short = (
        f"{level_icon} {context.competitor_name}: {change_str}"
    )

    # Mensaje largo (email/dashboard)
    position_str = {
        "1st": "🥇 Más barato",
        "2nd": "🥈 2º más barato",
        "most_expensive": "⚠️ El más caro",
    }.get(context.your_position, f"Posición {context.your_position}")

    trend_icon = {
        TrendDirection.DOWNTREND: "📉 Bajista",
        TrendDirection.UPTREND: "📈 Alcista",
        TrendDirection.STABLE: "➡️ Estable",
        TrendDirection.VOLATILE: "↕️ Volátil",
    }.get(context.trend, "N/A")

    action_icon = {
        AlertAction.AUTO_REPRICE: "⚙️ Repricing automático",
        AlertAction.WAIT: "⏳ Esperar",
        AlertAction.IGNORE: "✓ Mantener precio",
        AlertAction.MANUAL_REVIEW: "🔍 Revisión manual",
    }.get(context.action, "N/A")

    long_lines = [
        f"Competidor: {context.competitor_name}",
        f"Cambio: {change_str}",
    ]
    if context.trend != TrendDirection.STABLE:
        long_lines.append(f"Tendencia: {trend_icon} ({context.trend_days}d)")
    if context.your_position != "unknown":
        long_lines.append(f"Tu posición: {position_str}")
    if context.your_price:
        long_lines.append(f"Tu precio: €{context.your_price:.2f}")
    if context.best_competitor_price and context.price_gap_eur != 0:
        gap_sign = "+" if context.price_gap_eur > 0 else ""
        long_lines.append(
            f"Mejor competidor: €{context.best_competitor_price:.2f} "
            f"(diferencia: {gap_sign}€{context.price_gap_eur:.2f})"
        )
    if context.margin_current_percent is not None:
        long_lines.append(f"Margen actual: {context.margin_current_percent:.1f}%")
        if context.margin_delta_pp is not None:
            sign = "+" if context.margin_delta_pp >= 0 else ""
            long_lines.append(
                f"Margen si copias: {context.margin_if_copy_percent:.1f}% "
                f"({sign}{context.margin_delta_pp:.1f}pp)"
            )
    long_lines.append(f"Recomendación: {action_icon}")
    if context.action_reason:
        long_lines.append(f"  → {context.action_reason}")
    if context.suggested_price:
        long_lines.append(f"  → Precio sugerido: €{context.suggested_price:.2f}")

    title = f"Cambio de precio detectado — {product_ref}"

    available_actions = ["manual_review"]
    if context.action == AlertAction.AUTO_REPRICE and context.suggested_price:
        available_actions = ["auto_reprice", "wait", "ignore"]
    elif context.action == AlertAction.WAIT:
        available_actions = ["wait", "auto_reprice", "ignore"]

    return EnrichedAlert(
        alert_id=str(uuid.uuid4()),
        user_id=user_id,
        sku=sku,
        ean=ean,
        context=context,
        title=title,
        message_short=short,
        message_long="\n".join(long_lines),
        available_actions=available_actions,
        created_at=now.isoformat(),
    )
