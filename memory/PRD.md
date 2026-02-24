# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores con las siguientes funcionalidades:
- Descargar archivos de productos (CSV) desde FTP/SFTP o URL
- Ver precios y stocks de proveedores
- Crear múltiples catálogos de productos personalizados
- Asignar reglas de márgenes de beneficio a catálogos
- Exportar catálogos a CSV y a WooCommerce
- Autenticación de usuarios mediante JWT
- Sistema de roles (viewer, user, admin, superadmin)

## Funcionalidades Implementadas (100%)

### Core Features
- [x] Autenticación JWT (registro, login, token)
- [x] Gestión de proveedores CRUD (FTP/URL)
- [x] Sincronización automática de productos
- [x] Mapeo de columnas CSV personalizable
- [x] Gestión de múltiples catálogos
- [x] Reglas de margen por catálogo
- [x] Unificación de productos por EAN
- [x] Exportación CSV (PrestaShop, WooCommerce, Shopify)
- [x] Exportación a WooCommerce API (con EAN como GTIN)
- [x] Sincronización automática WooCommerce

### Febrero 2026 - Funcionalidades Completadas
- [x] **Sistema de Roles y Límites de Usuario** (P0)
  - Roles: superadmin, admin, user, viewer
  - Límites configurables: proveedores, catálogos, tiendas WooCommerce
  - SuperAdmin puede establecer límites a cualquier usuario
  - Verificación de límites al crear recursos

- [x] **Dashboard SuperAdmin** (P2)
  - Estadísticas globales de la plataforma
  - Gráficos de usuarios por rol y recursos
  - Top usuarios por proveedores y productos
  - Estadísticas de sincronizaciones y WooCommerce

- [x] **Planes de Suscripción Editables** (Mejora)
  - 4 planes: Free, Starter, Professional, Enterprise
  - **SuperAdmin puede editar precios, límites y características de cada plan**
  - Toggle mensual/anual con ahorro calculado
  - Sistema de suscripción (simulado, sin pagos reales)

- [x] **Mejora Sincronización FTP** (Bug Fix)
  - Ampliados los aliases de columnas para detección automática
  - Mejor manejo de nombres de columna no estándar
  - Mensajes de error más descriptivos cuando falla el mapeo

- [x] **Refactorización de Componentes** (P3)
  - `ProductsTable.jsx` - Tabla de productos reutilizable
  - `ProductFilters.jsx` - Filtros de búsqueda
  - `SupplierCard.jsx` - Tarjeta de proveedor
  - Componentes compartidos: Pagination, SortableHeader, EmptyState, StockBadge, FileDropzone

- [x] **WebSockets para Notificaciones en Tiempo Real**
- [x] **Asistente de Mapeo de Columnas**
- [x] **Historial de Sincronizaciones**
- [x] **Paginación y Ordenación de Productos**

## Arquitectura
```
/app/backend/
├── config.py
├── server.py         # FastAPI + WebSocket + Scheduler
├── models/schemas.py
├── routes/
│   ├── auth.py            # Auth + usuarios + límites
│   ├── catalogs.py        # Catálogos y márgenes
│   ├── dashboard.py       # Stats + superadmin stats
│   ├── products.py        # Productos + unificación
│   ├── suppliers.py       # Proveedores + FTP
│   ├── subscriptions.py   # Planes editables + suscripciones
│   └── woocommerce.py
└── services/
    ├── auth.py            # Roles, permisos, límites
    ├── database.py
    └── sync.py            # Sincronización mejorada

/app/frontend/src/
├── pages/
│   ├── Subscriptions.jsx  # Con modo edición para SuperAdmin
│   ├── SuperAdminDashboard.jsx
│   ├── UserManagement.jsx
│   └── ...
├── components/
│   ├── products/          # Componentes refactorizados
│   │   ├── ProductsTable.jsx
│   │   └── ProductFilters.jsx
│   ├── suppliers/
│   │   └── SupplierCard.jsx
│   ├── shared/            # Componentes reutilizables
│   │   ├── Pagination.jsx
│   │   ├── SortableHeader.jsx
│   │   ├── EmptyState.jsx
│   │   ├── StockBadge.jsx
│   │   └── FileDropzone.jsx
│   └── dialogs/
│       └── ProductDetailDialog.jsx
└── App.js
```

## Roles y Permisos
| Rol | Permisos | Límites por defecto |
|-----|----------|---------------------|
| superadmin | Todos + manage_limits + edit_plans | Ilimitados |
| admin | read, write, delete, manage_settings, sync, export | 50/20/10 |
| user | read, write, delete, sync, export | 10/5/2 |
| viewer | read | 0/0/0 |

## Planes de Suscripción (Editables por SuperAdmin)
| Plan | Precio/mes | Precio/año | Proveedores | Catálogos | Tiendas |
|------|------------|------------|-------------|-----------|---------|
| Free | €0 | €0 | 2 | 1 | 1 |
| Starter | €19.99 | €199.99 | 10 | 5 | 2 |
| Professional | €49.99 | €499.99 | 50 | 20 | 10 |
| Enterprise | €199.99 | €1999.99 | ∞ | ∞ | ∞ |

## Key API Endpoints
- `PUT /api/subscriptions/plans/{plan_id}` - Editar plan (SuperAdmin only)
- `GET /api/dashboard/superadmin-stats` - Stats globales
- `PUT /api/users/{id}/limits` - Actualizar límites de usuario

## Issues Conocidos
- Bug FTP: Si el archivo CSV usa nombres de columna muy inusuales, puede requerir mapeo manual. La mejora de aliases ayuda pero no cubre todos los casos posibles.

## Testing
- Backend: 100% tests passed
- Frontend: 100% flows verified
- Última iteración: iteration_14.json

## Backlog Futuro
- [ ] Integración con Stripe para pagos reales
- [ ] SFTP/APIs como fuentes de datos adicionales
- [ ] Autenticación de dos factores (2FA)
- [ ] Dashboard de analytics avanzado

## Credenciales de Prueba
- SuperAdmin: test@test.com / test123
- Admin: admin@test.com / admin123

## Última Actualización
24 Febrero 2026 - Edición de planes por SuperAdmin, mejoras FTP, refactorización completada
