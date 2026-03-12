# Integración de Odoo 17 en SyncStock

## Descripción General

Se ha implementado una integración completa de Odoo 17 en SyncStock, siguiendo el mismo patrón arquitectónico que la integración existente con Dolibarr.

## Características Implementadas

### 1. Cliente OdooClient (`backend/routes/crm.py`)
- **Autenticación**: API Token (Bearer token en Authorization header)
- **Comunicación**: REST API con JSON
- **Rate Limiting**: 100ms entre requests (configurable)
- **Connection Pooling**: 10 conexiones simultáneas máximo

#### Métodos Principales

- `test_connection()` - Prueba la conexión con Odoo
- `get_products(limit=500)` - Obtiene productos de Odoo
- `get_product_by_sku(sku)` - Busca producto por SKU
- `create_product(product_data)` - Crea nuevo producto
- `update_product(product_id, product_data)` - Actualiza producto existente
- `update_stock(product_id, stock)` - Actualiza stock de producto
- `get_warehouses()` - Obtiene almacenes disponibles
- `get_suppliers(limit=500)` - Obtiene proveedores/partners
- `create_supplier(supplier_data)` - Crea nuevo proveedor
- `update_supplier(supplier_id, supplier_data)` - Actualiza proveedor
- `link_product_to_supplier(product_sku, supplier_id, purchase_price)` - Vincula producto a proveedor
- `get_orders(limit=100)` - Obtiene órdenes de venta
- `get_purchase_orders(limit=100)` - Obtiene órdenes de compra
- `get_stats()` - Obtiene estadísticas del CRM

### 2. Endpoints API Actualizados

Todos los endpoints existentes para Dolibarr ahora soportan Odoo:

#### POST `/crm/connections`
Crear nueva conexión Odoo:
```json
{
  "name": "Mi Odoo",
  "platform": "odoo",
  "config": {
    "api_url": "https://odoo.example.com",
    "api_token": "token_api_123456"
  },
  "sync_settings": {
    "products": true,
    "stock": true,
    "prices": true,
    "descriptions": true,
    "images": true,
    "suppliers": true,
    "orders": true
  }
}
```

#### POST `/crm/test-connection`
Probar conexión sin guardarla:
```json
{
  "platform": "odoo",
  "config": {
    "api_url": "https://odoo.example.com",
    "api_token": "token_api_123456"
  }
}
```

#### PUT `/crm/connections/{connection_id}`
Actualizar conexión existente

#### DELETE `/crm/connections/{connection_id}`
Eliminar conexión

#### GET `/crm/connections`
Obtener todas las conexiones (ahora incluye stats para Odoo)

#### POST `/crm/connections/{connection_id}/sync`
Sincronizar con Odoo:
```json
{
  "sync_type": "all",  // "all", "products", "suppliers", "orders"
  "catalog_id": "optional_catalog_id"
}
```

### 3. Funciones de Sincronización

#### `async def sync_products_to_odoo()`
- Sincroniza productos desde SyncStock a Odoo
- Soporta creación y actualización
- Sincroniza imágenes, precios y stock
- Usa margin rules para cálculo de precios si aplica

#### `async def sync_suppliers_to_odoo()`
- Sincroniza proveedores hacia Odoo
- Crea nuevos partners o actualiza existentes
- Vincula productos a proveedores

#### `async def sync_orders_to_odoo()`
- Importa órdenes de WooCommerce a Odoo
- Rastrea órdenes sincronizadas para evitar duplicados
- Registra el historial en `crm_synced_orders`

## Configuración Requerida

### En Odoo 17:
1. Crear un usuario con permisos de administrador
2. Generar un API Token:
   - Ir a Settings > Users > Your User
   - Copiar el Access Token

### En SyncStock:
1. Crear una conexión CRM desde la interfaz
2. Ingresar:
   - URL base de Odoo (ej: https://odoo.example.com)
   - API Token
3. Hacer clic en "Test Connection" para validar

## Diferencias con Dolibarr

| Aspecto | Dolibarr | Odoo |
|--------|----------|------|
| **Autenticación** | API Key header `DOLAPIKEY` | Bearer token |
| **Stock** | `stock.warehouse` y `stock.move` | Misma estructura |
| **Partners** | Thirdparties/Suppliers | res.partner con flags |
| **Órdenes** | sale.order, purchase.order | sale.order, purchase.order |
| **Productos** | product.product | product.product |

## Implementación Técnica

### Clase OdooClient

La clase sigue el mismo patrón que DolibarrClient:

```python
class OdooClient:
    def __init__(self, api_url: str, api_token: str):
        # Session pooling
        # HTTP adapter con 10 conexiones
        # Rate limiting de 100ms
    
    def _rate_limited_request(self, method, url, **kwargs):
        # Implementa rate limiting automático
```

### Conexión a Base de Datos

Las conexiones se guardan en `crm_connections` con:
- `platform`: "odoo"
- `config`: {api_url, api_token}
- `sync_settings`: configuración de qué sincronizar
- `is_connected`: estado de conexión
- `last_sync`: timestamp del último sync

### Jobs de Sincronización

El sync es asincrónico y rastrea progreso en `sync_jobs`:
- `status`: "running", "completed", "error"
- `progress`: porcentaje (0-100)
- `current_step`: paso actual
- `results`: resumen de creaciones/actualizaciones

## Pruebas Recomendadas

1. **Conexión**: POST `/crm/test-connection` con datos de Odoo
2. **Crear conexión**: POST `/crm/connections`
3. **Sincronizar productos**: POST `/crm/connections/{id}/sync` con `sync_type: "products"`
4. **Verificar stats**: GET `/crm/connections` - debe incluir stats de Odoo
5. **Sincronizar proveedores**: POST `/crm/connections/{id}/sync` con `sync_type: "suppliers"`
6. **Sincronizar órdenes**: POST `/crm/connections/{id}/sync` con `sync_type: "orders"`

## Limitaciones Actuales

1. **Órdenes**: Solo se importan órdenes de WooCommerce a Odoo (no sincronización bidireccional)
2. **Clientes**: No se crear/actualiza clientes en Odoo (solo conteo en stats)
3. **Descuentos**: No se sincronizan descuentos ni promociones
4. **Atributos**: No se sincronizan atributos de productos (color, talla, etc.)

## Mejoras Futuras

1. Sincronización bidireccional de órdenes
2. Manejo de variantes de productos (attributes)
3. Sincronización de clientes/contactos
4. Descuentos y promociones
5. Warehouse/almacén específico
6. Integración de pagos y reconciliación

## Estructura de Archivos

```
backend/
  routes/
    crm.py  # Contiene DolibarrClient y OdooClient
  services/
    database.py  # Conexión MongoDB
    auth.py  # Autenticación
```

## Requisitos de Paquetes

Python packages necesarios (ya incluidos en requirements.txt):
- `requests>=2.28.0` - HTTP client
- `motor>=3.0.0` - MongoDB async driver

## Ejemplos de Uso

### Crear conexión Odoo
```bash
curl -X POST http://localhost:8000/crm/connections \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Odoo",
    "platform": "odoo",
    "config": {
      "api_url": "https://odoo.example.com",
      "api_token": "your_token"
    }
  }'
```

### Sincronizar datos
```bash
curl -X POST http://localhost:8000/crm/connections/conn_id/sync \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "all"
  }'
```

### Obtener estado de sincronización
```bash
curl -X GET http://localhost:8000/crm/sync-jobs/job_id \
  -H "Authorization: Bearer token"
```

## Notas de Desarrollo

- El cliente OdooClient utiliza `requests.Session` con pooling para eficiencia
- Todos los requests tienen timeout de 30s
- Los logs incluyen timestamps y detalles para debugging
- Las excepciones son capturadas y registradas sin romper la ejecución
- Rate limiting se configura automáticamente a 100ms entre requests

## Compatibilidad

- ✅ Odoo 17.0 (confirmado)
- ✅ Odoo 16.0 (debería funcionar)
- ❓ Versiones anteriores (no probado)

Requiere que Odoo esté accesible vía HTTPS con API REST habilitada.
