"""
Tests de seguridad — Sprint 5
Verifica el guard de race condition en el endpoint POST /suppliers/{id}/sync.
Usa FastAPI TestClient con mocks para no requerir MongoDB real.
"""
import os
import sys
from unittest.mock import AsyncMock, patch

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
# Fixtures
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
# Tests de race condition guard
# ---------------------------------------------------------------------------

class TestRaceConditionGuard:
    """Verifica que sync_supplier_manual rechaza con 409 si sync_status='running'."""

    def test_sync_returns_409_when_already_running(self):
        """
        Si el proveedor ya tiene sync_status='running', el endpoint debe
        responder HTTP 409 Conflict sin escribir en MongoDB ni lanzar background tasks.
        """
        supplier_running = _make_supplier(sync_status="running")

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_running), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock) as mock_update:

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
        mock_update.assert_not_called()

    def test_sync_proceeds_when_idle(self):
        """
        Si sync_status es 'idle', el endpoint debe responder HTTP 200 'queued'
        y marcar sync_status como 'running' en MongoDB.
        """
        supplier_idle = _make_supplier(sync_status="idle")

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_idle), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock) as mock_update, \
             patch("routes.suppliers.sync_supplier", new_callable=AsyncMock, return_value={"status": "success", "message": "OK"}):

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 200, (
            f"Se esperaba HTTP 200, se obtuvo {response.status_code}. Body: {response.text}"
        )
        body = response.json()
        assert body.get("status") == "queued"

        # Debe haber llamado update_by_id para marcar como running
        assert mock_update.call_count >= 1
        first_call_data = mock_update.call_args_list[0][0][1]
        assert first_call_data.get("sync_status") == "running"

    def test_sync_proceeds_when_status_is_none(self):
        """
        Si sync_status es None (proveedor sin historial), debe proceder sin
        lanzar 409.
        """
        supplier_no_status = _make_supplier(sync_status=None)

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_no_status), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock) as mock_update, \
             patch("routes.suppliers.sync_supplier", new_callable=AsyncMock, return_value={"status": "success", "message": "OK"}):

            app = _build_test_app()
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/suppliers/test-supplier-id-123/sync")

        assert response.status_code == 200, (
            f"Se esperaba HTTP 200, se obtuvo {response.status_code}. Body: {response.text}"
        )
        assert mock_update.call_count >= 1

    def test_409_status_code_is_exactly_conflict(self):
        """
        El código de estado debe ser exactamente 409 (Conflict), no 400, 403 ni 500.
        """
        supplier_running = _make_supplier(sync_status="running")

        with patch("repositories.SupplierRepository.get_by_id", new_callable=AsyncMock, return_value=supplier_running), \
             patch("repositories.SupplierRepository.update_by_id", new_callable=AsyncMock):

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
