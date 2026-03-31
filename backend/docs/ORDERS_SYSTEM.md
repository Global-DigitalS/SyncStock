# Sistema de Pedidos Entre Plataformas

## Resumen

SyncStock ahora soporta recibir pedidos de múltiples tiendas online (WooCommerce, Shopify, PrestaShop) y sincronizarlos automáticamente con el CRM configurado (Dolibarr, Odoo, etc.).

## Arquitectura

```
Tienda Online (WooCommerce, Shopify, PrestaShop)
    ↓ POST /api/webhooks/receive/{config_id}
Webhook Receiver (webhooks.py)
    ↓ Validación de firma
process_order_event()
    ↓
process_order_webhook() [services/orders/order_service.py]
    ├─ Normalización (normalizer.py)
    ├─ Validación de duplicados
    ├─ Enriquecimiento (productos, stock)
    ├─ Sincronización con CRM
    └─ Guardado en MongoDB
    ↓
CRM Configurado (Dolibarr, Odoo, etc.)
    ↓
MongoDB (orders collection)
```

## Flujo de un Pedido

### 1. Recepción del Webhook
- El endpoint `/api/webhooks/receive/{config_id}` recibe POST de la tienda online
- Se valida la firma según la plataforma:
  - WooCommerce: X-WC-Webhook-Signature (HMAC-SHA256)
  - Shopify: X-Shopify-Hmac-SHA256
- Se responde inmediatamente con 200 (no bloqueante)

### 2. Procesamiento Asincrónico
- Se llama a `process_order_webhook()` que:
  1. **Normaliza** datos de la plataforma a estructura estándar
  2. **Valida** estructura del pedido
  3. **Detecta duplicados** por (source + sourceOrderId)
  4. **Enriquece** con datos de productos (stock, margen, etc.)
  5. **Sincroniza** con el CRM configurado del usuario
  6. **Guarda** en MongoDB con auditoría

### 3. Sincronización con CRM

#### Dolibarr
- Crea/actualiza Customer (Tercero) en Dolibarr
- Crea Order (Pedido de cliente) con líneas de producto
- Guarda Dolibarr Order ID para referencia

#### Odoo
- Similar a Dolibarr (implementación pendiente)

### 4. Guardado en MongoDB

Colección: `orders`
```json
{
  "id": "uuid",
  "source": "woocommerce",
  "sourceOrderId": "12345",
  "customer": {
    "name": "Juan García",
    "email": "juan@example.com",
    "phone": "+34601234567"
  },
  "items": [
    {
      "sku": "PROD-001",
      "quantity": 2,
      "price": 29.99,
      "name": "Producto A",
      "status": "available" | "backorder" | "not_found"
    }
  ],
  "addresses": {
    "shipping": { "street": "Calle X", "city": "Madrid", ... },
    "billing": { ... }
  },
  "totalAmount": 59.98,
  "totalItems": 2,
  "status": "completed" | "backorder" | "error",
  "crmData": {
    "crm": "dolibarr",
    "dolibarr_order_id": "50",
    "dolibarr_customer_id": "25"
  },
  "history": [
    {
      "action": "created",
      "timestamp": "2026-03-31T...",
      "details": {}
    }
  ],
  "createdAt": "2026-03-31T..."
}
```

## APIs

### Listar Pedidos
```
GET /api/orders?status=completed&source=woocommerce&limit=50&skip=0
```

### Obtener Detalles de Pedido
```
GET /api/orders/{order_id}
```

### Listar Pedidos Fallidos
```
GET /api/orders/status/failed?limit=50&skip=0
```

### Resumen de Pedidos
```
GET /api/orders/status/summary
```

### Estadísticas por Fuente
```
GET /api/orders/stats/by-source
```

### Reintentar Pedido Fallido
```
POST /api/orders/{order_id}/retry
```

## Normalización por Plataforma

### WooCommerce
- Mapea `line_items` a `items`
- Usa `shipping` y `billing` de los datos de WooCommerce
- Obtiene email de `billing.email`
- Status de pago: `completed` → "paid", otros → "pending"

### Shopify
- Mapea `line_items` a `items`
- Usa `address1` + `address2` para dirección
- Obtiene email de `customer.email`
- Status de pago: `financial_status` = "paid" → "paid"

### PrestaShop
- Mapea `products` a `items`
- Estructura de dirección diferente
- Email de campo directo

## Configuración

### Variables de Entorno Requeridas
Ninguna adicional - usa la configuración existente de CRM.

### Inicializar Índices en MongoDB
```python
from services.orders import create_order_indexes

# Llamar en startup
indexes = create_order_indexes()
```

## Manejo de Errores

### Duplicados
- Se detectan por (source + sourceOrderId)
- Respuesta: 200 + `{"status": "duplicate"}`

### Productos No Encontrados
- Se marcan como `status: "not_found"` pero se continúa
- Se guarda el pedido pero se notifica al admin

### Sin Stock
- Se marcan como `status: "backorder"`
- Se guarda el pedido indicando backorder
- Se puede procesar después manualmente

### Error en CRM
- Se guarda pedido con `status: "error"`
- Se puede reintentar con POST `/api/orders/{order_id}/retry`
- Se crea notificación para el usuario

## Notificaciones

Se crean automáticamente:
- `order_processed`: Pedido procesado exitosamente
- `order_error`: Error en procesamiento

## Testing

```bash
# Prueba webhook WooCommerce
curl -X POST http://localhost:8001/api/webhooks/receive/{config_id} \
  -H "Content-Type: application/json" \
  -H "X-WC-Webhook-Signature: {signature}" \
  -d '{"id": 123, "line_items": [...]}'
```

## Limitaciones Actuales

1. **Sin reintentos automáticos** - Los errores de CRM requieren reintento manual
2. **Sin batch processing** - Procesa pedidos uno a uno
3. **No actualiza stock** - Los pedidos se sincronizan pero no restan del stock
4. **Odoo sin implementar** - Solo Dolibarr está completamente funcional

## Próximas Mejoras

- [ ] Implementar reintentos automáticos con exponential backoff
- [ ] Actualizar stock en SyncStock cuando se crea pedido
- [ ] Implementar sincronización bidireccional (estado de CRM → SyncStock)
- [ ] Implementar soporte para Odoo
- [ ] Alertas en tiempo real para errores
- [ ] Dashboard de estadísticas de pedidos

## Debugging

Logs importantes:
```
logger.info(f"Processing {platform} order {order.source_order_id}")
logger.warning(f"Product not found for SKU: {item.sku}")
logger.error(f"Error syncing to CRM: {error}")
```

Ver logs en:
- `systemd`: `journalctl -u syncstock-backend -f`
- `ficheros`: `/var/log/syncstock/`
