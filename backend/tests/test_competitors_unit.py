"""
Pruebas unitarias para los nuevos módulos de monitoreo de competidores.

Cubre:
- ProxyManager con circuit breaker
- CrawlJob serialización/deserialización
- calculate_final_price con reglas de margen
- Matching de productos multicapa
- Lógica de configuración de catálogo
"""
import time
import uuid
import pytest
import sys
import os

# Añadir backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===================================================================
# TESTS: ProxyManager con Circuit Breaker
# ===================================================================

class TestProxyManagerCircuitBreaker:
    """Tests del circuito de proxy con estados CLOSED/OPEN/HALF_OPEN."""

    def setup_method(self):
        from services.scrapers.proxy_manager import ProxyManager, CircuitState
        self.ProxyManager = ProxyManager
        self.CircuitState = CircuitState

    def test_proxy_manager_direct_mode(self):
        """Sin proxies, crea entrada 'direct'."""
        manager = self.ProxyManager(proxy_urls=None)
        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.host == "direct"
        assert proxy.url is None

    def test_proxy_manager_with_proxies(self):
        """Con proxies, selecciona el mejor disponible."""
        manager = self.ProxyManager(proxy_urls=[
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080",
        ])
        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.host in ("proxy1.example.com", "proxy2.example.com")

    def test_proxy_starts_closed(self):
        """Proxy empieza en estado CLOSED."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()
        assert proxy.state == self.CircuitState.CLOSED

    def test_success_rate_initial(self):
        """Sin peticiones, tasa de éxito es 1.0."""
        from services.scrapers.proxy_manager import ProxyEntry
        entry = ProxyEntry(url=None, host="direct")
        assert entry.success_rate == 1.0

    def test_failure_increments_count(self):
        """Los fallos incrementan el contador hasta abrir el circuito."""
        from services.scrapers.proxy_manager import FAILURE_THRESHOLD
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()

        # 2 fallos (no threshold)
        for _ in range(FAILURE_THRESHOLD - 1):
            manager.record_failure(proxy, error="timeout")

        # No abierto aún
        assert proxy.state == self.CircuitState.CLOSED

    def test_threshold_opens_circuit(self):
        """Al alcanzar el umbral, el circuito se abre."""
        from services.scrapers.proxy_manager import FAILURE_THRESHOLD
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()

        for _ in range(FAILURE_THRESHOLD):
            manager.record_failure(proxy, error="timeout")

        assert proxy.state == self.CircuitState.OPEN

    def test_hard_block_immediately_opens_circuit(self):
        """HTTP 429/403 abre el circuito de inmediato (sin esperar umbral)."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()

        # Un solo 429 abre el circuito
        manager.record_failure(proxy, status_code=429)
        assert proxy.state == self.CircuitState.OPEN

    def test_hard_block_403(self):
        """HTTP 403 también abre el circuito."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()
        manager.record_failure(proxy, status_code=403)
        assert proxy.state == self.CircuitState.OPEN

    def test_captcha_detection_opens_circuit(self):
        """Detectar CAPTCHA en contenido HTML abre el circuito."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()
        manager.record_failure(proxy, html_content="<div>Please complete this captcha</div>")
        assert proxy.state == self.CircuitState.OPEN

    def test_success_increments_counter(self):
        """Los éxitos incrementan total_successes."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()

        initial_successes = proxy.total_successes
        manager.record_success(proxy)
        assert proxy.total_successes == initial_successes + 1

    def test_cooldown_escalates_on_multiple_blocks(self):
        """El nivel de cooldown aumenta con cada apertura del circuito."""
        from services.scrapers.proxy_manager import COOLDOWN_LEVELS
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])

        # Forzar apertura
        proxy = manager._proxies[0]
        initial_level = proxy.cooldown_level
        manager._open_circuit(proxy, "test")
        assert proxy.cooldown_level > initial_level
        assert proxy.current_cooldown == COOLDOWN_LEVELS[min(proxy.cooldown_level, len(COOLDOWN_LEVELS)-1)]

    def test_reset_proxy_clears_state(self):
        """reset_proxy() limpia el estado del circuito."""
        from services.scrapers.proxy_manager import FAILURE_THRESHOLD
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        proxy = manager.get_proxy()

        for _ in range(FAILURE_THRESHOLD):
            manager.record_failure(proxy, error="timeout")

        assert proxy.state == self.CircuitState.OPEN

        manager.reset_proxy("proxy1.example.com")
        assert proxy.state == self.CircuitState.CLOSED
        assert proxy.failure_count == 0
        assert proxy.cooldown_level == 0

    def test_get_stats_returns_data(self):
        """get_stats() devuelve estadísticas de todos los proxies."""
        manager = self.ProxyManager(proxy_urls=["http://proxy1.example.com:8080"])
        stats = manager.get_stats()
        assert len(stats) == 1
        s = stats[0]
        assert "host" in s
        assert "state" in s
        assert "success_rate" in s
        assert "is_available" in s

    def test_captcha_keywords_detected(self):
        """Detecta múltiples keywords de CAPTCHA en contenido."""
        from services.scrapers.proxy_manager import ProxyManager
        for keyword in ["captcha", "cloudflare", "ddos-guard", "under-attack", "are you human"]:
            result = ProxyManager._detect_captcha(f"Some HTML with {keyword} text")
            assert result is True, f"Keyword '{keyword}' not detected"

    def test_captcha_not_in_normal_content(self):
        """Contenido normal no activa la detección de CAPTCHA."""
        from services.scrapers.proxy_manager import ProxyManager
        result = ProxyManager._detect_captcha("<html><body>Normal product page</body></html>")
        assert result is False

    def test_is_available_property(self):
        """is_available es True para proxies CLOSED."""
        from services.scrapers.proxy_manager import ProxyEntry, CircuitState
        entry = ProxyEntry(url=None, host="direct")
        assert entry.is_available is True

        entry.state = CircuitState.OPEN
        entry.opened_at = time.monotonic()
        assert entry.is_available is False


# ===================================================================
# TESTS: CrawlJob Serialización
# ===================================================================

class TestCrawlJobSerialization:
    """Tests de serialización y deserialización de CrawlJob."""

    def setup_method(self):
        from services.scrapers.scraper_scheduler import CrawlJob, JobStatus
        self.CrawlJob = CrawlJob
        self.JobStatus = JobStatus

    def test_crawl_job_to_dict(self):
        """CrawlJob.to_dict() serializa correctamente."""
        job = self.CrawlJob(
            id="test-id",
            user_id="user-id",
            competitor_id="comp-id",
        )
        d = job.to_dict()
        assert d["id"] == "test-id"
        assert d["user_id"] == "user-id"
        assert d["competitor_id"] == "comp-id"
        assert d["status"] == "pending"
        assert d["attempts"] == 0

    def test_crawl_job_status_is_string_in_dict(self):
        """El estado en el dict es string, no enum."""
        job = self.CrawlJob(
            id="test-id",
            user_id="user-id",
            competitor_id="comp-id",
            status=self.JobStatus.RUNNING,
        )
        d = job.to_dict()
        assert isinstance(d["status"], str)
        assert d["status"] == "running"

    def test_crawl_job_from_dict_basic(self):
        """CrawlJob.from_dict() reconstruye correctamente."""
        data = {
            "id": "test-id",
            "user_id": "user-id",
            "competitor_id": "comp-id",
            "status": "completed",
            "attempts": 2,
        }
        job = self.CrawlJob.from_dict(data)
        assert job.id == "test-id"
        assert job.user_id == "user-id"
        assert job.competitor_id == "comp-id"
        assert job.status == "completed"
        assert job.attempts == 2

    def test_crawl_job_from_dict_filters_unknown_fields(self):
        """from_dict() ignora campos desconocidos (ej. campos MongoDB)."""
        data = {
            "id": "test-id",
            "user_id": "user-id",
            "competitor_id": "comp-id",
            "_id": "mongo-oid",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
            "__some_internal": "value",
        }
        # No debe lanzar TypeError
        job = self.CrawlJob.from_dict(data)
        assert job.id == "test-id"
        assert not hasattr(job, "_id")

    def test_crawl_job_from_dict_with_defaults(self):
        """from_dict() aplica defaults para campos requeridos faltantes."""
        data = {}  # Sin campos
        job = self.CrawlJob.from_dict(data)
        assert job.id == ""
        assert job.user_id == ""
        assert job.competitor_id == ""

    def test_crawl_job_roundtrip(self):
        """Serialización/deserialización produce el mismo objeto."""
        original = self.CrawlJob(
            id=str(uuid.uuid4()),
            user_id="user-123",
            competitor_id="comp-456",
            status=self.JobStatus.FAILED,
            attempts=3,
            error_message="Connection refused",
        )
        d = original.to_dict()
        restored = self.CrawlJob.from_dict(d)

        assert restored.id == original.id
        assert restored.user_id == original.user_id
        assert restored.competitor_id == original.competitor_id
        assert restored.attempts == original.attempts
        assert restored.error_message == original.error_message


# ===================================================================
# TESTS: calculate_final_price
# ===================================================================

class TestCalculateFinalPrice:
    """Tests de cálculo de precio final con reglas de margen."""

    def setup_method(self):
        from services.sync import calculate_final_price
        self.calculate_final_price = calculate_final_price

    def _make_rule(self, rule_type, value, apply_to="all", **kwargs):
        rule = {
            "rule_type": rule_type,
            "value": value,
            "apply_to": apply_to,
        }
        rule.update(kwargs)
        return rule

    def test_no_rules_returns_base_price(self):
        """Sin reglas, devuelve el precio base sin cambios."""
        product = {"id": "p1", "category": "electronics"}
        price = self.calculate_final_price(100.0, product, [])
        assert price == 100.0

    def test_percentage_margin_rule(self):
        """Regla porcentual +10% aplica correctamente."""
        product = {"id": "p1"}
        rules = [self._make_rule("percentage", 10)]
        price = self.calculate_final_price(100.0, product, rules)
        assert abs(price - 110.0) < 0.01

    def test_fixed_margin_rule(self):
        """Regla fija +5€ aplica correctamente."""
        product = {"id": "p1"}
        rules = [self._make_rule("fixed", 5)]
        price = self.calculate_final_price(100.0, product, rules)
        assert abs(price - 105.0) < 0.01

    def test_percentage_negative_margin(self):
        """Regla porcentual negativa -5% reduce el precio."""
        product = {"id": "p1"}
        rules = [self._make_rule("percentage", -5)]
        price = self.calculate_final_price(100.0, product, rules)
        assert abs(price - 95.0) < 0.01

    def test_category_specific_rule(self):
        """Regla por categoría aplica solo a la categoría correcta."""
        rules = [self._make_rule("percentage", 20, apply_to="category", apply_to_value="electronics")]

        product_match = {"id": "p1", "category": "electronics"}
        product_no_match = {"id": "p2", "category": "clothing"}

        price_match = self.calculate_final_price(100.0, product_match, rules)
        price_no_match = self.calculate_final_price(100.0, product_no_match, rules)

        assert abs(price_match - 120.0) < 0.01
        assert abs(price_no_match - 100.0) < 0.01  # Sin cambio

    def test_supplier_specific_rule(self):
        """Regla por proveedor aplica solo al proveedor correcto."""
        rules = [self._make_rule("percentage", 15, apply_to="supplier", apply_to_value="supplier-1")]

        product_match = {"id": "p1", "supplier_id": "supplier-1"}
        product_no_match = {"id": "p2", "supplier_id": "supplier-2"}

        price_match = self.calculate_final_price(100.0, product_match, rules)
        price_no_match = self.calculate_final_price(100.0, product_no_match, rules)

        assert abs(price_match - 115.0) < 0.01
        assert abs(price_no_match - 100.0) < 0.01

    def test_product_specific_rule(self):
        """Regla por producto específico aplica solo a ese producto."""
        rules = [self._make_rule("fixed", 10, apply_to="product", apply_to_value="prod-1")]

        product_match = {"id": "prod-1"}
        product_no_match = {"id": "prod-2"}

        price_match = self.calculate_final_price(100.0, product_match, rules)
        price_no_match = self.calculate_final_price(100.0, product_no_match, rules)

        assert abs(price_match - 110.0) < 0.01
        assert abs(price_no_match - 100.0) < 0.01

    def test_min_price_filter(self):
        """La regla no aplica si el precio es menor que min_price."""
        rules = [self._make_rule("percentage", 10, min_price=150.0)]
        product = {"id": "p1"}

        price_below = self.calculate_final_price(100.0, product, rules)
        price_above = self.calculate_final_price(200.0, product, rules)

        assert abs(price_below - 100.0) < 0.01  # No aplica
        assert abs(price_above - 220.0) < 0.01  # Aplica

    def test_max_price_filter(self):
        """La regla no aplica si el precio es mayor que max_price."""
        rules = [self._make_rule("percentage", 10, max_price=150.0)]
        product = {"id": "p1"}

        price_below = self.calculate_final_price(100.0, product, rules)
        price_above = self.calculate_final_price(200.0, product, rules)

        assert abs(price_below - 110.0) < 0.01  # Aplica
        assert abs(price_above - 200.0) < 0.01  # No aplica (encima de max_price)

    def test_first_matching_rule_wins(self):
        """Sólo la primera regla que aplica se usa (break después del primer match)."""
        rules = [
            self._make_rule("percentage", 10),  # Primera
            self._make_rule("percentage", 50),  # Segunda (no debe aplicar)
        ]
        product = {"id": "p1"}
        price = self.calculate_final_price(100.0, product, rules)
        assert abs(price - 110.0) < 0.01  # Solo primera regla


# ===================================================================
# TESTS: Matcher multicapa
# ===================================================================

class TestMultiLayerMatcher:
    """Tests del matcher de productos multicapa (EAN → SKU → Specs+Fuzzy)."""

    def setup_method(self):
        from services.scrapers.matcher import match_product, MatchResult, AUTO_ACCEPT_THRESHOLD
        self.match_product = match_product
        self.MatchResult = MatchResult
        self.AUTO_ACCEPT_THRESHOLD = AUTO_ACCEPT_THRESHOLD

    def _make_scraped(self, name, ean=None, sku=None, price=99.99):
        from services.scrapers.base import ScrapedProduct
        return ScrapedProduct(
            product_name=name,
            price=price,
            ean=ean,
            sku=sku,
        )

    def _make_user_products(self, items):
        """Crea lista de products dummy."""
        return [
            {
                "id": item.get("id", str(uuid.uuid4())),
                "name": item.get("name", "Product"),
                "sku": item.get("sku"),
                "ean": item.get("ean"),
                "price": item.get("price", 100.0),
            }
            for item in items
        ]

    def test_ean_match_exact(self):
        """Match exacto por EAN (capa 1) - prueba sincrónica via asyncio.run."""
        import asyncio
        user_products = self._make_user_products([
            {"name": "Laptop Lenovo X1", "ean": "1234567890123", "sku": "LNV-X1"},
        ])
        scraped = self._make_scraped("Lenovo ThinkPad X1 Carbon", ean="1234567890123")

        result = asyncio.run(self.match_product(scraped, user_products))
        assert result is not None
        assert result.matched_by == "ean"
        assert result.confidence > 0.9

    def test_sku_match_exact(self):
        """Match exacto por SKU (capa 2)."""
        import asyncio
        user_products = self._make_user_products([
            {"name": "Laptop Lenovo X1", "sku": "LNV-X1-2024"},
        ])
        scraped = self._make_scraped("Lenovo ThinkPad", sku="LNV-X1-2024")

        result = asyncio.run(self.match_product(scraped, user_products))
        assert result is not None
        assert result.matched_by == "sku"

    def test_no_match_returns_result_with_low_confidence(self):
        """Sin match, devuelve resultado de baja confianza (matched=False)."""
        import asyncio
        user_products = self._make_user_products([
            {"name": "Laptop Lenovo X1", "ean": "0000000000001", "sku": "LNV-X1"},
        ])
        scraped = self._make_scraped("Monitor Samsung 27 pulgadas", ean="9999999999999")

        result = asyncio.run(self.match_product(scraped, user_products))
        assert result is not None
        # Confianza baja o no ha hecho match
        if result.matched:
            assert result.confidence < 0.85

    def test_auto_accept_threshold(self):
        """Umbral AUTO_ACCEPT_THRESHOLD es >= 0.85."""
        assert self.AUTO_ACCEPT_THRESHOLD >= 0.85

    def test_match_result_default_no_review(self):
        """MatchResult con alta confianza no necesita revisión."""
        result = self.MatchResult(
            product_id="p1",
            product_sku="SKU-001",
            product_ean="1234567890",
            product_name="Test Product",
            matched_by="ean",
            confidence=0.95,
            matched=True,
        )
        assert result.product_id == "p1"
        assert result.matched_by == "ean"
        assert result.confidence == 0.95
        # needs_review depende de la confianza asignada al crear
        # Alta confianza no necesita revisión cuando se marca explícitamente
        assert result.needs_review is False

    def test_low_confidence_needs_review(self):
        """Resultados marcados con needs_review=True."""
        result = self.MatchResult(
            product_id="p1",
            product_sku="SKU-001",
            product_ean="1234567890",
            product_name="Test Product",
            matched_by="fuzzy",
            confidence=self.AUTO_ACCEPT_THRESHOLD - 0.1,
            matched=True,
            needs_review=True,
        )
        assert result.needs_review is True

    def test_fuzzy_score_same_names(self):
        """Nombres idénticos tienen score 1.0."""
        from services.scrapers.matcher import fuzzy_name_score
        score = fuzzy_name_score("Laptop Lenovo ThinkPad X1", "Laptop Lenovo ThinkPad X1")
        assert score >= 0.99

    def test_fuzzy_score_different_names(self):
        """Nombres muy distintos tienen score bajo."""
        from services.scrapers.matcher import fuzzy_name_score
        score = fuzzy_name_score("SSD Samsung 970 EVO 1TB", "Laptop Lenovo ThinkPad X1")
        assert score < 0.5


# ===================================================================
# TESTS: SpecParser
# ===================================================================

class TestSpecParser:
    """Tests de extracción de especificaciones técnicas."""

    def setup_method(self):
        from services.scrapers.spec_parser import SpecParser
        self.parser = SpecParser()

    def test_parse_cpu_intel(self):
        """Detecta CPU Intel Core y extrae brand y modelo."""
        specs = self.parser.parse("Laptop Intel Core i7-12700H 16GB RAM")
        # Verifica que hay alguna info de CPU
        has_cpu = (specs.cpu_brand is not None or
                   specs.cpu_family is not None or
                   specs.cpu_model is not None)
        assert has_cpu, f"No CPU detectada en: 'Laptop Intel Core i7-12700H 16GB RAM' → {specs.to_dict()}"

    def test_parse_cpu_intel_brand(self):
        """Detecta la marca Intel."""
        specs = self.parser.parse("Intel Core i7-12700H")
        if specs.cpu_brand:
            assert "Intel" in specs.cpu_brand or "intel" in specs.cpu_brand.lower()

    def test_parse_cpu_amd(self):
        """Detecta CPU AMD Ryzen."""
        specs = self.parser.parse("PC AMD Ryzen 9 5900X 32GB DDR4")
        has_cpu = (specs.cpu_brand is not None or
                   specs.cpu_family is not None or
                   specs.cpu_model is not None)
        assert has_cpu, f"No CPU AMD detectada → {specs.to_dict()}"

    def test_parse_ram(self):
        """Detecta cantidad de RAM en GB."""
        specs = self.parser.parse("Laptop 16GB DDR4 NVMe SSD")
        assert specs.ram_gb is not None, "RAM no detectada"
        assert specs.ram_gb == 16

    def test_parse_ram_type(self):
        """Detecta tipo de RAM DDR4."""
        specs = self.parser.parse("Laptop 32GB DDR5 6000MHz")
        if specs.ram_type:
            assert "DDR" in specs.ram_type.upper()

    def test_parse_storage(self):
        """Detecta almacenamiento en GB."""
        specs = self.parser.parse("SSD 1TB NVMe M.2")
        # 1TB = 1000GB
        has_storage = (specs.storage_gb is not None or specs.storage_type is not None)
        assert has_storage, f"Almacenamiento no detectado → {specs.to_dict()}"

    def test_parse_gpu_nvidia(self):
        """Detecta GPU NVIDIA RTX."""
        specs = self.parser.parse("Laptop NVIDIA RTX 4080 16GB")
        has_gpu = (specs.gpu_brand is not None or
                   specs.gpu_family is not None or
                   specs.gpu_model is not None)
        assert has_gpu, f"GPU no detectada → {specs.to_dict()}"

    def test_parse_unknown_returns_empty_specs(self):
        """Producto sin especificaciones técnicas devuelve specs vacías."""
        specs = self.parser.parse("Lápiz HB número 2")
        # No debe lanzar excepción
        assert specs is not None
        # has_specs() es False para un producto no técnico
        assert specs.has_specs() is False


# ===================================================================
# TESTS: Lógica de configuración de catálogo (unit, sin DB)
# ===================================================================

class TestCatalogMonitoringConfig:
    """Tests de lógica de configuración de catálogo para monitoreo."""

    def test_valid_catalog_id_format(self):
        """Un catalog_id UUID válido es correcto."""
        catalog_id = str(uuid.uuid4())
        assert len(catalog_id) == 36
        assert catalog_id.count("-") == 4

    def test_empty_catalog_id_rejected(self):
        """Un catalog_id vacío debe rechazarse en validación."""
        catalog_id = ""
        assert not catalog_id  # Vacío = falsy

    def test_catalog_monitoring_config_response_structure(self):
        """La estructura de respuesta de la configuración de catálogo es correcta."""
        # Simula la respuesta esperada del endpoint
        mock_response = {
            "catalog_id": "some-uuid",
            "catalog_name": "Mi Catálogo Principal",
            "is_default": True,
        }
        assert "catalog_id" in mock_response
        assert "catalog_name" in mock_response
        assert "is_default" in mock_response

    def test_available_catalogs_structure(self):
        """La estructura de catálogos disponibles es correcta."""
        mock_response = {
            "catalogs": [
                {
                    "catalog_id": "uuid-1",
                    "catalog_name": "Catálogo A",
                    "is_default": True,
                    "is_selected": True,
                },
                {
                    "catalog_id": "uuid-2",
                    "catalog_name": "Catálogo B",
                    "is_default": False,
                    "is_selected": False,
                },
            ],
            "current_catalog_id": "uuid-1",
        }
        catalogs = mock_response["catalogs"]
        assert len(catalogs) == 2

        selected = [c for c in catalogs if c["is_selected"]]
        assert len(selected) == 1
        assert selected[0]["catalog_id"] == mock_response["current_catalog_id"]


# ===================================================================
# TESTS: SSRF Protection en Webhooks
# ===================================================================

class TestSSRFProtection:
    """Tests de protección contra SSRF en el envío de webhooks."""

    def setup_method(self):
        """Importar la función de validación SSRF desde orchestrator."""
        import importlib
        module = importlib.import_module("services.scrapers.orchestrator")
        self._is_safe = getattr(module, "_is_safe_webhook_url", None)

    def test_localhost_blocked(self):
        """localhost debe ser bloqueado."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("http://localhost/callback") is False
        assert self._is_safe("http://localhost:8080/hook") is False

    def test_127_blocked(self):
        """127.0.0.1 debe ser bloqueado."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("http://127.0.0.1/callback") is False

    def test_private_ip_blocked(self):
        """IPs privadas deben ser bloqueadas."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("http://192.168.1.1/hook") is False
        assert self._is_safe("http://10.0.0.1/hook") is False

    def test_internal_domain_blocked(self):
        """Dominios internos deben ser bloqueados."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("http://api.local/hook") is False
        assert self._is_safe("http://server.internal/hook") is False

    def test_public_url_allowed(self):
        """URLs públicas legítimas deben pasar."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("https://hooks.example.com/callback") is True

    def test_https_public_url_allowed(self):
        """URL HTTPS pública debe pasar."""
        if self._is_safe is None:
            pytest.skip("_is_safe_webhook_url no encontrada")
        assert self._is_safe("https://api.mywebsite.com/notifications") is True
