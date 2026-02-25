# SupplierSync Pro - PRD

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos CSV de productos desde FTP/SFTP o URL, ver precios y stocks, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Usuarios y Roles
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **SuperAdmin** | Administrador global de la plataforma | Gestión de usuarios, límites de recursos, planes de suscripción, dashboard global |
| **Admin** | Administrador de una organización | Gestión completa de proveedores, productos, catálogos, tiendas |
| **User** | Usuario operativo | CRUD de proveedores, productos, catálogos (dentro de sus límites) |
| **Viewer** | Solo lectura | Visualización de datos sin modificación |

## Funcionalidades Implementadas

### ✅ P0 - Core (Completado)

#### Autenticación y Usuarios
- [x] Login/Registro con JWT
- [x] Sistema de roles (SuperAdmin, Admin, User, Viewer)
- [x] Límites de recursos por usuario
- [x] Gestión de usuarios por SuperAdmin

#### Gestión de Proveedores
- [x] CRUD de proveedores (FTP, URL directa)
- [x] Sincronización automática de archivos CSV
- [x] Mapeo de columnas flexible
- [x] Historial de sincronizaciones
- [x] Detección de columnas en archivos CSV

#### **Nuevo Flujo de Productos** (Implementado 25/02/2026)
- [x] Selección de productos desde vista del proveedor
- [x] Banner "Flujo de Productos" con estadísticas
- [x] Selección masiva por categoría o individual
- [x] Campo `is_selected` en modelo de productos
- [x] Página Productos solo muestra productos seleccionados
- [x] Endpoints: `/products/select`, `/products/deselect`, `/products/select-by-supplier`

#### Catálogos y Márgenes
- [x] Creación de múltiples catálogos
- [x] Reglas de margen (porcentaje, fijo, por categoría)
- [x] Exportación a CSV
- [x] Añadir productos a catálogos

#### Tiendas Multi-plataforma
- [x] WooCommerce (integración completa)
- [x] PrestaShop (integración completa)
- [x] Shopify (integración básica)
- [x] Wix eCommerce (UI, sin integración)
- [x] Magento (UI, sin integración)
- [x] Sincronización de precios y stock

#### **Página de Configuración Inicial** (Implementado 25/02/2026)
- [x] Verificación de estado de configuración
- [x] Test de conexión a MongoDB
- [x] Creación de usuario SuperAdmin
- [x] Redirección automática si ya está configurado
- [x] Endpoints: `/setup/status`, `/setup/configure`, `/setup/test-connection`

### ✅ P1 - Funcionalidades Adicionales (Completado)

#### Dashboard y Estadísticas
- [x] Dashboard principal con resumen
- [x] Dashboard SuperAdmin con estadísticas globales
- [x] Historial de precios
- [x] Notificaciones en tiempo real (WebSocket)

#### Planes y Suscripciones
- [x] Gestión de planes de suscripción
- [x] Edición de planes por SuperAdmin
- [x] Asignación de planes a usuarios

#### Webhooks
- [x] Sistema de webhooks para eventos
- [x] Configuración de URLs de destino
- [x] Gestión de eventos (productos, tiendas, catálogos)

### 🟡 P2 - Pendiente

#### Mejoras de Integración
- [ ] SFTP como fuente de datos
- [ ] APIs directas de proveedores
- [ ] Integración real con Wix y Magento

#### Seguridad
- [ ] Autenticación de dos factores (2FA)
- [ ] Logs de auditoría avanzados

## Arquitectura Técnica

```
/app/
├── backend/                    # FastAPI + MongoDB
│   ├── models/schemas.py       # Pydantic models
│   ├── routes/
│   │   ├── auth.py            # Autenticación JWT
│   │   ├── suppliers.py       # CRUD proveedores
│   │   ├── products.py        # CRUD productos + selección
│   │   ├── catalogs.py        # CRUD catálogos
│   │   ├── stores.py          # Tiendas multi-plataforma
│   │   ├── subscriptions.py   # Planes de suscripción
│   │   ├── webhooks.py        # Sistema de webhooks
│   │   ├── setup.py           # Configuración inicial
│   │   └── dashboard.py       # Estadísticas
│   ├── services/
│   │   ├── sync.py            # Sincronización FTP/URL
│   │   ├── auth.py            # JWT helpers
│   │   └── store_integrations.py  # Integraciones eCommerce
│   └── server.py              # Main app + health check
└── frontend/                   # React + TailwindCSS + Shadcn
    ├── src/
    │   ├── pages/
    │   │   ├── Setup.jsx      # Configuración inicial
    │   │   ├── Products.jsx   # Productos seleccionados
    │   │   ├── Suppliers.jsx  # Lista de proveedores
    │   │   ├── SupplierDetail.jsx  # Detalle + selección
    │   │   ├── Stores.jsx     # Tiendas multi-plataforma
    │   │   └── ...
    │   └── components/ui/     # Shadcn components
    └── ...
```

## APIs Principales

### Setup
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/setup/status` | Estado de configuración |
| POST | `/api/setup/test-connection` | Test conexión MongoDB |
| POST | `/api/setup/configure` | Configurar app + crear SuperAdmin |

### Selección de Productos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/products/selected-count` | Conteo de productos seleccionados |
| POST | `/api/products/select` | Seleccionar productos por IDs |
| POST | `/api/products/deselect` | Deseleccionar productos por IDs |
| POST | `/api/products/select-by-supplier` | Seleccionar por proveedor/categoría |
| GET | `/api/supplier/{id}/products` | Productos de un proveedor |
| GET | `/api/supplier/{id}/categories` | Categorías con conteos |

### Productos Unificados
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/products-unified` | Productos por EAN (solo seleccionados) |
| GET | `/api/products-unified?include_all=true` | Todos los productos |

## Credenciales de Prueba
- **Email**: test@test.com
- **Password**: test123
- **Rol**: superadmin

## Historial de Cambios

### 25/02/2026
- ✅ Implementado nuevo flujo de selección de productos (Proveedores → Productos → Catálogos)
- ✅ Implementada página de configuración inicial para MongoDB y SuperAdmin
- ✅ Testing completo: Backend 100% (26/26), Frontend 100%

### Cambios Anteriores
- SuperAdmin role con gestión de límites
- Dashboard SuperAdmin con estadísticas globales
- Sistema de planes de suscripción editables
- Tiendas multi-plataforma (WooCommerce, PrestaShop, Shopify)
- Sistema de webhooks
- Fix de despliegue (endpoint /health)

## Próximas Tareas

### P2 - Prioridad Media
1. Completar refactorización de componentes compartidos
2. Verificar fix de bug FTP con datos reales
3. Integración SFTP

### P3 - Backlog
1. 2FA para mayor seguridad
2. Integración real con Wix y Magento
3. Expansión del dashboard SuperAdmin
