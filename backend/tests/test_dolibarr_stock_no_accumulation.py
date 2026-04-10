"""
Tests unitarios para verificar que la sincronización de stock con Dolibarr
REEMPLAZA el stock en lugar de SUMARLO.

Regla de oro: stockDolibarr === stockSyncStock SIEMPRE después de una sincronización.

Escenario que este test previene:
  SyncStock:  100 unidades
  Dolibarr:    50 unidades (stock actual)
  Después de sincronizar: debe ser 100, NO 150.
"""
import unittest
from unittest.mock import MagicMock, patch, call


def _make_response(status_code: int, json_data=None, text: str = ""):
    """Crea un mock de respuesta HTTP."""
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.text = text
    return r


class TestDolibarrStockNoAccumulation(unittest.TestCase):
    """
    Valida que update_stock() REEMPLAZA el stock, nunca lo suma.
    Todos los tests usan mocks de la API de Dolibarr.
    """

    def _make_client(self):
        """
        Instancia DolibarrClient con dependencias mockeadas para poder
        probar update_stock() sin conexión real.
        """
        from backend.services.crm_clients.dolibarr import DolibarrClient
        client = DolibarrClient.__new__(DolibarrClient)
        client.base_url = "http://fake-dolibarr/api/index.php"
        client.api_key = "fake-key"
        client._rate_limiter = MagicMock()
        return client

    # ------------------------------------------------------------------
    # CASO 1: El path normal (warehouse encontrado en endpoint específico)
    # ------------------------------------------------------------------

    def test_reemplaza_stock_cuando_warehouse_encontrado(self):
        """
        Escenario: Dolibarr tiene 50 unidades (warehouse encontrado directamente).
        Resultado esperado: Dolibarr queda con 100, NO 150.
        """
        client = self._make_client()

        # _get_warehouse_stock devuelve 50 (stock actual confirmado)
        # La verificación final devuelve 100 (después de reset+set)
        client._get_warehouse_stock = MagicMock(side_effect=[50, 100])
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Movimiento de eliminación → éxito
        remove_resp = _make_response(200)
        # Movimiento de adición → éxito
        add_resp = _make_response(200)

        call_sequence = [remove_resp, add_resp]

        with patch.object(client, '_rate_limited_request', side_effect=call_sequence) as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success",
                         f"Esperado 'success', obtenido: {result}")

        # Verificar que se ejecutó la eliminación (type=1) y la adición (type=0)
        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 2, "Deben hacerse exactamente 2 llamadas: remove + add")

        remove_call = calls[0]
        self.assertEqual(remove_call[0][0], 'POST')
        self.assertIn('stockmovements', remove_call[0][1])
        self.assertEqual(remove_call[1]['json']['qty'], 50)   # eliminar 50
        self.assertEqual(remove_call[1]['json']['type'], 1)   # type=1 = salida

        add_call = calls[1]
        self.assertEqual(add_call[1]['json']['qty'], 100)     # añadir 100
        self.assertEqual(add_call[1]['json']['type'], 0)      # type=0 = entrada

    def test_no_suma_multiples_sincronizaciones(self):
        """
        Escenario: se sincronizan 3 valores distintos en secuencia.
        Cada vez el resultado debe ser EXACTAMENTE el valor de SyncStock.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Secuencia: stock inicial=0 → sync 50 → sync 75 → sync 30
        # _get_warehouse_stock: lectura inicial, verificación, lectura inicial, verificación, ...
        client._get_warehouse_stock = MagicMock(side_effect=[
            0,   # lectura antes de sync #1 (stock inicial 0)
            50,  # verificación tras sync #1
            50,  # lectura antes de sync #2
            75,  # verificación tras sync #2
            75,  # lectura antes de sync #3
            30,  # verificación tras sync #3
        ])

        ok = _make_response(200)

        with patch.object(client, '_rate_limited_request', return_value=ok):
            r1 = client.update_stock(42, 50, warehouse_id=1)
            r2 = client.update_stock(42, 75, warehouse_id=1)
            r3 = client.update_stock(42, 30, warehouse_id=1)

        self.assertEqual(r1["status"], "success")
        self.assertEqual(r2["status"], "success")
        self.assertEqual(r3["status"], "success")

    # ------------------------------------------------------------------
    # CASO 2: Fallback a stock_reel cuando warehouse endpoint falla
    # ------------------------------------------------------------------

    def test_fallback_stock_reel_positivo_hace_remove_antes_de_add(self):
        """
        Escenario: _get_warehouse_stock devuelve None, pero stock_reel=50.
        Resultado esperado: se elimina 50, luego se añaden 100 → total 100.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Primera llamada (antes del update) → None (endpoint fallback)
        # Segunda llamada (verificación post-update) → 100
        client._get_warehouse_stock = MagicMock(side_effect=[None, 100])
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "50"})

        remove_resp = _make_response(200)
        add_resp = _make_response(200)

        with patch.object(client, '_rate_limited_request', side_effect=[remove_resp, add_resp]) as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success")

        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 2)
        # Debe eliminar los 50 del fallback
        self.assertEqual(calls[0][1]['json']['qty'], 50)
        self.assertEqual(calls[0][1]['json']['type'], 1)
        # Luego añadir 100
        self.assertEqual(calls[1][1]['json']['qty'], 100)
        self.assertEqual(calls[1][1]['json']['type'], 0)

    def test_fallback_stock_reel_cero_omite_update_sin_acumular(self):
        """
        BUG PRINCIPAL: Cuando _get_warehouse_stock=None y stock_reel="0" (stale),
        el código ANTES saltaba la eliminación y sumaba el nuevo stock encima
        del existente (ej: 50 existente + 100 nuevo = 150).

        Con la corrección, debe OMITIR el update y devolver warning,
        evitando acumulación cuando no podemos determinar el stock actual.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Warehouse-specific endpoint falla → None
        client._get_warehouse_stock = MagicMock(return_value=None)
        # stock_reel reporta "0" (valor obsoleto/stale)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "0"})

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        # DEBE devolver warning, NO success
        self.assertEqual(result["status"], "warning",
                         f"Con stock_reel=0 en fallback debe devolver 'warning', obtenido: {result}")

        # NUNCA debe llamar a la API de stockmovements (ni eliminar ni añadir)
        mock_req.assert_not_called()

    def test_fallback_stock_reel_entero_cero_omite_update(self):
        """
        Variante: stock_reel viene como entero 0 (no string).
        Mismo comportamiento: debe omitir para evitar acumulación.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client._get_warehouse_stock = MagicMock(return_value=None)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": 0})

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "warning")
        mock_req.assert_not_called()

    def test_fallback_stock_reel_none_omite_update(self):
        """stock_reel=None debe omitir el update (ya existía, verificar que sigue funcionando)."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client._get_warehouse_stock = MagicMock(return_value=None)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": None})

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "warning")
        mock_req.assert_not_called()

    # ------------------------------------------------------------------
    # CASO 3: Auto-corrección post-update (STEP 3)
    # ------------------------------------------------------------------

    def test_autocorreccion_elimina_exceso_detectado(self):
        """
        Escenario: A pesar de la sincronización, la verificación detecta 150
        cuando se esperaba 100 (acumulación residual).
        El STEP 3 debe auto-corregir eliminando el exceso de 50.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Lectura inicial=0, verificación post-update detecta 150 (acumulación)
        client._get_warehouse_stock = MagicMock(side_effect=[0, 150])

        remove_resp = _make_response(200)   # No se usa (current_stock=0)
        add_resp = _make_response(200)      # Añadir 100
        corrective_resp = _make_response(200)  # Corrección: eliminar 50

        with patch.object(client, '_rate_limited_request',
                          side_effect=[add_resp, corrective_resp]) as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success",
                         f"Con auto-corrección exitosa debe devolver 'success': {result}")

        calls = mock_req.call_args_list
        # Llamada 1: añadir 100
        self.assertEqual(calls[0][1]['json']['qty'], 100)
        self.assertEqual(calls[0][1]['json']['type'], 0)
        # Llamada 2: corrección, eliminar exceso de 50
        self.assertEqual(calls[1][1]['json']['qty'], 50)   # 150 - 100 = 50 de exceso
        self.assertEqual(calls[1][1]['json']['type'], 1)   # type=1 = salida

    # ------------------------------------------------------------------
    # CASO 4: Edge cases
    # ------------------------------------------------------------------

    def test_stock_cero_en_syncstock_elimina_todo_en_dolibarr(self):
        """
        Si SyncStock tiene 0 unidades, Dolibarr debe quedar en 0 también.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # Dolibarr tiene 80, queremos dejarlo en 0
        client._get_warehouse_stock = MagicMock(side_effect=[80, 0])

        remove_resp = _make_response(200)

        with patch.object(client, '_rate_limited_request', return_value=remove_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=0, warehouse_id=1)

        self.assertEqual(result["status"], "success")

        calls = mock_req.call_args_list
        # Solo debe hacer 1 llamada: eliminar los 80
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['json']['qty'], 80)
        self.assertEqual(calls[0][1]['json']['type'], 1)

    def test_stock_negativo_es_rechazado(self):
        """Stock negativo debe devolver error sin llamar a la API."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=-5, warehouse_id=1)

        self.assertEqual(result["status"], "error")
        mock_req.assert_not_called()

    def test_warehouse_no_disponible_devuelve_warning(self):
        """Si no hay almacén disponible, debe devolver warning sin intentar update."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=None)

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100)

        self.assertEqual(result["status"], "warning")
        mock_req.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
