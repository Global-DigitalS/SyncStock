# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores con las siguientes funcionalidades:
- Descargar archivos de productos (CSV) desde FTP/SFTP o URL
- Ver precios y stocks de proveedores
- Crear múltiples catálogos de productos personalizados
- Asignar reglas de márgenes de beneficio a catálogos
- Exportar catálogos a CSV y a múltiples plataformas eCommerce
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

### Febrero 2026 - Últimas Actualizaciones

#### Sistema Multi-Plataforma de Tiendas (NUEVO)
- [x] **Renombrado de "WooCommerce" a "Tiendas"**
- [x] **Soporte para 5 plataformas eCommerce:**
  - **WooCommerce** - Integración completa funcional
  - **PrestaShop** - Configuración lista (demo)
  - **Shopify** - Configuración lista (demo)
  - **Wix eCommerce** - Configuración lista (demo)
  - **Magento** - Configuración lista (demo)
- [x] Selector de plataforma al añadir tienda
- [x] Formularios de configuración específicos por plataforma
- [x] Credenciales enmascaradas en respuestas API

#### SuperAdmin y Sistema de Límites
- [x] Roles: superadmin, admin, user, viewer
- [x] Límites configurables por usuario
- [x] Dashboard SuperAdmin con estadísticas globales

#### Planes de Suscripción
- [x] 4 planes editables: Free, Starter, Professional, Enterprise
- [x] SuperAdmin puede editar precios y características
- [x] Toggle mensual/anual

#### Otras Mejoras
- [x] WebSockets para notificaciones en tiempo real
- [x] Historial de sincronizaciones
- [x] Paginación y ordenación de productos
- [x] Componentes refactorizados

## Arquitectura
```
/app/backend/
├── routes/
│   ├── auth.py            # Auth + usuarios + límites
│   ├── stores.py          # Tiendas multi-plataforma (NUEVO)
│   ├── woocommerce.py     # Integración WooCommerce (legado)
│   ├── subscriptions.py   # Planes editables
│   └── ...
└── services/
    ├── sync.py            # Sincronización mejorada
    └── ...

/app/frontend/src/
├── pages/
│   ├── WooCommerceExport.jsx  # Ahora StoresPage multi-plataforma
│   ├── Subscriptions.jsx      # Edición de planes
│   ├── SuperAdminDashboard.jsx
│   └── ...
├── components/
│   ├── Sidebar.jsx            # "Tiendas" en lugar de "WooCommerce"
│   └── ...
└── App.js                     # Ruta /stores
```

## Plataformas de Tiendas Soportadas

| Plataforma | Estado | Campos de Configuración |
|------------|--------|------------------------|
| WooCommerce | ✅ Funcional | store_url, consumer_key, consumer_secret |
| PrestaShop | 🔶 Demo | store_url, api_key |
| Shopify | 🔶 Demo | store_url, access_token, api_version |
| Wix eCommerce | 🔶 Demo | store_url, api_key, site_id |
| Magento | 🔶 Demo | store_url, access_token, store_code |

**Nota**: Las integraciones de PrestaShop, Shopify, Wix y Magento están en modo demo. La prueba de conexión retorna éxito pero no realiza llamadas API reales.

## Key API Endpoints
- `GET /api/stores/configs` - Listar tiendas del usuario
- `POST /api/stores/configs` - Crear tienda (con platform)
- `PUT /api/stores/configs/{id}` - Actualizar tienda
- `POST /api/stores/configs/{id}/test` - Probar conexión
- `POST /api/stores/configs/{id}/sync` - Sincronizar precio/stock
- `POST /api/stores/export` - Exportar productos a tienda
- `PUT /api/subscriptions/plans/{plan_id}` - Editar plan (SuperAdmin)

## Testing
- Backend: 100% (16/16 tests)
- Frontend: 100% (todos los flujos verificados)
- Última iteración: iteration_15.json

## Backlog Futuro
- [ ] Integración real para PrestaShop, Shopify, Wix, Magento
- [ ] Integración con Stripe para pagos reales
- [ ] SFTP/APIs como fuentes de datos adicionales
- [ ] Autenticación de dos factores (2FA)

## Credenciales de Prueba
- SuperAdmin: test@test.com / test123
- Admin: admin@test.com / admin123

## Última Actualización
24 Febrero 2026 - Sistema multi-plataforma de tiendas (WooCommerce, PrestaShop, Shopify, Wix, Magento)
