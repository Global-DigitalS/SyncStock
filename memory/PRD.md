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
- [x] Sincronización automática WooCommerce (cada 12h)
- [x] Dashboard mejorado con stats y alertas de stock
- [x] Refactorización completa del backend
- [x] Ficha de producto con pestañas (Proveedores + Datos editables)
- [x] Explorador FTP integrado
- [x] Soporte multi-archivo por proveedor
- [x] Sistema de notificaciones con alertas de precio
- [x] Configuración centralizada MongoDB (config.py)
- [x] Historial de Sincronizaciones con gráficas
- [x] Paginación y ordenación de productos
- [x] Gráficas de evolución de precios mejoradas
- [x] **Sistema de Roles de Usuario** (Febrero 2026)
  - Roles: admin, user, viewer
  - Permisos: read, write, delete, manage_users, manage_settings, sync, export
  - Primer usuario se convierte automáticamente en admin
  - Página de gestión de usuarios `/users` (solo admins)
  - Endpoints: GET/PUT/DELETE `/api/users/*`
- [x] **WebSockets para Notificaciones en Tiempo Real** (Febrero 2026)
  - Conexión WebSocket en `/ws/notifications/{user_id}`
  - Notificaciones push instantáneas de sincronización
  - Toasts automáticos para sync completado/error
  - Reconexión automática si se pierde conexión
- [x] **Asistente de Mapeo de Columnas Mejorado** (Febrero 2026)
  - Endpoint `/api/suppliers/{id}/preview-file` con sugerencias automáticas
  - Detección automática de columnas al abrir mapeo
  - Aliases expandidos para más formatos de CSV
  - Vista previa de datos del archivo

## Arquitectura
```
/app/backend/
├── config.py        # Configuración centralizada
├── server.py        # FastAPI + WebSocket Manager
├── models/schemas.py
├── routes/
│   ├── auth.py      # + gestión de usuarios y roles
│   ├── catalogs.py
│   ├── dashboard.py
│   ├── products.py
│   ├── suppliers.py # + preview-file endpoint
│   └── woocommerce.py
└── services/
    ├── auth.py      # + ROLE_PERMISSIONS, check_permission
    ├── database.py
    └── sync.py      # + send_realtime_notification

/app/frontend/src/
├── pages/
│   ├── UserManagement.jsx  # Gestión de usuarios (admin)
│   └── ...
├── components/
│   ├── ColumnMappingDialog.jsx  # + suggestedMapping prop
│   └── ...
└── App.js           # + WebSocket context, AuthContext exportado
```

## Roles y Permisos
| Rol | Permisos |
|-----|----------|
| admin | Todos (read, write, delete, manage_users, manage_settings, sync, export) |
| user | read, write, delete, sync, export |
| viewer | read (solo lectura) |

## WebSocket Events
```javascript
// Mensaje de notificación en tiempo real
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "type": "sync_complete|sync_error|price_change|stock_low|stock_out",
    "message": "...",
    "user_id": "...",
    "created_at": "..."
  }
}
```

## Backlog Futuro
- [ ] Alertas programadas por email
- [ ] Dashboard de analytics avanzado
- [ ] Importación masiva de proveedores
- [ ] API pública para integraciones

## Credenciales de Prueba
- Email: test@test.com (admin)
- Password: test123

## Última Actualización
Febrero 2026 - Sistema de roles, WebSockets en tiempo real, asistente de mapeo de columnas
