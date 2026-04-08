"""
Servicio de sincronización multi-tienda con algoritmo jerárquico EAN > SKU > Borrador.

Algoritmo de decisión por producto:
1. Tienda sin productos  → CREATE_FULL   (publicado, con toda la información)
2. Encontrado por EAN    → UPDATE_BY_EAN (solo precio + stock, nada más cambia)
3. Encontrado por SKU    → UPDATE_BY_SKU (solo precio + stock, nada más cambia)
4. No encontrado         → CREATE_DRAFT  (borrador, requiere revisión manual)

Plataformas soportadas: WooCommerce, PrestaShop, Shopify
"""
import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from services.database import db

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN DE RATE LIMITING (segundos mínimos entre requests)
# ============================================================
_PLATFORM_RATE_LIMIT = {
    "woocommerce": 0.1,   # 10 req/s  (límite documentado de WC)
    "shopify": 0.5,       # 2 req/s   (límite de Shopify)
    "prestashop": 0.2,    # 5 req/s   (conservador, sin límite documentado)
    "magento": 0.2,
    "wix": 0.2,
}

MAX_RETRIES = 3
_RETRY_DELAYS = [1.0, 2.0, 4.0]  # backoff exponencial en segundos

# Palabras clave que indican error no reintentable
_NON_RETRYABLE_KEYWORDS = [
    "401", "403", "authentication", "credentials",
    "invalid api", "unauthorized", "forbidden",
]


# ============================================================
# ENUMERADOS Y TIPOS
# ============================================================

class SyncAction(str, Enum):
    CREATE_FULL = "CREATE_FULL"
    UPDATE_BY_EAN = "UPDATE_BY_EAN"
    UPDATE_BY_SKU = "UPDATE_BY_SKU"
    CREATE_DRAFT = "CREATE_DRAFT"
    SKIPPED = "SKIPPED"


# ============================================================
# RATE LIMITER
# ============================================================

class _RateLimiter:
    """Rate limiter simple por plataforma (in-process)."""

    def __init__(self):
        self._last: dict[str, float] = {}

    async def wait(self, platform: str):
        delay = _PLATFORM_RATE_LIMIT.get(platform, 0.2)
        last = self._last.get(platform, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last[platform] = time.monotonic()


_rate_limiter = _RateLimiter()


# ============================================================
# HELPERS DE REINTENTO
# ============================================================

def _is_retryable(error_msg: str) -> bool:
    lower = error_msg.lower()
    return not any(kw in lower for kw in _NON_RETRYABLE_KEYWORDS)


async def _call(func, *args, platform: str = "", **kwargs):
    """
    Ejecuta una función síncrona con:
    - Espera de rate limiting antes de la llamada
    - Reintentos con backoff exponencial ante errores transitorios
    """
    last_exc: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            await _rate_limiter.wait(platform)
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as exc:
            last_exc = exc
            msg = str(exc)
            if not _is_retryable(msg) or attempt >= MAX_RETRIES:
                raise
            delay = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)]
            logger.warning(
                f"[{platform}] Reintento {attempt + 1}/{MAX_RETRIES} en {delay}s: {msg[:100]}"
            )
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ============================================================
# WOOCOMMERCE — helpers síncronos (se ejecutan en thread pool)
# ============================================================

def _wc_count_products(wcapi) -> int:
    """Cuenta productos en WooCommerce (usa cabecera X-WP-Total)."""
    try:
        r = wcapi.get("products", params={"per_page": 1, "page": 1, "status": "any"})
        if r.status_code == 200:
            return int(r.headers.get("X-WP-Total", "0"))
        return 0
    except Exception:
        return 0


def _wc_build_index(wcapi) -> tuple[dict, dict]:
    """
    Obtiene todos los productos de WooCommerce y construye índices EAN y SKU.
    Retorna (by_ean: {ean → wc_id}, by_sku: {sku → wc_id}).
    """
    by_ean: dict[str, int] = {}
    by_sku: dict[str, int] = {}
    page = 1
    while True:
        try:
            r = wcapi.get("products", params={"per_page": 100, "page": page, "status": "any"})
            if r.status_code != 200:
                break
            batch = r.json()
            if not batch:
                break
            for p in batch:
                pid = p["id"]
                for meta in p.get("meta_data", []):
                    if meta.get("key") in ["_global_unique_id", "_gtin", "_ean", "gtin"]:
                        val = (meta.get("value") or "").strip()
                        if val:
                            by_ean[val] = pid
                            break
                sku = (p.get("sku") or "").strip()
                if sku:
                    by_sku[sku] = pid
            page += 1
            if len(batch) < 100:
                break
        except Exception as e:
            logger.error(f"WooCommerce _wc_build_index error página {page}: {e}")
            break
    return by_ean, by_sku


def _wc_update_price_stock(wcapi, wc_id: int, price: float, stock: int) -> dict:
    """Actualiza solo precio y stock en WooCommerce."""
    payload = {
        "regular_price": str(round(price, 2)),
        "manage_stock": True,
        "stock_quantity": stock,
    }
    r = wcapi.put(f"products/{wc_id}", payload)
    if r.status_code in [200, 201]:
        return {"status": "success"}
    return {"status": "error", "message": r.text[:200]}


def _wc_create_product(wcapi, product: dict, price: float, stock: int, status: str) -> dict:
    """Crea un producto en WooCommerce (status: 'publish' o 'draft')."""
    payload = {
        "name": product.get("name", ""),
        "type": "simple",
        "status": status,
        "regular_price": str(round(price, 2)),
        "manage_stock": True,
        "stock_quantity": stock,
        "sku": product.get("sku", ""),
        "description": product.get("long_description") or product.get("description", ""),
        "short_description": product.get("short_description", ""),
    }
    ean = (product.get("ean") or "").strip()
    if ean:
        payload["meta_data"] = [{"key": "_global_unique_id", "value": ean}]
    images = []
    if product.get("image_url"):
        images.append({"src": product["image_url"]})
    for url in (product.get("gallery_images") or []):
        if url:
            images.append({"src": url})
    if images:
        payload["images"] = images

    r = wcapi.post("products", payload)
    if r.status_code in [200, 201]:
        created = r.json()
        return {"status": "success", "product_id": created.get("id")}
    return {"status": "error", "message": r.text[:300]}


# ============================================================
# FUNCIÓN PRINCIPAL: sync_store
# ============================================================

async def sync_store(store_config: dict) -> dict:
    """
    Sincroniza los productos de un catálogo con una tienda online.

    Implementa el algoritmo jerárquico EAN > SKU > Borrador:
    - Si la tienda está vacía: sube todos los productos publicados.
    - Si el producto existe por EAN: actualiza solo precio y stock.
    - Si no hay EAN pero existe por SKU: actualiza solo precio y stock.
    - Si no se encuentra por ningún identificador: crea borrador.

    Args:
        store_config: Documento de la colección ``woocommerce_configs``.

    Returns:
        dict con el resumen completo de la sincronización.
    """
    store_id = store_config.get("id", "?")
    store_name = store_config.get("name", store_id)
    platform = store_config.get("platform", "woocommerce")
    catalog_id = store_config.get("catalog_id")

    sync_id = f"sync_{uuid.uuid4().hex[:8]}"
    start_time = datetime.now(UTC)

    logger.info(
        f"[{sync_id}] Iniciando sync | tienda='{store_name}' plataforma={platform} catálogo={catalog_id}"
    )

    results: dict = {
        "sync_id": sync_id,
        "store_id": store_id,
        "store_name": store_name,
        "platform": platform,
        "start_time": start_time.isoformat(),
        "status": "success",
        "summary": {
            "total": 0,
            "create_full": 0,
            "update_by_ean": 0,
            "update_by_sku": 0,
            "create_draft": 0,
            "skipped": 0,
            "failed": 0,
        },
        "draft_products": [],
        "errors": [],
    }

    if not catalog_id:
        results["status"] = "skipped"
        results["message"] = f"Tienda '{store_name}' no tiene catálogo asociado"
        logger.warning(f"[{sync_id}] {results['message']}")
        return results

    try:
        catalog_items = await db.catalog_items.find(
            {"catalog_id": catalog_id, "active": True}
        ).to_list(10000)

        if not catalog_items:
            results["status"] = "skipped"
            results["message"] = "No hay productos activos en el catálogo"
            return results

        margin_rules = await db.catalog_margin_rules.find(
            {"catalog_id": catalog_id}
        ).sort("priority", -1).to_list(100)

        results["summary"]["total"] = len(catalog_items)

        if platform == "woocommerce":
            await _sync_woocommerce(
                store_config, catalog_items, margin_rules, results, sync_id
            )
        elif platform == "prestashop":
            await _sync_prestashop(
                store_config, catalog_items, margin_rules, results, sync_id
            )
        elif platform == "shopify":
            await _sync_shopify(
                store_config, catalog_items, margin_rules, results, sync_id
            )
        else:
            results["status"] = "error"
            results["message"] = f"Plataforma '{platform}' no soportada en el sync multi-tienda"
            return results

        # Persiste timestamp de última sync
        end_time = datetime.now(UTC)
        duration_s = (end_time - start_time).total_seconds()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = round(duration_s, 1)

        s = results["summary"]
        if results["status"] != "error":
            results["status"] = "success" if s["failed"] == 0 else "partial"

        synced_count = s["update_by_ean"] + s["update_by_sku"] + s["create_full"]
        await db.woocommerce_configs.update_one(
            {"id": store_id},
            {"$set": {
                "last_sync": end_time.isoformat(),
                "products_synced": synced_count,
            }}
        )

        logger.info(
            f"[{sync_id}] Sync completado | {platform} '{store_name}' | "
            f"EAN={s['update_by_ean']} SKU={s['update_by_sku']} "
            f"nuevos={s['create_full']} borradores={s['create_draft']} "
            f"saltados={s['skipped']} fallidos={s['failed']} | "
            f"{duration_s:.1f}s"
        )

        # Notificación de borradores creados
        if results["draft_products"]:
            logger.info(
                f"[{sync_id}] {len(results['draft_products'])} productos creados como borrador "
                f"(requieren revisión manual)"
            )

    except Exception as exc:
        results["status"] = "error"
        results["message"] = str(exc)
        results["errors"].append(str(exc))
        logger.error(f"[{sync_id}] Error crítico en sync de '{store_name}': {exc}")

    return results


# ============================================================
# WOOCOMMERCE
# ============================================================

async def _sync_woocommerce(
    store_config: dict,
    catalog_items: list,
    margin_rules: list,
    results: dict,
    sync_id: str,
):
    from services.sync import calculate_final_price, get_woocommerce_client

    wcapi = get_woocommerce_client(store_config)
    platform = "woocommerce"

    # ¿Tiene la tienda productos?
    total_in_store = await _call(_wc_count_products, wcapi, platform=platform)
    store_is_empty = total_in_store == 0

    by_ean: dict[str, int] = {}
    by_sku: dict[str, int] = {}
    if not store_is_empty:
        by_ean, by_sku = await _call(_wc_build_index, wcapi, platform=platform)
        logger.info(
            f"[{sync_id}] WC índice construido: {len(by_ean)} EAN, {len(by_sku)} SKU"
        )

    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]})
        if not product:
            results["summary"]["skipped"] += 1
            continue

        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        stock = product.get("stock", 0)
        ean = (product.get("ean") or "").strip()
        sku = (product.get("sku") or "").strip()
        log_tag = f"[{sync_id}] WC | {sku or ean or product['id']}"

        try:
            if store_is_empty:
                # CASO 1: Subir completo publicado
                r = await _call(_wc_create_product, wcapi, product, final_price, stock, "publish", platform=platform)
                _handle_result(r, SyncAction.CREATE_FULL, results, log_tag, sku, ean, product)
                continue

            # CASO 2: Buscar por EAN
            wc_id = by_ean.get(ean) if ean else None
            if wc_id:
                r = await _call(_wc_update_price_stock, wcapi, wc_id, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_EAN, results, log_tag, sku, ean, product)
                continue

            # CASO 3: Buscar por SKU
            wc_id = by_sku.get(sku) if sku else None
            if wc_id:
                r = await _call(_wc_update_price_stock, wcapi, wc_id, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_SKU, results, log_tag, sku, ean, product)
                continue

            # CASO 4: Crear borrador
            r = await _call(_wc_create_product, wcapi, product, final_price, stock, "draft", platform=platform)
            _handle_result(r, SyncAction.CREATE_DRAFT, results, log_tag, sku, ean, product)

        except Exception as exc:
            results["summary"]["failed"] += 1
            results["errors"].append(f"{sku or ean}: {str(exc)[:100]}")
            logger.error(f"{log_tag} → ERROR: {exc}")


# ============================================================
# PRESTASHOP
# ============================================================

async def _sync_prestashop(
    store_config: dict,
    catalog_items: list,
    margin_rules: list,
    results: dict,
    sync_id: str,
):
    from services.platforms.prestashop import PrestaShopClient
    from services.sync import calculate_final_price

    client = PrestaShopClient(
        store_url=store_config.get("store_url", ""),
        api_key=store_config.get("api_key", ""),
    )
    platform = "prestashop"

    store_is_empty = not await _call(client.has_products, platform=platform)

    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]})
        if not product:
            results["summary"]["skipped"] += 1
            continue

        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        stock = product.get("stock", 0)
        ean = (product.get("ean") or "").strip()
        sku = (product.get("sku") or "").strip()
        log_tag = f"[{sync_id}] PS | {sku or ean or product['id']}"

        try:
            if store_is_empty:
                # CASO 1: Subir completo publicado
                product_data = _build_product_data(product, final_price, stock)
                r = await _call(client.create_product, product_data, platform=platform)
                _handle_result(r, SyncAction.CREATE_FULL, results, log_tag, sku, ean, product)
                continue

            # CASO 2: Buscar por EAN
            ps_id = await _call(client.find_by_ean, ean, platform=platform) if ean else None
            if ps_id:
                r = await _call(client.update_price_stock, ps_id, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_EAN, results, log_tag, sku, ean, product)
                continue

            # CASO 3: Buscar por SKU
            ps_id = await _call(client.find_by_sku, sku, platform=platform) if sku else None
            if ps_id:
                r = await _call(client.update_price_stock, ps_id, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_SKU, results, log_tag, sku, ean, product)
                continue

            # CASO 4: Crear borrador
            product_data = _build_product_data(product, final_price, stock)
            r = await _call(client.create_draft_product, product_data, platform=platform)
            _handle_result(r, SyncAction.CREATE_DRAFT, results, log_tag, sku, ean, product)

        except Exception as exc:
            results["summary"]["failed"] += 1
            results["errors"].append(f"{sku or ean}: {str(exc)[:100]}")
            logger.error(f"{log_tag} → ERROR: {exc}")


# ============================================================
# SHOPIFY
# ============================================================

async def _sync_shopify(
    store_config: dict,
    catalog_items: list,
    margin_rules: list,
    results: dict,
    sync_id: str,
):
    from services.platforms.shopify_client import ShopifyClient
    from services.sync import calculate_final_price

    client = ShopifyClient(
        store_url=store_config.get("store_url", ""),
        access_token=store_config.get("access_token", ""),
        api_version=store_config.get("api_version", "2024-10"),
    )
    platform = "shopify"

    store_is_empty = not await _call(client.has_products, platform=platform)

    # Pre-construir índice EAN+SKU si la tienda tiene productos
    by_ean: dict[str, tuple] = {}
    by_sku: dict[str, tuple] = {}
    if not store_is_empty:
        by_ean, by_sku = await _call(client.build_product_index, platform=platform)
        logger.info(
            f"[{sync_id}] Shopify índice construido: {len(by_ean)} EAN, {len(by_sku)} SKU"
        )

    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]})
        if not product:
            results["summary"]["skipped"] += 1
            continue

        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        stock = product.get("stock", 0)
        ean = (product.get("ean") or "").strip()
        sku = (product.get("sku") or "").strip()
        log_tag = f"[{sync_id}] SH | {sku or ean or product['id']}"

        try:
            if store_is_empty:
                # CASO 1: Subir completo publicado
                product_data = _build_product_data(product, final_price, stock)
                r = await _call(client.create_product, product_data, platform=platform)
                _handle_result(r, SyncAction.CREATE_FULL, results, log_tag, sku, ean, product)
                continue

            # CASO 2: Buscar por EAN
            match_ean = by_ean.get(ean) if ean else None
            if match_ean:
                pid, vid = match_ean
                r = await _call(client.update_price_stock, pid, vid, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_EAN, results, log_tag, sku, ean, product)
                continue

            # CASO 3: Buscar por SKU
            match_sku = by_sku.get(sku) if sku else None
            if match_sku:
                pid, vid = match_sku
                r = await _call(client.update_price_stock, pid, vid, final_price, stock, platform=platform)
                _handle_result(r, SyncAction.UPDATE_BY_SKU, results, log_tag, sku, ean, product)
                continue

            # CASO 4: Crear borrador
            product_data = _build_product_data(product, final_price, stock)
            r = await _call(client.create_draft_product, product_data, platform=platform)
            _handle_result(r, SyncAction.CREATE_DRAFT, results, log_tag, sku, ean, product)

        except Exception as exc:
            results["summary"]["failed"] += 1
            results["errors"].append(f"{sku or ean}: {str(exc)[:100]}")
            logger.error(f"{log_tag} → ERROR: {exc}")


# ============================================================
# UTILIDADES INTERNAS
# ============================================================

def _build_product_data(product: dict, price: float, stock: int) -> dict:
    """Construye el dict de datos de producto para crear en tienda."""
    return {
        "sku": product.get("sku", ""),
        "ean": product.get("ean", ""),
        "name": product.get("name", ""),
        "price": round(price, 2),
        "stock": stock,
        "short_description": product.get("short_description", ""),
        "long_description": product.get("long_description") or product.get("description", ""),
        "description": product.get("description", ""),
        "brand": product.get("brand", ""),
        "weight": product.get("weight", 0),
        "image_url": product.get("image_url", ""),
        "gallery_images": product.get("gallery_images", []),
        "category": product.get("category", ""),
    }


def _handle_result(
    r: dict,
    action: SyncAction,
    results: dict,
    log_tag: str,
    sku: str,
    ean: str,
    product: dict,
):
    """Registra el resultado de una operación de sync en el resumen."""
    if r.get("status") == "success":
        key = action.value.lower()  # create_full, update_by_ean, etc.
        results["summary"][key] += 1
        if action == SyncAction.CREATE_DRAFT:
            results["draft_products"].append({
                "sku": sku,
                "ean": ean,
                "name": product.get("name", ""),
                "store_product_id": r.get("product_id"),
                "reason": "Sin coincidencia por EAN ni SKU",
            })
            logger.info(
                f"{log_tag} → {action.value} "
                f"(id={r.get('product_id')}) — requiere revisión manual"
            )
        else:
            logger.info(f"{log_tag} → {action.value}")
    else:
        results["summary"]["failed"] += 1
        error_msg = r.get("message", "Error desconocido")
        results["errors"].append(f"{sku or ean}: {error_msg[:100]}")
        logger.warning(f"{log_tag} → {action.value} FALLIDO: {error_msg[:80]}")
