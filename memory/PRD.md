# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores.

## Funcionalidades Implementadas (100%)
- [x] Autenticación JWT (registro, login, token)
- [x] Gestión de proveedores CRUD
- [x] Sincronización FTP/SFTP/URL de productos
- [x] Mapeo de columnas CSV personalizable
- [x] Gestión de múltiples catálogos
- [x] Reglas de margen por catálogo
- [x] Unificación de productos por EAN
- [x] Exportación CSV (PrestaShop, WooCommerce, Shopify)
- [x] Exportación a WooCommerce API (con EAN como GTIN)
- [x] Sincronización automática WooCommerce (cada 12h, precio y stock)
- [x] Dashboard mejorado con stats WooCommerce y alertas de stock
- [x] Refactorización completa del backend a arquitectura modular
- [x] Ficha de producto con 2 pestañas (Proveedores + Datos editables)
- [x] Explorador FTP integrado en configuración de proveedor
- [x] Soporte multi-archivo por proveedor
- [x] Extracción automática de ZIP y detección de roles de archivo
- [x] Sincronización multi-archivo con fusión de datos por clave común
- [x] Auto-selección del ZIP más reciente y StockFile al conectar al FTP
- [x] Búsqueda dinámica del archivo más reciente durante sync automático
- [x] Sistema de notificaciones mejorado con alertas de cambio de precio
- [x] Configuración centralizada de MongoDB (config.py)
- [x] Historial de Sincronizaciones con gráficas
- [x] Refactorización de componentes frontend
- [x] Paginación de productos
- [x] **Ordenación de columnas en productos** (Febrero 2026)
  - Ordenar por nombre, precio, stock y número de proveedores
  - Indicadores visuales ASC/DESC en cabeceras
  - Integrado con paginación
- [x] **Gráficas de evolución de precios mejoradas** (Febrero 2026)
  - Gráfica de área con subidas (rojo) y bajadas (verde)
  - Panel "Productos más activos" con número de cambios
  - Vista detallada de evolución por producto con precio actual/min/max
  - Nuevos endpoints: `/api/price-history/top-products` y `/api/price-history/product/{name}`
- [x] **Mejoras en detección de columnas CSV** (Febrero 2026)
  - Más aliases para columnas comunes (partnumber, item_code, etc.)
  - Logging mejorado para depuración de columnas no detectadas
  - Endpoint `/api/suppliers/{id}/preview-file` para previsualizar CSV

## Arquitectura
- **Backend**: FastAPI modular + MongoDB + APScheduler
- **Frontend**: React + TailwindCSS + Shadcn UI + Recharts
- **Estructura Backend**:
```
/app/backend/
├── config.py        # Configuración centralizada
├── server.py        # Orquestador FastAPI
├── models/schemas.py
├── routes/
│   ├── auth.py, catalogs.py, dashboard.py
│   ├── products.py  # Con sorting
│   ├── suppliers.py # Con preview-file
│   └── woocommerce.py
└── services/
    ├── auth.py, database.py
    └── sync.py      # normalize_product_data mejorado
```

## Aliases de Columnas CSV (normalize_product_data)
```python
'sku': ['sku', 'codigo', 'code', 'ref', 'referencia', 'reference', 'id', 'product_id', 'partnumber', 'part_number', 'articulo', 'codigo_articulo', 'cod', 'item_code']
'name': ['name', 'nombre', 'title', 'titulo', 'product_name', 'descripcion', 'description', 'producto', 'articulo_nombre', 'item_name']
'price': ['price', 'precio', 'pvp', 'cost', 'coste', 'unit_price', 'tarifa', 'importe', 'pricen', 'precio_neto', 'net_price']
'stock': ['stock', 'quantity', 'cantidad', 'qty', 'inventory', 'disponible', 'existencias', 'unidades', 'disponibilidad', 'units']
```

## Problema Conocido: FTP con CSV de columnas no estándar
Si un archivo CSV tiene columnas con nombres diferentes a los aliases predefinidos, no se reconocerán los productos. **Solución**: Configurar el mapeo de columnas manualmente en la configuración del proveedor.

## Backlog Futuro
- [ ] Sistema de roles de usuario
- [ ] Notificaciones push en tiempo real (WebSockets)
- [ ] Alertas programadas por email
- [ ] Wizard de mapeo de columnas más visual

## Credenciales de Prueba
- Email: test@test.com
- Password: test123

## Última Actualización
Febrero 2026 - Ordenación de productos, gráficas de precios mejoradas, mejoras en detección de columnas CSV
