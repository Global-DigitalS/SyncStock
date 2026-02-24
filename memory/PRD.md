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

### Febrero 2026 - Últimas funcionalidades
- [x] **Sistema de Roles de Usuario**
  - Roles: superadmin, admin, user, viewer
  - Permisos diferenciados por rol
  - Primer usuario se convierte automáticamente en superadmin
  
- [x] **SuperAdmin y Sistema de Límites** (P0)
  - Límites configurables: proveedores, catálogos, tiendas WooCommerce
  - Endpoint PUT /api/users/{id}/limits (solo superadmin)
  - Verificación de límites al crear recursos
  - UI de gestión de límites en página de usuarios

- [x] **Dashboard SuperAdmin** (P2)
  - Estadísticas globales de la plataforma
  - Gráficos de usuarios por rol y recursos
  - Top usuarios por proveedores y productos
  - Estadísticas de sincronizaciones y WooCommerce

- [x] **Planes de Suscripción** (Mejora potencial)
  - 4 planes: Free, Starter (€19.99), Professional (€49.99), Enterprise (€199.99)
  - Toggle mensual/anual con ahorro
  - Sistema simulado de suscripciones
  - Actualización automática de límites al suscribirse

- [x] **WebSockets para Notificaciones en Tiempo Real**
  - Conexión WebSocket en `/ws/notifications/{user_id}`
  - Toasts automáticos de sincronización
  
- [x] **Asistente de Mapeo de Columnas**
  - Detección automática de columnas
  - Vista previa de datos del archivo

### Refactorización (P3 - Parcial)
- [x] Componentes compartidos creados:
  - Pagination.jsx - Paginación reutilizable
  - SortableHeader.jsx - Headers ordenables
  - EmptyState.jsx - Estado vacío genérico
  - StockBadge.jsx - Badges de stock
  - FileDropzone.jsx - Zona de arrastre de archivos
  - ProductDetailDialog.jsx - Diálogo de detalle de producto

## Arquitectura
```
/app/backend/
├── config.py        # Configuración centralizada
├── server.py        # FastAPI + WebSocket + Scheduler
├── models/schemas.py
├── routes/
│   ├── auth.py          # Autenticación + gestión usuarios
│   ├── catalogs.py      # Catálogos y márgenes
│   ├── dashboard.py     # Stats + notificaciones + superadmin stats
│   ├── products.py      # Productos + unificación
│   ├── suppliers.py     # Proveedores + FTP
│   ├── subscriptions.py # Planes y suscripciones (NUEVO)
│   └── woocommerce.py   # Integración WC
└── services/
    ├── auth.py          # Roles, permisos, límites
    ├── database.py      # MongoDB
    └── sync.py          # Sincronización

/app/frontend/src/
├── pages/
│   ├── Dashboard.jsx
│   ├── Products.jsx
│   ├── Suppliers.jsx
│   ├── Catalogs.jsx
│   ├── UserManagement.jsx
│   ├── SuperAdminDashboard.jsx (NUEVO)
│   ├── Subscriptions.jsx (NUEVO)
│   └── ...
├── components/
│   ├── Sidebar.jsx
│   ├── shared/           # Componentes reutilizables (NUEVO)
│   │   ├── Pagination.jsx
│   │   ├── SortableHeader.jsx
│   │   ├── EmptyState.jsx
│   │   ├── StockBadge.jsx
│   │   └── FileDropzone.jsx
│   └── dialogs/
│       └── ProductDetailDialog.jsx (NUEVO)
└── App.js
```

## Roles y Permisos
| Rol | Permisos | Límites por defecto |
|-----|----------|---------------------|
| superadmin | Todos + manage_limits | Ilimitados |
| admin | read, write, delete, manage_settings, sync, export | 50/20/10 |
| user | read, write, delete, sync, export | 10/5/2 |
| viewer | read | 0/0/0 |

## Planes de Suscripción
| Plan | Precio/mes | Precio/año | Proveedores | Catálogos | Tiendas |
|------|------------|------------|-------------|-----------|---------|
| Free | €0 | €0 | 2 | 1 | 1 |
| Starter | €19.99 | €199.99 | 10 | 5 | 2 |
| Professional | €49.99 | €499.99 | 50 | 20 | 10 |
| Enterprise | €199.99 | €1999.99 | ∞ | ∞ | ∞ |

## Key API Endpoints
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Login y obtención de token
- `GET /api/users` - Listar usuarios (admin+)
- `PUT /api/users/{id}/limits` - Actualizar límites (superadmin)
- `GET /api/dashboard/superadmin-stats` - Stats globales (superadmin)
- `GET /api/subscriptions/plans` - Planes disponibles
- `POST /api/subscriptions/subscribe/{plan_id}` - Suscribirse

## Issues Conocidos
- Bug FTP: Sincronización de proveedores con un solo CSV sin mapeo explícito (PENDIENTE - esperando credenciales FTP del usuario para reproducir)

## Backlog Futuro
- [ ] Ampliar fuentes de datos (SFTP, APIs)
- [ ] Completar refactorización de Products.jsx y Suppliers.jsx
- [ ] Autenticación de dos factores (2FA)
- [ ] Dashboard de analytics avanzado
- [ ] Integración con pasarela de pagos real (Stripe)
- [ ] API pública para integraciones

## Credenciales de Prueba
- SuperAdmin: test@test.com / test123
- Admin: admin@test.com / admin123

## Última Actualización
24 Febrero 2026 - Sistema SuperAdmin, Dashboard Admin, Planes de Suscripción, Componentes refactorizados
