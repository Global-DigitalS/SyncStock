"""
Tests unitarios para el servicio de sincronización multi-tienda (multi_store_sync.py).

TC1  - Tienda vacía → CREATE_FULL (publicado)
TC2  - Encontrado por EAN → UPDATE_BY_EAN (solo precio + stock)
TC3  - Fallback a SKU → UPDATE_BY_SKU
TC4  - Sin coincidencia → CREATE_DRAFT (borrador)
TC5  - Reintentos con backoff exponencial
TC6  - Sincronización concurrente / rate limiter
TC7  - Imágenes incluidas / fallo graceful
TC8  - Validaciones de entrada
TC_PS  - PrestaShop: los 4 casos del algoritmo
TC_SH  - Shopify: los 4 casos del algoritmo
"""
import asyncio
import sys
import uuid
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Registrar servicios pesados como mocks antes de que se importen los módulos
# bajo prueba. Esto evita instalar dependencias opcionales (paramiko, xlrd…)
# en el entorno de CI.
# ---------------------------------------------------------------------------
def _make_services_mock():
    """Crea mocks para los módulos de servicios que tienen deps pesadas."""
    # services.sync
    _sync = MagicMock()
    _sync.calculate_final_price.side_effect = lambda base, product, rules: float(base)
    _sync.get_woocommerce_client.return_value = MagicMock()
    _sync.sync_woocommerce_store_price_stock = MagicMock()
    sys.modules.setdefault("services.sync", _sync)

    # Asegurar que services.sync esté accesible desde el paquete services
    _services_pkg = sys.modules.get("services")
    if _services_pkg is not None and not hasattr(_services_pkg, "sync"):
        _services_pkg.sync = _sync


_make_services_mock()


# ---------------------------------------------------------------------------
# Helpers de datos de prueba
# ---------------------------------------------------------------------------

def _store(platform: str = "woocommerce", catalog_id: str = "cat_001") -> dict:
    return {
        "id": f"store_{uuid.uuid4().hex[:6]}",
        "name": f"Tienda {platform}",
        "platform": platform,
        "catalog_id": catalog_id,
        "store_url": f"https://test.example.com",
        "consumer_key": "ck_test",
        "consumer_secret": "cs_test",
        "api_key": "key_test",
        "access_token": "token_test",
        "is_connected": True,
    }


def _product(sku: str = "SKU-001", ean: str = "1234567890123",
             price: float = 99.99, stock: int = 50) -> dict:
    return {
        "id": f"prod_{uuid.uuid4().hex[:6]}",
        "user_id": "user_001",
        "name": "Producto de Prueba",
        "sku": sku,
        "ean": ean,
        "price": price,
        "stock": stock,
        "description": "Descripción larga.",
        "short_description": "Corta.",
        "brand": "MarcaTest",
        "weight": 0.5,
        "image_url": "https://example.com/img.jpg",
        "gallery_images": [],
        "category": "Cat",
    }


def _item(product_id: str, catalog_id: str = "cat_001",
          custom_price: Optional[float] = None) -> dict:
    return {
        "id": f"item_{uuid.uuid4().hex[:6]}",
        "catalog_id": catalog_id,
        "product_id": product_id,
        "custom_price": custom_price,
        "active": True,
    }


def _make_db(items: list, products: list, rules: list = None) -> MagicMock:
    """Construye mock de DB con catalog_items, products y margin_rules."""
    db = MagicMock()

    async def _find_one(query):
        pid = query.get("id")
        return next((p for p in products if p["id"] == pid), None)

    db.products.find_one = AsyncMock(side_effect=_find_one)

    cur_items = MagicMock()
    cur_items.to_list = AsyncMock(return_value=items)
    db.catalog_items.find = MagicMock(return_value=cur_items)

    cur_rules = MagicMock()
    cur_rules.to_list = AsyncMock(return_value=rules or [])
    cur_rules.sort = MagicMock(return_value=cur_rules)
    db.catalog_margin_rules.find = MagicMock(return_value=cur_rules)

    db.woocommerce_configs.update_one = AsyncMock(return_value=None)
    return db


# ---------------------------------------------------------------------------
# Fixture para parchear _call ejecutando la función real síncronamente
# ---------------------------------------------------------------------------

def _real_call_patch():
    """Devuelve un side_effect que ejecuta func(*args) en thread pool."""
    async def _side(func, *args, platform="", **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return _side


# ===========================================================================
# TC1 — Tienda vacía: CREATE_FULL
# ===========================================================================

class TestTC1EmptyStore:

    @pytest.mark.asyncio
    async def test_create_full_on_empty_store(self):
        prod = _product()
        store = _store()
        db = _make_db([_item(prod["id"])], [prod])

        created = []

        def fake_create(wcapi, product, price, stock, status):
            created.append(status)
            return {"status": "success", "product_id": 100}

        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.multi_store_sync._wc_create_product", side_effect=fake_create), \
             patch("services.sync.calculate_final_price", return_value=99.99), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item(prod["id"])], [], results, "tc1")

        assert results["summary"]["create_full"] == 1
        assert results["summary"]["update_by_ean"] == 0
        assert results["summary"]["create_draft"] == 0
        assert results["summary"]["failed"] == 0
        # Asegurar que el status es "publish", no "draft"
        assert created == ["publish"]


# ===========================================================================
# TC2 — UPDATE_BY_EAN
# ===========================================================================

class TestTC2UpdateByEAN:

    @pytest.mark.asyncio
    async def test_found_by_ean_updates_price_stock_only(self):
        prod = _product(ean="EAN-001", sku="SKU-A")
        store = _store()
        db = _make_db([_item(prod["id"])], [prod])

        updated = []

        def fake_update(wcapi, wc_id, price, stock):
            updated.append({"wc_id": wc_id, "price": price, "stock": stock})
            return {"status": "success"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=5), \
             patch("services.multi_store_sync._wc_build_index",
                   return_value=({"EAN-001": 42}, {})), \
             patch("services.multi_store_sync._wc_update_price_stock", side_effect=fake_update), \
             patch("services.sync.calculate_final_price", return_value=89.99), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item(prod["id"])], [], results, "tc2")

        assert results["summary"]["update_by_ean"] == 1
        assert results["summary"]["update_by_sku"] == 0
        assert results["summary"]["create_draft"] == 0
        assert updated[0]["price"] == 89.99
        assert updated[0]["stock"] == prod["stock"]


# ===========================================================================
# TC3 — UPDATE_BY_SKU (fallback cuando EAN no coincide)
# ===========================================================================

class TestTC3UpdateBySKU:

    @pytest.mark.asyncio
    async def test_sku_fallback_when_no_ean_match(self):
        prod = _product(ean="NO-MATCH", sku="SKU-REAL")
        store = _store()
        db = _make_db([_item(prod["id"])], [prod])

        updated = []

        def fake_update(wcapi, wc_id, price, stock):
            updated.append(wc_id)
            return {"status": "success"}

        # EAN no está en índice; SKU sí
        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=5), \
             patch("services.multi_store_sync._wc_build_index",
                   return_value=({}, {"SKU-REAL": 77})), \
             patch("services.multi_store_sync._wc_update_price_stock", side_effect=fake_update), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item(prod["id"])], [], results, "tc3")

        assert results["summary"]["update_by_sku"] == 1
        assert results["summary"]["update_by_ean"] == 0
        assert results["summary"]["create_draft"] == 0
        assert updated == [77]


# ===========================================================================
# TC4 — CREATE_DRAFT cuando ningún identificador coincide
# ===========================================================================

class TestTC4CreateDraft:

    @pytest.mark.asyncio
    async def test_no_match_creates_draft_with_all_info(self):
        prod = _product(ean="NO-EAN", sku="NO-SKU")
        store = _store()
        db = _make_db([_item(prod["id"])], [prod])

        statuses = []

        def fake_create(wcapi, product, price, stock, status):
            statuses.append(status)
            return {"status": "success", "product_id": 555}

        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=3), \
             patch("services.multi_store_sync._wc_build_index", return_value=({}, {})), \
             patch("services.multi_store_sync._wc_create_product", side_effect=fake_create), \
             patch("services.sync.calculate_final_price", return_value=100.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item(prod["id"])], [], results, "tc4")

        assert results["summary"]["create_draft"] == 1
        assert results["summary"]["failed"] == 0
        assert len(results["draft_products"]) == 1
        assert results["draft_products"][0]["sku"] == prod["sku"]
        assert statuses == ["draft"]

    def test_build_product_data_includes_all_fields(self):
        from services.multi_store_sync import _build_product_data
        prod = _product()
        data = _build_product_data(prod, price=79.99, stock=10)
        for field in ("sku", "ean", "name", "price", "stock", "image_url", "brand", "description"):
            assert field in data, f"Campo '{field}' faltante"
        assert data["price"] == 79.99
        assert data["stock"] == 10


# ===========================================================================
# TC5 — Reintentos con backoff exponencial
# ===========================================================================

class TestTC5Retry:

    @pytest.mark.asyncio
    async def test_retries_on_transient_error_then_succeeds(self):
        from services.multi_store_sync import _call, _RETRY_DELAYS

        attempts = []

        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionError("ETIMEDOUT")
            return {"status": "success"}

        with patch("services.multi_store_sync._RETRY_DELAYS", [0, 0, 0]):
            result = await _call(flaky, platform="woocommerce")

        assert result["status"] == "success"
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_auth_error_not_retried(self):
        from services.multi_store_sync import _call

        attempts = []

        def auth_fail():
            attempts.append(1)
            raise ValueError("401 Unauthorized")

        with patch("services.multi_store_sync._RETRY_DELAYS", [0, 0, 0]):
            with pytest.raises(ValueError):
                await _call(auth_fail, platform="woocommerce")

        assert len(attempts) == 1  # No reintentó

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises_last_error(self):
        from services.multi_store_sync import _call

        def always_fails():
            raise ConnectionError("siempre falla")

        with patch("services.multi_store_sync._RETRY_DELAYS", [0, 0, 0]):
            with pytest.raises(ConnectionError, match="siempre falla"):
                await _call(always_fails, platform="woocommerce")

    def test_is_retryable_classification(self):
        from services.multi_store_sync import _is_retryable

        assert _is_retryable("ECONNREFUSED")
        assert _is_retryable("timeout")
        assert _is_retryable("500 Server Error")
        assert not _is_retryable("401 Unauthorized")
        assert not _is_retryable("403 Forbidden")
        assert not _is_retryable("Authentication failed")
        assert not _is_retryable("Invalid API key")

    @pytest.mark.asyncio
    async def test_failed_product_recorded_in_errors(self):
        prod = _product()
        store = _store()
        db = _make_db([_item(prod["id"])], [prod])

        def crash(*a, **kw):
            raise RuntimeError("API caída")

        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.multi_store_sync._wc_create_product", side_effect=crash), \
             patch("services.sync.calculate_final_price", return_value=50.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item(prod["id"])], [], results, "tc5e")

        assert results["summary"]["failed"] == 1
        assert len(results["errors"]) == 1


# ===========================================================================
# TC6 — Rate limiter: sin race condition
# ===========================================================================

class TestTC6RateLimiter:

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_delay(self):
        from services.multi_store_sync import _RateLimiter
        import time

        limiter = _RateLimiter()
        t0 = asyncio.get_event_loop().time()
        await limiter.wait("shopify")
        t1 = asyncio.get_event_loop().time()
        await limiter.wait("shopify")
        t2 = asyncio.get_event_loop().time()

        # Primera llamada: casi inmediata
        assert (t1 - t0) < 0.1
        # Segunda llamada: debe haber esperado ≥ 0.4s (Shopify = 0.5s)
        assert (t2 - t1) >= 0.4

    @pytest.mark.asyncio
    async def test_rate_limiter_different_platforms_independent(self):
        from services.multi_store_sync import _RateLimiter
        limiter = _RateLimiter()
        # Llamadas a plataformas distintas no deben bloquearse entre sí
        t0 = asyncio.get_event_loop().time()
        await limiter.wait("woocommerce")
        await limiter.wait("shopify")   # plataforma diferente → no espera
        elapsed = asyncio.get_event_loop().time() - t0
        assert elapsed < 0.3


# ===========================================================================
# TC7 — Imágenes
# ===========================================================================

class TestTC7Images:

    def test_build_product_data_includes_images(self):
        from services.multi_store_sync import _build_product_data
        prod = _product()
        prod["gallery_images"] = ["https://example.com/g1.jpg"]
        data = _build_product_data(prod, 10.0, 5)
        assert data["image_url"] == prod["image_url"]
        assert len(data["gallery_images"]) == 1

    def test_build_product_data_handles_no_images(self):
        from services.multi_store_sync import _build_product_data
        prod = _product()
        prod["image_url"] = ""
        prod["gallery_images"] = []
        data = _build_product_data(prod, 10.0, 5)
        assert data["image_url"] == ""
        assert data["gallery_images"] == []


# ===========================================================================
# TC8 — Validaciones de entrada
# ===========================================================================

class TestTC8Validations:

    @pytest.mark.asyncio
    async def test_store_without_catalog_is_skipped(self):
        from services.multi_store_sync import sync_store
        store = _store()
        store["catalog_id"] = None
        db = _make_db([], [])
        with patch("services.multi_store_sync.db", db):
            result = await sync_store(store)
        assert result["status"] == "skipped"
        assert "catálogo" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_empty_catalog_is_skipped(self):
        from services.multi_store_sync import sync_store
        db = _make_db([], [])
        with patch("services.multi_store_sync.db", db):
            result = await sync_store(_store())
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_unsupported_platform_returns_error(self):
        from services.multi_store_sync import sync_store
        prod = _product()
        db = _make_db([_item(prod["id"])], [prod])
        with patch("services.multi_store_sync.db", db):
            result = await sync_store(_store("magento"))
        assert result["status"] == "error"
        assert "magento" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_missing_product_in_db_is_skipped(self):
        store = _store()
        db = _make_db([_item("id-inexistente")], [])  # producto no existe

        with patch("services.multi_store_sync.db", db), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_woocommerce
            results = _empty_results()
            await _sync_woocommerce(store, [_item("id-inexistente")], [], results, "tc8d")

        assert results["summary"]["skipped"] == 1
        assert results["summary"]["failed"] == 0

    def test_handle_result_increments_correct_counter(self):
        from services.multi_store_sync import SyncAction, _handle_result

        for action in list(SyncAction):
            if action == SyncAction.SKIPPED:
                continue
            results = _empty_results()
            _handle_result(
                {"status": "success", "product_id": 1},
                action, results, "tag", "SKU", "EAN", _product()
            )
            key = action.value.lower()
            assert results["summary"][key] == 1, f"Contador '{key}' no incrementado para {action}"

    def test_handle_result_failure_increments_failed_and_errors(self):
        from services.multi_store_sync import SyncAction, _handle_result
        results = _empty_results()
        _handle_result(
            {"status": "error", "message": "Timeout"},
            SyncAction.UPDATE_BY_EAN, results, "tag", "SKU", "EAN", _product()
        )
        assert results["summary"]["failed"] == 1
        assert len(results["errors"]) == 1


# ===========================================================================
# TC_PS — PrestaShop: los 4 casos del algoritmo
# ===========================================================================

class TestPrestaShopSync:
    """Verifica los 4 casos del algoritmo para PrestaShop."""

    @pytest.mark.asyncio
    async def test_ps_empty_store_creates_full(self):
        prod = _product()
        store = _store("prestashop")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = False
        mock_client.create_product.return_value = {"status": "success", "product_id": "10"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.prestashop.PrestaShopClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=99.99), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_prestashop
            results = _empty_results()
            await _sync_prestashop(store, [_item(prod["id"])], [], results, "ps1")

        assert results["summary"]["create_full"] == 1

    @pytest.mark.asyncio
    async def test_ps_update_by_ean(self):
        prod = _product(ean="PS-EAN")
        store = _store("prestashop")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.find_by_ean.return_value = "42"
        mock_client.update_price_stock.return_value = {"status": "success"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.prestashop.PrestaShopClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_prestashop
            results = _empty_results()
            await _sync_prestashop(store, [_item(prod["id"])], [], results, "ps2")

        assert results["summary"]["update_by_ean"] == 1

    @pytest.mark.asyncio
    async def test_ps_fallback_to_sku(self):
        prod = _product(ean="NO-MATCH", sku="PS-SKU")
        store = _store("prestashop")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.find_by_ean.return_value = None   # EAN no encontrado
        mock_client.find_by_sku.return_value = "99"
        mock_client.update_price_stock.return_value = {"status": "success"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.prestashop.PrestaShopClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_prestashop
            results = _empty_results()
            await _sync_prestashop(store, [_item(prod["id"])], [], results, "ps3")

        assert results["summary"]["update_by_sku"] == 1

    @pytest.mark.asyncio
    async def test_ps_no_match_creates_draft(self):
        prod = _product(ean="NOPE", sku="NOPE")
        store = _store("prestashop")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.find_by_ean.return_value = None
        mock_client.find_by_sku.return_value = None
        mock_client.create_draft_product.return_value = {"status": "success", "product_id": "77"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.prestashop.PrestaShopClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_prestashop
            results = _empty_results()
            await _sync_prestashop(store, [_item(prod["id"])], [], results, "ps4")

        assert results["summary"]["create_draft"] == 1
        assert len(results["draft_products"]) == 1


# ===========================================================================
# TC_SH — Shopify: los 4 casos del algoritmo
# ===========================================================================

class TestShopifySync:
    """Verifica los 4 casos del algoritmo para Shopify."""

    @pytest.mark.asyncio
    async def test_sh_empty_store_creates_full(self):
        prod = _product()
        store = _store("shopify")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = False
        mock_client.create_product.return_value = {"status": "success", "product_id": 100}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.shopify_client.ShopifyClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=99.99), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_shopify
            results = _empty_results()
            await _sync_shopify(store, [_item(prod["id"])], [], results, "sh1")

        assert results["summary"]["create_full"] == 1

    @pytest.mark.asyncio
    async def test_sh_update_by_ean(self):
        prod = _product(ean="SH-EAN")
        store = _store("shopify")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.build_product_index.return_value = ({"SH-EAN": (1, 11)}, {})
        mock_client.update_price_stock.return_value = {"status": "success"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.shopify_client.ShopifyClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_shopify
            results = _empty_results()
            await _sync_shopify(store, [_item(prod["id"])], [], results, "sh2")

        assert results["summary"]["update_by_ean"] == 1

    @pytest.mark.asyncio
    async def test_sh_fallback_to_sku(self):
        prod = _product(ean="NOPE", sku="SH-SKU")
        store = _store("shopify")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.build_product_index.return_value = ({}, {"SH-SKU": (2, 22)})
        mock_client.update_price_stock.return_value = {"status": "success"}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.shopify_client.ShopifyClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_shopify
            results = _empty_results()
            await _sync_shopify(store, [_item(prod["id"])], [], results, "sh3")

        assert results["summary"]["update_by_sku"] == 1

    @pytest.mark.asyncio
    async def test_sh_no_match_creates_draft(self):
        prod = _product(ean="NOPE", sku="NOPE")
        store = _store("shopify")
        db = _make_db([_item(prod["id"])], [prod])

        mock_client = MagicMock()
        mock_client.has_products.return_value = True
        mock_client.build_product_index.return_value = ({}, {})
        mock_client.create_draft_product.return_value = {"status": "success", "product_id": 200}

        with patch("services.multi_store_sync.db", db), \
             patch("services.platforms.shopify_client.ShopifyClient", return_value=mock_client), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.multi_store_sync._call", side_effect=_real_call_patch()):

            from services.multi_store_sync import _sync_shopify
            results = _empty_results()
            await _sync_shopify(store, [_item(prod["id"])], [], results, "sh4")

        assert results["summary"]["create_draft"] == 1
        assert len(results["draft_products"]) == 1


# ===========================================================================
# Tests unitarios de _escape_cdata (seguridad XML)
# ===========================================================================

class TestEscapeCdata:

    def test_normal_text_unchanged(self):
        from services.platforms.prestashop import _escape_cdata
        assert _escape_cdata("Producto Normal") == "Producto Normal"

    def test_cdata_close_sequence_escaped(self):
        from services.platforms.prestashop import _escape_cdata
        malicious = "test]]>injected"
        result = _escape_cdata(malicious)
        # La técnica estándar para CDATA divide ]]> en dos secciones: ]]]]><![CDATA[>
        # El resultado contiene ]]> como terminador de la primera sección (esperado).
        assert result == "test]]]]><![CDATA[>injected"
        assert "injected" in result

    def test_empty_string_returns_empty(self):
        from services.platforms.prestashop import _escape_cdata
        assert _escape_cdata("") == ""
        assert _escape_cdata(None) == ""


# ---------------------------------------------------------------------------
# Helper compartido
# ---------------------------------------------------------------------------

def _empty_results() -> dict:
    return {
        "sync_id": "test",
        "summary": {
            "total": 0, "create_full": 0, "update_by_ean": 0,
            "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0,
        },
        "draft_products": [],
        "errors": [],
    }
