# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores.

## Funcionalidades Implementadas
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
- [x] Búsqueda dinámica del archivo más reciente durante sync automático (auto_latest)
- [x] **Sistema de notificaciones mejorado** (Febrero 2026)
  - Notificaciones de cambio de precio significativo (umbral configurable)
  - Alertas de stock bajo y sin stock
  - Notificaciones de sincronización (completadas y errores)
  - Filtros por tipo y estado (leídas/sin leer)
  - Estadísticas de notificaciones por tipo
  - Eliminar notificaciones individuales y en lote
- [x] **Configuración centralizada de MongoDB** (Febrero 2026)
  - Archivo config.py con todas las configuraciones documentadas
  - Umbrales configurables para notificaciones
  - Opciones de conexión avanzadas para MongoDB

## Arquitectura
- **Backend**: FastAPI modular + MongoDB + APScheduler
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Estructura**:
```
/app/backend/
├── config.py        # Configuración centralizada BD y notificaciones
├── server.py        # Orquestador FastAPI
├── models/
│   └── schemas.py   # Modelos Pydantic
├── routes/
│   ├── auth.py
│   ├── catalogs.py
│   ├── dashboard.py # Notificaciones, stats, exportación
│   ├── products.py
│   ├── suppliers.py
│   └── woocommerce.py
└── services/
    ├── auth.py
    ├── database.py
    └── sync.py      # Sincronización y generación de notificaciones
```

## Configuración de Notificaciones (config.py)
- `PRICE_CHANGE_THRESHOLD_PERCENT`: Umbral de cambio de precio para alertas (default: 10%)
- `LOW_STOCK_THRESHOLD`: Umbral de stock bajo (default: 5 unidades)
- `SUPPLIER_SYNC_INTERVAL_HOURS`: Intervalo de sincronización (default: 6 horas)
- `WOOCOMMERCE_SYNC_INTERVAL_HOURS`: Intervalo sincronización WooCommerce (default: 12 horas)

## Backlog (P2-P3)
- [ ] Mapeo de columnas para archivos TechData
- [ ] Gráficas de evolución de precios
- [ ] Sistema de roles de usuario
- [ ] Historial de sincronizaciones detallado
- [ ] Refactorizar componentes grandes del frontend (Products.jsx, Suppliers.jsx)
- [ ] Ampliar fuentes de datos (SFTP, APIs directas)

## Credenciales de Prueba
- Email: test@test.com
- Password: test123

## Última Actualización
Febrero 2026 - Sistema de notificaciones mejorado y configuración centralizada de MongoDB
