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
