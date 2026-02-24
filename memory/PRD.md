# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores con las siguientes funcionalidades:
- Descargar archivos de productos (CSV) desde FTP/SFTP o URL
- Ver precios y stocks de proveedores
- Crear múltiples catálogos de productos personalizados
- Asignar reglas de márgenes de beneficio a catálogos
- Exportar catálogos a múltiples plataformas eCommerce
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
- [x] Exportación CSV (múltiples formatos)

### Febrero 2026 - Sistema Multi-Plataforma de Tiendas

#### Integraciones eCommerce Reales (NUEVO)
- [x] **WooCommerce** - Integración completa (WooCommerce API)
- [x] **PrestaShop** - Cliente real (Webservice API, formato XML)
- [x] **Shopify** - Cliente real (Admin API 2024-10)
- [x] **Magento** - Cliente real (REST API V1)
- [x] **Wix eCommerce** - Cliente real (Stores API)

Cada plataforma tiene:
- Test de conexión real
- CRUD de productos
- Actualización de inventario
- Sincronización de precios

#### Sistema de Webhooks (NUEVO)
- [x] **Configuración de webhooks** por tienda
- [x] **Eventos soportados:**
  - inventory.updated - Actualización de inventario
  - order.created - Pedido creado
  - order.completed - Pedido completado
  - product.updated - Producto actualizado
  - product.created - Producto creado
- [x] **Verificación de firmas** (HMAC-SHA256)
- [x] **Procesamiento en background** de eventos
- [x] **Logs de eventos** y estadísticas
- [x] **Secret key** regenerable
- [x] **Página de gestión** con UI completa

#### SuperAdmin y Sistema de Límites
- [x] Roles: superadmin, admin, user, viewer
- [x] Límites configurables por usuario
- [x] Dashboard SuperAdmin con estadísticas globales

#### Planes de Suscripción
- [x] 4 planes editables: Free, Starter, Professional, Enterprise
- [x] SuperAdmin puede editar precios y características

## Arquitectura
```
/app/backend/
├── routes/
│   ├── auth.py
│   ├── stores.py          # Multi-plataforma eCommerce
│   ├── webhooks.py        # Sistema de webhooks (NUEVO)
│   ├── subscriptions.py
│   └── ...
├── services/
│   ├── platforms.py       # Clientes eCommerce (NUEVO)
│   │   ├── PrestaShopClient
│   │   ├── ShopifyClient
│   │   ├── MagentoClient
│   │   └── WixClient
│   ├── sync.py
│   └── ...
└── ...

/app/frontend/src/
├── pages/
│   ├── WooCommerceExport.jsx  # Ahora "Tiendas"
│   ├── Webhooks.jsx           # Gestión de webhooks (NUEVO)
│   └── ...
└── ...
```

## Plataformas de Tiendas Soportadas

| Plataforma | Estado | API Client | Funcionalidades |
|------------|--------|------------|-----------------|
| WooCommerce | ✅ Completo | woocommerce | CRUD, Sync, Export |
| PrestaShop | ✅ Real | PrestaShopClient | Test, CRUD, Stock |
| Shopify | ✅ Real | ShopifyClient | Test, CRUD, Inventory |
| Magento | ✅ Real | MagentoClient | Test, CRUD, Stock |
| Wix | ✅ Real | WixClient | Test, CRUD, Inventory |

**Nota**: Todas las integraciones tienen implementaciones reales que hacen llamadas HTTP a las APIs oficiales. Requieren credenciales válidas para funcionar completamente.

## Webhooks API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| /api/webhooks/configs | GET | Listar webhooks |
| /api/webhooks/configs | POST | Crear webhook |
| /api/webhooks/configs/{id} | PUT | Actualizar webhook |
| /api/webhooks/configs/{id} | DELETE | Eliminar webhook |
| /api/webhooks/configs/{id}/regenerate-secret | POST | Regenerar secret |
| /api/webhooks/receive/{config_id} | POST | Recibir evento (sin auth) |
| /api/webhooks/events | GET | Logs de eventos |
| /api/webhooks/stats | GET | Estadísticas |

## Testing
- Backend: 100% (14/14 tests plataformas y webhooks)
- Frontend: 100% (todos los flujos verificados)
- Última iteración: iteration_16.json

## Backlog Futuro
- [ ] Integración con Stripe para pagos reales
- [ ] SFTP como fuente de datos
- [ ] Autenticación 2FA
- [ ] Dashboard de analytics avanzado

## Credenciales de Prueba
- SuperAdmin: test@test.com / test123
- Admin: admin@test.com / admin123

## Última Actualización
24 Febrero 2026 - Integraciones reales (PrestaShop, Shopify, Magento, Wix) + Sistema de Webhooks completo
