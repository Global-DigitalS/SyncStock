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
- [x] Búsqueda dinámica del archivo más reciente durante sync automático (auto_latest)
- [x] Sistema de notificaciones mejorado con alertas de cambio de precio
- [x] Configuración centralizada de MongoDB (config.py)
- [x] **Historial de Sincronizaciones** (Febrero 2026)
  - Página dedicada `/sync-history` con estadísticas
  - Gráfica de barras por día (exitosas vs errores)
  - Filtros por proveedor, estado y rango de días
  - Tabla detallada con métricas (importados, actualizados, errores, duración)
  - Registro automático de cada sincronización
- [x] **Refactorización de componentes frontend** (Febrero 2026)
  - FtpFileBrowser.jsx - Explorador FTP reutilizable
  - ProductDetailDialog.jsx - Ficha de producto con pestañas
  - CatalogSelectorDialog.jsx - Selector de catálogos

## Arquitectura
- **Backend**: FastAPI modular + MongoDB + APScheduler
- **Frontend**: React + TailwindCSS + Shadcn UI + Recharts
- **Estructura Backend**:
```
/app/backend/
├── config.py        # Configuración centralizada BD y notificaciones
├── server.py        # Orquestador FastAPI
├── models/
│   └── schemas.py   # Modelos Pydantic (incluyendo SyncHistoryResponse)
├── routes/
│   ├── auth.py
│   ├── catalogs.py
│   ├── dashboard.py # Notificaciones, stats, sync-history, exportación
│   ├── products.py
│   ├── suppliers.py
│   └── woocommerce.py
└── services/
    ├── auth.py
    ├── database.py
    └── sync.py      # Sincronización y record_sync_history
```
- **Estructura Frontend**:
```
/app/frontend/src/
├── pages/
│   ├── SyncHistory.jsx  # Nueva página de historial
│   └── ...
├── components/
│   ├── FtpFileBrowser.jsx       # Explorador FTP refactorizado
│   ├── ProductDetailDialog.jsx  # Ficha de producto refactorizada
│   ├── CatalogSelectorDialog.jsx
│   └── Sidebar.jsx              # Con enlace a sync-history
└── ...
```

## Nuevos Endpoints API
- `GET /api/sync-history` - Lista de sincronizaciones con filtros
- `GET /api/sync-history/stats` - Estadísticas para gráficas

## Colecciones MongoDB
- **sync_history**: Historial de sincronizaciones
  - id, supplier_id, supplier_name, sync_type (manual/scheduled)
  - status (success/error/partial), imported, updated, errors
  - duration_seconds, error_message, user_id, created_at

## Backlog Futuro
- [ ] Gráficas de evolución de precios por producto
- [ ] Sistema de roles de usuario
- [ ] Notificaciones push en tiempo real (WebSockets)
- [ ] Integración SFTP y APIs directas

## Credenciales de Prueba
- Email: test@test.com
- Password: test123

## Última Actualización
Febrero 2026 - Historial de sincronizaciones y refactorización de componentes frontend
