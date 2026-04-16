"""
Tests de seguridad — Sprint 5
Verifica el guard de race condition atómico en el endpoint POST /suppliers/{id}/sync.

El guard usa db.suppliers.update_one con filtro condicional ($ne:"running") y verifica
matched_count para detectar colisiones de forma atómica, eliminando la ventana de
race condition del patrón check-then-set anterior.
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Configurar path y variables de entorno antes de importar módulos del proyecto
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Proveer FERNET_KEY válida para que encryption.py no falle al importar
from cryptography.fernet import Fernet as _Fernet
os.environ.setdefault("FERNET_KEY", _Fernet.generate_key().decode())

# Ahora es seguro importar módulos del proyecto
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_supplier(sync_status=None) -> dict:
    """Construye un dict de proveedor de prueba."""
    return {
        "id": "test-supplier-id-123",
        "name": "Proveedor Test",
        "user_id": "user-id-abc",
        "connection_type": "ftp",
        "ftp_host": "ftp.example.com",
        "ftp_path": "/catalogo.csv",
        "ftp_password": None,
        "url_password": None,
        "ftp_paths": [],
        "sync_status": sync_status,
    }


def _make_update_result(matched_count: int):
    """Crea un objeto UpdateResult simulado con el matched_count indicado."""
    result = MagicMock()
    result.matched_count = matched_count
    return result


def _build_test_app():
    """
    Construye una aplicación FastAPI mínima con el router de proveedores
    y las dependencias de auth sobreescritas para no necesitar JWT real.
    """
    from routes.suppliers import router as suppliers_router
    from services.auth import get_current_user

    app = FastAPI()

    # Registrar el rate limiter en la app (necesario para SlowAPI)
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Override de auth: siempre devuelve usuario de prueba
    async def _mock_user():
        return {"id": "user-id-abc", "role": "user", "plan": "pro"}

    app.dependency_overrides[get_current_user] = _mock_user
    app.include_router(suppliers_router)

    return app


# ---------------------------------------------------------------------------
# Tests de race condition guard (operación atómica con update_one condicional)
# ---------------------------------------------------------------------------

class TestRaceConditionGuard:
    """
    Verifica que sync_supplier_manual rechaza con 409 cuando matched_count == 0
    (el proveedor ya estaba en estado 'running' en MongoDB).

    La operación atómica usa db.suppliers.update_one con filtro
    {$or: [{sync_status: {$ne: "running"}}, {sync_status: {$exists: false}}]}
    y verifica matched_count para detectar colisiones sin ventana de race condition.
    """

    def test_sync_returns_409_when_already_running(self):
        """
        Si MongoDB rechaza el update (matched_count==0) porque el proveedor ya
        estaba en 'running', el endpoint debe responder HTTP 409 Conflict.
        """
        supplier_running = _make_supplier(sync_status="running")
        # matched_count=0 simula que el filtro $ne:"running" no encontró documento
        atomic_result = _make_update_result(matched_count=0)

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_running), \
             patch("routes.suppliers.db") as mock_db:

            mock_db.suppliers.update_one = AsyncMock(return_value=atomic_result)

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 409, (
            f"Se esperaba HTTP 409, se obtuvo {response.status_code}. Body: {response.text}"
        )
        body = response.json()
        assert "progreso" in body.get("detail", "").lower(), (
            f"El mensaje de error no menciona 'progreso': {body.get('detail')}"
        )

    def test_sync_proceeds_when_idle(self):
        """
        Si MongoDB acepta el update (matched_count==1), el endpoint debe
        responder HTTP 200 'queued'.
        """
        supplier_idle = _make_supplier(sync_status="idle")
        # matched_count=1 simula que el filtro encontró el documento (no estaba running)
        atomic_result = _make_update_result(matched_count=1)

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_idle), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock), \
             patch("routes.suppliers.db") as mock_db, \
             patch("routes.suppliers.sync_supplier", new_callable=AsyncMock, return_value={"status": "success", "message": "OK"}):

            mock_db.suppliers.update_one = AsyncMock(return_value=atomic_result)

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 200, (
            f"Se esperaba HTTP 200, se obtuvo {response.status_code}. Body: {response.text}"
        )
        body = response.json()
        assert body.get("status") == "queued"

        # La operación atómica debe haberse llamado con el filtro condicional
        mock_db.suppliers.update_one.assert_called_once()
        call_filter = mock_db.suppliers.update_one.call_args[0][0]
        assert call_filter.get("id") == "test-supplier-id-123"
        assert "$or" in call_filter  # filtro condicional atómico presente

    def test_sync_proceeds_when_status_is_none(self):
        """
        Si sync_status es None (proveedor sin historial), MongoDB debe aceptar
        el update (matched_count==1) y el endpoint debe proceder sin lanzar 409.
        """
        supplier_no_status = _make_supplier(sync_status=None)
        atomic_result = _make_update_result(matched_count=1)

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_no_status), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock), \
             patch("routes.suppliers.db") as mock_db, \
             patch("routes.suppliers.sync_supplier", new_callable=AsyncMock, return_value={"status": "success", "message": "OK"}):

            mock_db.suppliers.update_one = AsyncMock(return_value=atomic_result)

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 200, (
            f"Se esperaba HTTP 200, se obtuvo {response.status_code}. Body: {response.text}"
        )

    def test_409_status_code_is_exactly_conflict(self):
        """
        El código de estado debe ser exactamente 409 (Conflict), no 400, 403 ni 500.
        """
        supplier_running = _make_supplier(sync_status="running")
        atomic_result = _make_update_result(matched_count=0)

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_running), \
             patch("routes.suppliers.db") as mock_db:

            mock_db.suppliers.update_one = AsyncMock(return_value=atomic_result)

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 409
        assert response.status_code not in (400, 403, 500)

    def test_sync_not_found_returns_404(self):
        """
        Si el proveedor no existe, debe retornar 404 (comportamiento existente preservado).
        """
        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=None):

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/nonexistent-supplier/sync")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests de límite de descarga 500 MB (Task 2)
# ---------------------------------------------------------------------------

class TestDownloadSizeLimit:
    """Task 2: Límite de tamaño de descarga."""

    def test_archivo_rechazado_via_content_length(self):
        """Content-Length mayor al límite debe lanzar ValueError."""
        from services.sync.downloaders import download_file_from_url_sync
        from unittest.mock import patch, MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": str(600 * 1024 * 1024)}  # 600 MB
        mock_response.raise_for_status = MagicMock()

        with patch("services.sync.downloaders._validate_url_ssrf"):
            with patch("services.sync.downloaders._build_browser_session") as mock_session:
                mock_session.return_value.get.return_value = mock_response
                with pytest.raises(ValueError, match="grande|límite"):
                    download_file_from_url_sync("http://example.com/file.csv")

    def test_archivo_rechazado_durante_streaming(self):
        """Archivo que supera el límite durante streaming debe lanzar ValueError."""
        from services.sync.downloaders import download_file_from_url_sync
        from unittest.mock import patch, MagicMock

        # Dos chunks: el segundo supera el límite
        chunk_300mb = b"x" * (300 * 1024 * 1024)

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = iter([chunk_300mb, chunk_300mb])

        with patch("services.sync.downloaders._validate_url_ssrf"):
            with patch("services.sync.downloaders._build_browser_session") as mock_session:
                mock_session.return_value.get.return_value = mock_response
                with pytest.raises(ValueError, match="límite"):
                    download_file_from_url_sync("http://example.com/file.csv")

    def test_archivo_pequeno_descargado_correctamente(self):
        """Archivo de 10 KB debe descargarse correctamente."""
        from services.sync.downloaders import download_file_from_url_sync
        from unittest.mock import patch, MagicMock

        data = b"col1,col2\nval1,val2\n"

        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": str(len(data))}
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = iter([data])

        with patch("services.sync.downloaders._validate_url_ssrf"):
            with patch("services.sync.downloaders._build_browser_session") as mock_session:
                mock_session.return_value.get.return_value = mock_response
                result = download_file_from_url_sync("http://example.com/file.csv")
                assert result == data


# ---------------------------------------------------------------------------
# Tests de upsert duplicado en product_sync (Task 3)
# ---------------------------------------------------------------------------

class TestUpsertDuplicado:
    """Task 3: Fix upsert duplicado en product_sync."""

    def test_no_hay_patron_doble_upsert_en_codigo_fuente(self):
        """Verificar que el código fuente no tiene el patrón doble UpdateOne para productos existentes."""
        import os
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "services", "sync", "product_sync.py"
        )
        with open(filepath) as f:
            source = f.read()

        # El patrón problemático era dos UpdateOne con "id": {"$ne": existing.id}
        # Este filtro solo tenía sentido en el patrón duplicado
        assert '{"$ne": existing.id}' not in source, \
            "Patrón de upsert duplicado todavía presente: {'$ne': existing.id}"

    def test_producto_existente_usa_filtro_por_id_unico(self):
        """El bloque if existing debe usar {"id": existing.id} como filtro, sin upsert."""
        import os
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "services", "sync", "product_sync.py"
        )
        with open(filepath) as f:
            source = f.read()

        # Verificar que existe el patrón correcto: filtro solo por id único del documento
        assert '"id": existing.id' in source or "{'id': existing.id}" in source, \
            "No se encontró el filtro correcto {'id': existing.id} para productos existentes"

    def test_bloque_existente_no_usa_setoninsert(self):
        """Con upsert=False, $setOnInsert nunca se ejecuta — no debe estar en el bloque if existing."""
        import os
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "services", "sync", "product_sync.py"
        )
        with open(filepath) as f:
            source = f.read()

        # Encontrar la sección del bloque if existing (antes del else)
        # Buscamos que $setOnInsert no aparezca junto a upsert=False en el bloque existing
        # El else sí puede tener $setOnInsert con upsert=True (productos nuevos)
        lines = source.splitlines()
        in_existing_block = False
        found_else = False
        existing_has_setoninsert = False

        for line in lines:
            stripped = line.strip()
            if "if existing:" in stripped:
                in_existing_block = True
                found_else = False
                continue
            if in_existing_block and stripped.startswith("else:"):
                found_else = True
                in_existing_block = False
                continue
            if in_existing_block and not found_else:
                if "$setOnInsert" in stripped:
                    existing_has_setoninsert = True

        assert not existing_has_setoninsert, \
            "$setOnInsert no debería estar en el bloque 'if existing:' (es inútil con upsert=False)"


# ---------------------------------------------------------------------------
# Tests de límite de archivos en ZIP (Task 4)
# ---------------------------------------------------------------------------

class TestZipFileLimit:
    """Task 4: Límite de archivos en ZIP."""

    def _create_zip_with_n_files(self, n: int) -> bytes:
        """Crea un ZIP con n archivos CSV de prueba."""
        import io
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(n):
                zf.writestr(f"file_{i}.csv", f"col1,col2\nval{i},val{i}")
        return buf.getvalue()

    def test_zip_con_muchos_archivos_lanza_valueerror(self):
        """ZIP con más de 100 archivos debe lanzar ValueError."""
        from services.sync.parsers import extract_zip_files
        big_zip = self._create_zip_with_n_files(150)
        with pytest.raises(ValueError, match="archivos|demasiados"):
            extract_zip_files(big_zip)

    def test_zip_con_pocos_archivos_funciona(self):
        """ZIP con 5 archivos debe extraerse correctamente."""
        from services.sync.parsers import extract_zip_files
        small_zip = self._create_zip_with_n_files(5)
        result = extract_zip_files(small_zip)
        assert len(result) == 5

    def test_zip_exactamente_en_limite_es_aceptado(self):
        """ZIP con exactamente 100 archivos debe ser aceptado."""
        from services.sync.parsers import extract_zip_files
        zip_at_limit = self._create_zip_with_n_files(100)
        result = extract_zip_files(zip_at_limit)
        assert len(result) == 100


# ---------------------------------------------------------------------------
# Tests de bloqueo explícito de localhost en validación SSRF (Task 5)
# ---------------------------------------------------------------------------

class TestSSRFLocalhost:
    """Task 5: Bloqueo explícito de localhost en validación SSRF."""

    def test_localhost_bloqueado_sin_resolver_dns(self):
        """'localhost' debe bloquearse por nombre antes de resolución DNS."""
        from services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError, match="localhost|interna|bloqueado"):
            _validate_url_ssrf("http://localhost/admin")

    def test_localhost_con_puerto_bloqueado(self):
        """'localhost:8080' debe bloquearse."""
        from services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError, match="localhost|interna|bloqueado"):
            _validate_url_ssrf("http://localhost:8080/api")

    def test_127_0_0_1_sigue_bloqueado(self):
        """127.0.0.1 debe seguir bloqueado (is_loopback ya lo cubre)."""
        from services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError):
            _validate_url_ssrf("http://127.0.0.1/secret")
