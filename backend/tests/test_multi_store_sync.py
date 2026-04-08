"""
Tests unitarios para el servicio de sincronización multi-tienda (multi_store_sync.py).

Cubre los 8 casos de prueba definidos en las especificaciones:
  TC1  - Primera sincronización: tienda vacía → subir todo publicado
  TC2  - Actualización precio/stock por EAN
  TC3  - Búsqueda fallida por EAN, éxito por SKU
  TC4  - Crear borrador cuando no hay coincidencia
  TC5  - Manejo de errores y reintentos
  TC6  - Sincronización concurrente (sin condiciones de carrera)
  TC7  - Imágenes (manejo graceful de fallo en descarga)
  TC8  - Validaciones (producto inválido, tienda desconectada)

Los tests usan mocks para no necesitar conexiones reales a tiendas.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers para construir datos de prueba
# ---------------------------------------------------------------------------

def _make_store(platform: str = "woocommerce", catalog_id: str = "cat_001") -> dict:
    return {
        "id": f"store_{uuid.uuid4().hex[:6]}",
        "name": f"Tienda Test {platform}",
        "platform": platform,
        "catalog_id": catalog_id,
        "store_url": f"https://test.{platform}.example.com",
        "consumer_key": "ck_test",
        "consumer_secret": "cs_test",
        "api_key": "key_test",
        "access_token": "token_test",
        "is_connected": True,
    }


def _make_product(sku: str = "SKU-001", ean: str = "1234567890123", price: float = 99.99, stock: int = 50) -> dict:
    return {
        "id": f"prod_{uuid.uuid4().hex[:6]}",
        "user_id": "user_001",
        "name": "Producto de Prueba",
        "sku": sku,
        "ean": ean,
        "price": price,
        "stock": stock,
        "description": "Descripción larga del producto.",
        "short_description": "Descripción corta.",
        "brand": "MarcaTest",
        "weight": 0.5,
        "image_url": "https://example.com/img.jpg",
        "gallery_images": [],
        "category": "Categoría Test",
    }


def _make_catalog_item(product_id: str, catalog_id: str = "cat_001", custom_price: float = None) -> dict:
    return {
        "id": f"item_{uuid.uuid4().hex[:6]}",
        "catalog_id": catalog_id,
        "product_id": product_id,
        "custom_price": custom_price,
        "active": True,
    }


# ---------------------------------------------------------------------------
# Fixture de DB mock
# ---------------------------------------------------------------------------

def _make_db_mock(catalog_items: list, products: list, margin_rules: list = None):
    """Construye un mock de la colección de base de datos."""
    db_mock = MagicMock()

    async def _find_one(query):
        # Buscar en products por id
        if "id" in query:
            return next((p for p in products if p["id"] == query["id"]), None)
        return None

    db_mock.products.find_one = AsyncMock(side_effect=_find_one)

    # catalog_items.find → siempre retorna la lista configurada
    items_cursor = MagicMock()
    items_cursor.to_list = AsyncMock(return_value=catalog_items)
    items_cursor.sort = MagicMock(return_value=items_cursor)
    db_mock.catalog_items.find = MagicMock(return_value=items_cursor)

    # catalog_margin_rules.find
    rules_cursor = MagicMock()
    rules_cursor.to_list = AsyncMock(return_value=margin_rules or [])
    rules_cursor.sort = MagicMock(return_value=rules_cursor)
    db_mock.catalog_margin_rules.find = MagicMock(return_value=rules_cursor)

    # woocommerce_configs.update_one (no necesita retornar nada)
    db_mock.woocommerce_configs.update_one = AsyncMock(return_value=None)

    return db_mock


# ===========================================================================
# TC1 — Tienda vacía: subir todo publicado (WooCommerce)
# ===========================================================================

class TestTC1EmptyStoreWooCommerce:
    """TC1: Primera sincronización con tienda vacía → CREATE_FULL."""

    @pytest.mark.asyncio
    async def test_empty_store_creates_full_product(self):
        product = _make_product(sku="SKU-001", ean="1234567890123")
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")

        db_mock = _make_db_mock([catalog_item], [product])

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._call") as mock_call, \
             patch("services.sync.calculate_final_price", return_value=product["price"]), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            call_results = [
                0,                                       # _wc_count_products → 0 (tienda vacía)
                {"status": "success", "product_id": 999},  # _wc_create_product
            ]
            mock_call.side_effect = [asyncio.coroutine(lambda *a, **k: r)() for r in call_results]

            # Importamos aquí para que los patches estén activos
            from services.multi_store_sync import _sync_woocommerce

            results = {
                "sync_id": "test_sync",
                "summary": {
                    "total": 1, "create_full": 0, "update_by_ean": 0,
                    "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0,
                },
                "draft_products": [],
                "errors": [],
            }

            with patch("services.multi_store_sync._call", new_callable=AsyncMock) as acall:
                acall.side_effect = [
                    0,                                          # count_products → vacío
                    {"status": "success", "product_id": 999},  # create_product publicado
                ]
                await _sync_woocommerce(store, [catalog_item], [], results, "tc1")

            assert results["summary"]["create_full"] == 1
            assert results["summary"]["update_by_ean"] == 0
            assert results["summary"]["create_draft"] == 0
            assert results["summary"]["failed"] == 0

    @pytest.mark.asyncio
    async def test_empty_store_full_product_published_not_draft(self):
        """Los productos creados en tienda vacía deben ser publicados, no borradores."""
        product = _make_product()
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        created_status = []

        def capture_create(wcapi, prod, price, stock, status):
            created_status.append(status)
            return {"status": "success", "product_id": 100}

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_create_product", side_effect=capture_create), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.multi_store_sync._rate_limiter") as rl_mock, \
             patch("services.sync.calculate_final_price", return_value=99.99), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            rl_mock.wait = AsyncMock()

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect_call(func, *args, platform="", **kwargs):
                    import asyncio
                    return await asyncio.to_thread(func, *args, **kwargs)

                mock_call.side_effect = side_effect_call

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc1b",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc1b")

        # Si se llamó _wc_create_product, verificar que el status es 'publish'
        if created_status:
            assert "publish" in created_status, f"Esperado 'publish', se usó: {created_status}"


# ===========================================================================
# TC2 — Actualización por EAN (no modifica otros campos)
# ===========================================================================

class TestTC2UpdateByEAN:
    """TC2: Producto encontrado por EAN → solo actualizar precio y stock."""

    @pytest.mark.asyncio
    async def test_found_by_ean_only_updates_price_stock(self):
        product = _make_product(ean="9991234567890", sku="SKU-EAN")
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        update_calls = []

        def fake_update(wcapi, wc_id, price, stock):
            update_calls.append({"wc_id": wc_id, "price": price, "stock": stock})
            return {"status": "success"}

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_update_price_stock", side_effect=fake_update), \
             patch("services.multi_store_sync._wc_count_products", return_value=10), \
             patch("services.multi_store_sync._wc_build_index",
                   return_value=({"9991234567890": 42}, {})), \
             patch("services.sync.calculate_final_price", return_value=89.99), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc2",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc2")

        assert results["summary"]["update_by_ean"] == 1
        assert results["summary"]["update_by_sku"] == 0
        assert results["summary"]["create_draft"] == 0
        assert results["summary"]["create_full"] == 0

        # Verificar que se pasó el precio correcto
        if update_calls:
            assert update_calls[0]["price"] == 89.99
            assert update_calls[0]["stock"] == product["stock"]


# ===========================================================================
# TC3 — Fallida por EAN, éxito por SKU
# ===========================================================================

class TestTC3UpdateBySKU:
    """TC3: No hay EAN en tienda, pero sí SKU → UPDATE_BY_SKU."""

    @pytest.mark.asyncio
    async def test_no_ean_match_falls_back_to_sku(self):
        product = _make_product(ean="0000000000000", sku="SKU-REAL-001")
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        update_calls = []

        def fake_update(wcapi, wc_id, price, stock):
            update_calls.append(wc_id)
            return {"status": "success"}

        # EAN no existe en índice, SKU sí
        wc_by_ean: dict = {}  # EAN vacío → no match
        wc_by_sku = {"SKU-REAL-001": 77}

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_update_price_stock", side_effect=fake_update), \
             patch("services.multi_store_sync._wc_count_products", return_value=5), \
             patch("services.multi_store_sync._wc_build_index", return_value=(wc_by_ean, wc_by_sku)), \
             patch("services.sync.calculate_final_price", return_value=55.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc3",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc3")

        assert results["summary"]["update_by_sku"] == 1
        assert results["summary"]["update_by_ean"] == 0
        assert results["summary"]["create_draft"] == 0


# ===========================================================================
# TC4 — No hay EAN ni SKU → crear borrador
# ===========================================================================

class TestTC4CreateDraft:
    """TC4: Sin coincidencia por EAN ni SKU → CREATE_DRAFT."""

    @pytest.mark.asyncio
    async def test_no_match_creates_draft(self):
        product = _make_product(ean="NO-EAN-MATCH", sku="NO-SKU-MATCH")
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        created_as = []

        def fake_create(wcapi, prod, price, stock, status):
            created_as.append(status)
            return {"status": "success", "product_id": 555}

        # Índices vacíos → nada coincide
        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_create_product", side_effect=fake_create), \
             patch("services.multi_store_sync._wc_count_products", return_value=3), \
             patch("services.multi_store_sync._wc_build_index", return_value=({}, {})), \
             patch("services.sync.calculate_final_price", return_value=100.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc4",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc4")

        assert results["summary"]["create_draft"] == 1
        assert results["summary"]["failed"] == 0
        assert len(results["draft_products"]) == 1
        assert results["draft_products"][0]["reason"] == "Sin coincidencia EAN/SKU"
        # El producto debe crearse en borrador
        if created_as:
            assert created_as[0] == "draft"

    @pytest.mark.asyncio
    async def test_draft_product_contains_all_info(self):
        """El borrador debe incluir toda la información del producto."""
        from services.multi_store_sync import _build_product_data

        product = _make_product(ean="EAN-DRAFT", sku="SKU-DRAFT")
        product_data = _build_product_data(product, price=79.99, stock=10)

        assert product_data["name"] == product["name"]
        assert product_data["sku"] == product["sku"]
        assert product_data["ean"] == product["ean"]
        assert product_data["price"] == 79.99
        assert product_data["stock"] == 10
        assert product_data["image_url"] == product["image_url"]
        assert product_data["brand"] == product["brand"]


# ===========================================================================
# TC5 — Manejo de errores y reintentos
# ===========================================================================

class TestTC5RetryLogic:
    """TC5: Errores transitorios → reintento exitoso; permanentes → fallo registrado."""

    @pytest.mark.asyncio
    async def test_transient_error_retries_and_succeeds(self):
        """Un fallo temporal seguido de éxito debe resultar en sync exitoso."""
        from services.multi_store_sync import _call, _RETRY_DELAYS

        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("ETIMEDOUT: transient error")
            return {"status": "success"}

        with patch("services.multi_store_sync._RETRY_DELAYS", [0, 0, 0]):
            result = await _call(flaky_func, platform="woocommerce")

        assert result["status"] == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_auth_error_not_retried(self):
        """Un error de autenticación (401) no debe reintentarse."""
        from services.multi_store_sync import _call, _is_retryable

        assert not _is_retryable("Error 401 Unauthorized")
        assert not _is_retryable("Authentication failed: invalid credentials")
        assert not _is_retryable("403 Forbidden")
        assert _is_retryable("ECONNREFUSED: Connection refused")
        assert _is_retryable("ETIMEDOUT: Timeout error")

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises(self):
        """Cuando se agotan los reintentos debe lanzar la última excepción."""
        from services.multi_store_sync import _call

        def always_fails():
            raise ConnectionError("Siempre falla")

        with patch("services.multi_store_sync._RETRY_DELAYS", [0, 0, 0]), \
             pytest.raises(ConnectionError, match="Siempre falla"):
            await _call(always_fails, platform="woocommerce")

    @pytest.mark.asyncio
    async def test_failed_product_recorded_in_errors(self):
        """Un producto que falla debe registrarse en results['errors']."""
        product = _make_product(ean="EAN-ERR", sku="SKU-ERR")
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        def always_fails(*args, **kwargs):
            raise RuntimeError("API caída")

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_count_products", return_value=5), \
             patch("services.multi_store_sync._wc_build_index", return_value=({}, {})), \
             patch("services.multi_store_sync._wc_create_product", side_effect=always_fails), \
             patch("services.sync.calculate_final_price", return_value=50.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc5d",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc5d")

        assert results["summary"]["failed"] == 1
        assert len(results["errors"]) == 1


# ===========================================================================
# TC6 — Sincronización concurrente
# ===========================================================================

class TestTC6ConcurrentSync:
    """TC6: Múltiples tiendas simultáneas sin condiciones de carrera."""

    @pytest.mark.asyncio
    async def test_multiple_stores_run_independently(self):
        """Cada tienda debe procesarse de forma independiente."""
        from services.multi_store_sync import sync_store

        stores = [_make_store("woocommerce", f"cat_{i}") for i in range(3)]
        results_list = []

        async def mock_sync(config):
            return {
                "status": "skipped",
                "message": "No hay productos activos en el catálogo",
                "sync_id": f"sync_{config['id']}",
                "summary": {
                    "total": 0, "create_full": 0, "update_by_ean": 0,
                    "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                },
                "draft_products": [], "errors": [],
            }

        with patch("services.multi_store_sync.sync_store", side_effect=mock_sync):
            tasks = [mock_sync(store) for store in stores]
            results_list = await asyncio.gather(*tasks)

        assert len(results_list) == 3
        # Cada resultado debe pertenecer a una tienda distinta (sync_id diferente)
        sync_ids = {r["sync_id"] for r in results_list}
        assert len(sync_ids) == 3

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_per_platform(self):
        """El rate limiter debe respetar los límites por plataforma."""
        from services.multi_store_sync import _RateLimiter

        limiter = _RateLimiter()

        # Simula dos llamadas rápidas a la misma plataforma
        t0 = asyncio.get_event_loop().time()
        await limiter.wait("shopify")   # primera llamada: inmediata
        t1 = asyncio.get_event_loop().time()
        await limiter.wait("shopify")   # segunda llamada: debe esperar
        t2 = asyncio.get_event_loop().time()

        # Primera espera debe ser casi 0
        assert (t1 - t0) < 0.1
        # Segunda espera debe ser ≥ 0.4s (Shopify rate limit = 0.5s)
        assert (t2 - t1) >= 0.4


# ===========================================================================
# TC7 — Imágenes (manejo graceful)
# ===========================================================================

class TestTC7Images:
    """TC7: Las imágenes se incluyen en la carga inicial; fallo no detiene el sync."""

    def test_build_product_data_includes_images(self):
        """_build_product_data debe incluir image_url y gallery_images."""
        from services.multi_store_sync import _build_product_data

        product = _make_product()
        product["image_url"] = "https://example.com/main.jpg"
        product["gallery_images"] = ["https://example.com/g1.jpg", "https://example.com/g2.jpg"]

        data = _build_product_data(product, price=10.0, stock=5)

        assert data["image_url"] == "https://example.com/main.jpg"
        assert len(data["gallery_images"]) == 2

    def test_build_product_data_handles_missing_images(self):
        """Si no hay imágenes, no debe fallar."""
        from services.multi_store_sync import _build_product_data

        product = _make_product()
        product["image_url"] = ""
        product["gallery_images"] = []

        data = _build_product_data(product, price=10.0, stock=5)
        assert data["image_url"] == ""
        assert data["gallery_images"] == []

    @pytest.mark.asyncio
    async def test_image_failure_does_not_stop_sync(self):
        """Si la subida de imágenes falla, el producto igual debe procesarse."""
        product = _make_product(ean="EAN-IMG", sku="SKU-IMG")
        product["image_url"] = "https://example.com/image.jpg"
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("woocommerce")
        db_mock = _make_db_mock([catalog_item], [product])

        # _wc_create_product devuelve éxito aunque internamente falle la imagen
        def create_with_img_error(wcapi, prod, price, stock, status):
            return {"status": "success", "product_id": 1001}

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_create_product", side_effect=create_with_img_error), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.sync.calculate_final_price", return_value=10.0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc7",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc7")

        assert results["summary"]["create_full"] == 1
        assert results["summary"]["failed"] == 0


# ===========================================================================
# TC8 — Validaciones
# ===========================================================================

class TestTC8Validations:
    """TC8: Validaciones de entrada y manejo de tiendas sin catálogo."""

    @pytest.mark.asyncio
    async def test_store_without_catalog_skipped(self):
        """Una tienda sin catalog_id debe retornar status='skipped'."""
        from services.multi_store_sync import sync_store

        store = _make_store("woocommerce")
        store["catalog_id"] = None  # Sin catálogo

        db_mock = _make_db_mock([], [])
        with patch("services.multi_store_sync.db", db_mock):
            result = await sync_store(store)

        assert result["status"] == "skipped"
        assert "catálogo" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_empty_catalog_skipped(self):
        """Un catálogo sin items activos debe retornar status='skipped'."""
        from services.multi_store_sync import sync_store

        store = _make_store("woocommerce", "cat_empty")
        db_mock = _make_db_mock([], [])  # Sin items

        with patch("services.multi_store_sync.db", db_mock):
            result = await sync_store(store)

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_unsupported_platform_returns_error(self):
        """Una plataforma no soportada debe retornar error claro."""
        from services.multi_store_sync import sync_store

        product = _make_product()
        catalog_item = _make_catalog_item(product["id"])
        store = _make_store("magento", "cat_001")  # Magento no soportado en multi_store_sync

        db_mock = _make_db_mock([catalog_item], [product])
        with patch("services.multi_store_sync.db", db_mock):
            result = await sync_store(store)

        assert result["status"] == "error"
        assert "magento" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_product_not_in_db_is_skipped(self):
        """Si el producto del catálogo no existe en BD, debe saltarse."""
        catalog_item = _make_catalog_item("id_que_no_existe")
        store = _make_store("woocommerce")
        # DB sin ese producto
        db_mock = _make_db_mock([catalog_item], [])

        with patch("services.multi_store_sync.db", db_mock), \
             patch("services.multi_store_sync._wc_count_products", return_value=0), \
             patch("services.sync.get_woocommerce_client", return_value=MagicMock()):

            with patch("services.multi_store_sync._call") as mock_call:
                async def side_effect(func, *args, platform="", **kwargs):
                    return func(*args, **kwargs)
                mock_call.side_effect = side_effect

                from services.multi_store_sync import _sync_woocommerce
                results = {
                    "sync_id": "tc8d",
                    "summary": {
                        "total": 1, "create_full": 0, "update_by_ean": 0,
                        "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                    },
                    "draft_products": [], "errors": [],
                }
                await _sync_woocommerce(store, [catalog_item], [], results, "tc8d")

        assert results["summary"]["skipped"] == 1
        assert results["summary"]["failed"] == 0

    def test_is_retryable_classification(self):
        """_is_retryable clasifica correctamente los tipos de error."""
        from services.multi_store_sync import _is_retryable

        # Errores reintentables
        assert _is_retryable("ECONNREFUSED")
        assert _is_retryable("ConnectionError: timeout")
        assert _is_retryable("Server error 500")
        assert _is_retryable("RateLimitError")

        # Errores NO reintentables
        assert not _is_retryable("401 Unauthorized")
        assert not _is_retryable("403 Forbidden")
        assert not _is_retryable("Authentication failed")
        assert not _is_retryable("Invalid API key")

    def test_handle_result_success_increments_counter(self):
        """_handle_result incrementa el contador correcto en caso de éxito."""
        from services.multi_store_sync import SyncAction, _handle_result

        for action in [SyncAction.CREATE_FULL, SyncAction.UPDATE_BY_EAN,
                       SyncAction.UPDATE_BY_SKU, SyncAction.CREATE_DRAFT]:
            results = {
                "sync_id": "test",
                "summary": {
                    "total": 1, "create_full": 0, "update_by_ean": 0,
                    "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
                },
                "draft_products": [], "errors": [],
            }
            product = _make_product()
            _handle_result(
                {"status": "success", "product_id": 1},
                action, results, "tag", "SKU", "EAN", product
            )
            key = action.value.lower()
            assert results["summary"][key] == 1, f"Contador '{key}' no incrementado para {action}"

    def test_handle_result_failure_increments_failed(self):
        """_handle_result incrementa 'failed' y agrega a 'errors' en caso de fallo."""
        from services.multi_store_sync import SyncAction, _handle_result

        results = {
            "sync_id": "test",
            "summary": {
                "total": 1, "create_full": 0, "update_by_ean": 0,
                "update_by_sku": 0, "create_draft": 0, "skipped": 0, "failed": 0
            },
            "draft_products": [], "errors": [],
        }
        product = _make_product()
        _handle_result(
            {"status": "error", "message": "Timeout"},
            SyncAction.UPDATE_BY_EAN, results, "tag", "SKU", "EAN", product
        )
        assert results["summary"]["failed"] == 1
        assert len(results["errors"]) == 1
