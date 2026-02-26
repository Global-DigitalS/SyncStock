# SupplierSync Pro - PRD

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos CSV de productos desde FTP/SFTP o URL, ver precios y stocks, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Usuarios y Roles
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **SuperAdmin** | Administrador global de la plataforma | Gestión de usuarios, límites de recursos, planes de suscripción, dashboard global, configuración SMTP |
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
- [x] Botón mostrar/ocultar contraseña en Login y Registro
- [x] Recuperación de contraseña vía email

#### Gestión de Proveedores
- [x] CRUD de proveedores (FTP, URL directa)
- [x] Sincronización automática de archivos CSV
- [x] Mapeo de columnas flexible
- [x] Historial de sincronizaciones
- [x] Detección de columnas en archivos CSV
- [x] Explorador FTP mejorado con test de conexión

#### Nuevo Flujo de Productos
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

#### Página de Configuración Inicial (/setup)
- [x] Paso 1: Configuración MongoDB y JWT
- [x] Paso 2: Creación de usuario SuperAdmin
- [x] Paso 3: Configuración SMTP (opcional) ✨ NUEVO
- [x] Test de conexión MongoDB
- [x] Test de conexión SMTP
- [x] Redirección automática si ya está configurado

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
- [x] **Email de notificación al cambiar de plan** ✨ NUEVO

#### Webhooks
- [x] Sistema de webhooks para eventos
- [x] Configuración de URLs de destino
- [x] Gestión de eventos (productos, tiendas, catálogos)

#### Sistema de Email
- [x] Configuración SMTP genérica
- [x] Email de bienvenida a nuevos usuarios
- [x] Email de recuperación de contraseña
- [x] **Email de cambio de suscripción** ✨ NUEVO
- [x] UI de configuración SMTP para SuperAdmin

### ✅ Refactorización (Completado)

#### Componentes Compartidos
- [x] `DataTablePagination` - Componente reutilizable de paginación
- [x] `SortableTableHead` - Encabezados de tabla ordenables
- [x] `EmptyState` - Estados vacíos para listas

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
│   │   ├── suppliers.py       # CRUD proveedores + FTP
│   │   ├── products.py        # CRUD productos + selección
│   │   ├── catalogs.py        # CRUD catálogos
│   │   ├── stores.py          # Tiendas multi-plataforma
│   │   ├── subscriptions.py   # Planes + email notificación
│   │   ├── webhooks.py        # Sistema de webhooks
│   │   ├── setup.py           # Configuración inicial + SMTP
│   │   ├── email.py           # Configuración y envío de emails
│   │   └── dashboard.py       # Estadísticas
│   ├── services/
│   │   ├── sync.py            # Sincronización FTP/URL
│   │   ├── auth.py            # JWT helpers
│   │   ├── config_manager.py  # Gestión config.json
│   │   ├── email_service.py   # Servicio SMTP
│   │   └── store_integrations.py  # Integraciones eCommerce
│   └── server.py              # Main app + health check
└── frontend/                   # React + TailwindCSS + Shadcn
    ├── src/
    │   ├── pages/
    │   │   ├── Setup.jsx      # Configuración inicial (3 pasos)
    │   │   ├── Products.jsx   # Productos (refactorizado)
    │   │   ├── Suppliers.jsx  # Lista de proveedores
    │   │   ├── SupplierDetail.jsx  # Detalle + selección
    │   │   ├── Stores.jsx     # Tiendas multi-plataforma
    │   │   ├── EmailConfig.jsx # Configuración SMTP
    │   │   ├── ForgotPassword.jsx
    │   │   ├── ResetPassword.jsx
    │   │   └── ...
    │   ├── components/
    │   │   ├── shared/        # Componentes reutilizables
    │   │   │   ├── DataTablePagination.jsx
    │   │   │   ├── SortableTableHead.jsx
    │   │   │   └── EmptyState.jsx
    │   │   └── ui/            # Shadcn components
    │   └── App.js
    └── ...
```

## APIs Principales

### Setup y Email
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/setup/status` | Estado de configuración |
| POST | `/api/setup/test-connection` | Test conexión MongoDB |
| POST | `/api/setup/configure` | Configurar app + SuperAdmin + SMTP |
| POST | `/api/email/test-connection` | Test conexión SMTP |
| GET, POST | `/api/email/config` | Configuración SMTP |
| POST | `/api/auth/forgot-password` | Solicitar reset de contraseña |
| POST | `/api/auth/reset-password` | Restablecer contraseña |

### Productos y Selección
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/products-unified` | Productos seleccionados por EAN |
| GET | `/api/products/selected-count` | Conteo de productos seleccionados |
| POST | `/api/products/select` | Seleccionar productos por IDs |
| POST | `/api/products/deselect` | Deseleccionar productos |

### Suscripciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/subscriptions/plans` | Lista de planes |
| POST | `/api/subscriptions/subscribe/{plan_id}` | Suscribirse (envía email) |
| GET | `/api/subscriptions/my` | Mi suscripción actual |

## Credenciales de Prueba
- **Email**: test@test.com
- **Password**: test123
- **Rol**: superadmin

## Historial de Cambios

### 26/02/2026 (Sesión actual)
- ✅ Añadido Paso 3 de configuración SMTP a página /setup
- ✅ Implementado envío de email al cambiar de plan de suscripción
- ✅ Refactorizado Products.jsx con componentes compartidos (DataTablePagination, SortableTableHead)
- ✅ Testing completo: Backend 100% (11/11), Frontend 100%

### 25/02/2026
- ✅ Implementado nuevo flujo de selección de productos
- ✅ Implementada página de configuración inicial
- ✅ Creado script de instalación automática
- ✅ Mejoras en conexión FTP
- ✅ Botón mostrar/ocultar contraseña
- ✅ Inicio de integración de email

## Próximas Tareas

### P2 - Prioridad Media
1. Verificar corrección del bug FTP con datos reales del usuario
2. Integración SFTP como fuente de datos
3. Selección múltiple de archivos en navegador FTP

### P3 - Backlog
1. 2FA para mayor seguridad
2. Integración real con Wix y Magento
3. Expansión del dashboard SuperAdmin
4. APIs directas de proveedores
