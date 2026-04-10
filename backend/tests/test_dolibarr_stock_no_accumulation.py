"""
Tests unitarios para verificar que la sincronización de stock con Dolibarr
REEMPLAZA el stock en lugar de SUMARLO.

Regla de oro: stockDolibarr === stockSyncStock SIEMPRE después de una sincronización.

Escenario que este test previene:
  SyncStock:  50 unidades
  Dolibarr:   30 unidades (stock_reel=30)
  Después de sincronizar: debe ser 50, NO 80.

Estrategia (enfoque delta):
  delta = desired - stock_reel
  delta > 0 → entrada (type=3, qty=delta)
  delta < 0 → salida  (type=2, qty=delta negativo)
  delta = 0 → sin cambio, no se llama a la API
"""
import unittest
from unittest.mock import MagicMock, patch


def _make_response(status_code: int, json_data=None, text: str = ""):
    """Crea un mock de respuesta HTTP."""
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.text = text
    return r


class TestDolibarrStockNoAccumulation(unittest.TestCase):
    """
    Valida que update_stock() REEMPLAZA el stock usando enfoque delta,
    nunca suma al stock existente.
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
    # CASO 1: Delta positivo (Dolibarr tiene menos que el deseado)
    # ------------------------------------------------------------------

    def test_delta_positivo_envia_entrada(self):
        """
        Escenario del bug: Dolibarr tiene 30 (stock_reel=30), queremos 50.
        Delta = 50 - 30 = +20 → entrada (type=3, qty=20).
        Resultado esperado: Dolibarr queda con 50, NO 80.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "30"})

        ok_resp = _make_response(200)

        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=50, warehouse_id=1)

        self.assertEqual(result["status"], "success", f"Esperado 'success', obtenido: {result}")

        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 1, "Enfoque delta: exactamente 1 llamada a stockmovements")

        payload = calls[0][1]['json']
        self.assertIn('stockmovements', calls[0][0][1])
        self.assertEqual(payload['qty'], 20)         # delta = 50 - 30 = +20
        self.assertEqual(payload['type'], 3)          # type=3 = entrada
        self.assertEqual(payload['product_id'], 42)
        self.assertEqual(payload['warehouse_id'], 1)

    def test_delta_negativo_envia_salida(self):
        """
        Escenario: Dolibarr tiene 80 (stock_reel=80), queremos 30.
        Delta = 30 - 80 = -50 → salida (type=2, qty=-50).
        Resultado esperado: Dolibarr queda con 30, NO 110.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "80"})

        ok_resp = _make_response(200)

        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=30, warehouse_id=1)

        self.assertEqual(result["status"], "success")

        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 1)
        payload = calls[0][1]['json']
        self.assertEqual(payload['qty'], -50)         # delta = 30 - 80 = -50
        self.assertEqual(payload['type'], 2)          # type=2 = salida

    def test_no_suma_multiples_sincronizaciones(self):
        """
        Escenario: se sincronizan 3 valores distintos en secuencia.
        Cada vez el resultado debe ser EXACTAMENTE el valor de SyncStock.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)

        # stock_reel simula el estado de Dolibarr tras cada sync
        client.get_product_by_id = MagicMock(side_effect=[
            {"stock_reel": "0"},   # sync #1: stock inicial 0
            {"stock_reel": "50"},  # sync #2: Dolibarr ya tiene 50
            {"stock_reel": "75"},  # sync #3: Dolibarr ya tiene 75
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
    # CASO 2: Delta = 0 (sin cambio necesario)
    # ------------------------------------------------------------------

    def test_delta_cero_no_llama_a_api(self):
        """
        Si el stock de SyncStock coincide con stock_reel de Dolibarr,
        no se debe hacer ninguna llamada a la API (delta=0).
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "100"})

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success")
        mock_req.assert_not_called()

    # ------------------------------------------------------------------
    # CASO 3: stock_reel ausente o nulo — asume 0
    # ------------------------------------------------------------------

    def test_stock_reel_nulo_asume_cero_y_envia_delta_completo(self):
        """
        Si stock_reel es None, se asume stock_actual=0.
        Delta = desired - 0 = desired → entrada completa.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": None})

        ok_resp = _make_response(200)
        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success")
        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['json']['qty'], 100)   # delta = 100 - 0 = 100
        self.assertEqual(calls[0][1]['json']['type'], 3)

    def test_stock_reel_cero_envia_delta_completo(self):
        """
        Si stock_reel es "0", delta = desired → entrada completa.
        Con el enfoque delta, stock_reel=0 es un valor válido (no ambiguo).
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "0"})

        ok_resp = _make_response(200)
        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "success")
        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['json']['qty'], 100)   # delta = 100 - 0 = 100
        self.assertEqual(calls[0][1]['json']['type'], 3)

    def test_stock_reel_string_vacio_asume_cero(self):
        """stock_reel='' debe tratarse como 0."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": ""})

        ok_resp = _make_response(200)
        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=50, warehouse_id=1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_req.call_args_list[0][1]['json']['qty'], 50)
        self.assertEqual(mock_req.call_args_list[0][1]['json']['type'], 3)

    # ------------------------------------------------------------------
    # CASO 4: Campos del payload correctos
    # ------------------------------------------------------------------

    def test_payload_usa_movementcode_y_movementlabel(self):
        """
        El payload debe incluir movementcode y movementlabel (no 'label').
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "10"})

        ok_resp = _make_response(200)
        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            client.update_stock(product_id=42, stock=60, warehouse_id=1)

        payload = mock_req.call_args_list[0][1]['json']
        self.assertIn('movementcode', payload)
        self.assertIn('movementlabel', payload)
        self.assertNotIn('label', payload)
        self.assertEqual(payload['movementcode'], 'SYNCSTOCK')

    # ------------------------------------------------------------------
    # CASO 5: Edge cases
    # ------------------------------------------------------------------

    def test_stock_cero_en_syncstock_elimina_todo_en_dolibarr(self):
        """
        Si SyncStock tiene 0 y Dolibarr tiene 80, delta=-80 → salida completa.
        """
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "80"})

        ok_resp = _make_response(200)
        with patch.object(client, '_rate_limited_request', return_value=ok_resp) as mock_req:
            result = client.update_stock(product_id=42, stock=0, warehouse_id=1)

        self.assertEqual(result["status"], "success")
        calls = mock_req.call_args_list
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]['json']['qty'], -80)   # delta = 0 - 80 = -80
        self.assertEqual(calls[0][1]['json']['type'], 2)    # type=2 = salida

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

    def test_producto_no_encontrado_devuelve_error(self):
        """Si el producto no existe en Dolibarr, debe devolver error sin llamar a stockmovements."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value=None)

        with patch.object(client, '_rate_limited_request') as mock_req:
            result = client.update_stock(product_id=42, stock=100, warehouse_id=1)

        self.assertEqual(result["status"], "error")
        mock_req.assert_not_called()

    def test_error_api_devuelve_error(self):
        """Si la API de Dolibarr devuelve error HTTP, debe retornar status=error."""
        client = self._make_client()
        client.get_or_create_default_warehouse = MagicMock(return_value=1)
        client.get_product_by_id = MagicMock(return_value={"stock_reel": "30"})

        error_resp = _make_response(500, text="Internal Server Error")
        with patch.object(client, '_rate_limited_request', return_value=error_resp):
            result = client.update_stock(product_id=42, stock=50, warehouse_id=1)

        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main(verbosity=2)
