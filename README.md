# SyncStock

**SyncStock** es una plataforma SaaS B2B moderna para gestión y sincronización inteligente de catálogos de productos y proveedores. Permite a empresas de cualquier tamaño centralizar, sincronizar y publicar catálogos en múltiples canales de venta con reglas de precios y márgenes personalizados.

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación Rápida](#instalación-rápida)
- [Instalación Manual](#instalación-manual)
- [Configuración Inicial](#configuración-inicial)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Desarrollo Local](#desarrollo-local)
- [Despliegue en Producción](#despliegue-en-producción)
- [Integraciones](#integraciones)
- [API Endpoints](#api-endpoints)
- [Configuración Avanzada](#configuración-avanzada)
- [Troubleshooting](#troubleshooting)
- [Licencia](#licencia)

---

## ✨ Características

### Gestión de Proveedores
- ✅ Importar productos de múltiples fuentes (FTP, SFTP, HTTP, CSV, XLSX, XML)
- ✅ Sincronización automática con intervalos configurables
- ✅ Mapeo automático de columnas
- ✅ Validación y limpieza de datos
- ✅ Historial de sincronización y logs detallados

### Catálogos Personalizados
- ✅ Crear múltiples catálogos por empresa
- ✅ Definir reglas de margen de beneficio
- ✅ Filtrado y categorización de productos
- ✅ Precios personalizados por catálogo
- ✅ Exportación en múltiples formatos

### Sincronización Multi-Tienda
- ✅ **WooCommerce** — Sincronización bidireccional
- ✅ **Shopify** — Conectar y publicar catálogos
- ✅ **PrestaShop** — Sincronización de stock y precios
- ✅ Control de límites según plan de suscripción

### Integraciones CRM/ERP
- ✅ **Dolibarr** — Sincronización completa de productos, proveedores y órdenes
- ✅ **Odoo** — Integración con REST y XML-RPC
- ✅ Sincronización automática configurable
- ✅ Importación de órdenes y clientes

### Monitoreo de Competidores
- ✅ Seguimiento de precios de competidores en tiempo real
- ✅ Alertas de cambios de precio con umbral configurable
- ✅ Jobs de rastreo (crawl jobs) con paginación
- ✅ Catálogo de monitoreo configurable por usuario
- ✅ Reglas de automatización y simulaciones

### Monitoreo en Tiempo Real
- ✅ Dashboard con analíticas (productos, stock, ingresos)
- ✅ Notificaciones por WebSocket
- ✅ Alertas de stock bajo
- ✅ Historial de eventos y actividad

### Suscripciones y Facturación
- ✅ Planes configurables (Free, Starter, Pro, Enterprise)
- ✅ Límites por plan (proveedores, catálogos, tiendas, usuarios)
- ✅ Integración con Stripe para pagos
- ✅ Facturación automática y backups

### Seguridad
- ✅ Autenticación JWT con cookies seguras (httpOnly, Secure, SameSite)
- ✅ Control de acceso basado en roles (RBAC)
- ✅ Rate limiting en endpoints críticos
- ✅ Protección CSRF con middleware dedicado
- ✅ Cabeceras de seguridad HTTP (HSTS, CSP, X-Frame-Options)
- ✅ Encriptación de credenciales de terceros
- ✅ Logs de auditoría

---

## 🛠️ Stack Tecnológico

### Backend
| Componente | Tecnología |
|-----------|-----------|
| Framework | FastAPI 0.110+ |
| Servidor | Uvicorn |
| Base de datos | MongoDB (Motor async driver 3.3+) |
| Autenticación | JWT (PyJWT) + bcrypt |
| Planificador | APScheduler 3.11 |
| Validación | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Procesamiento de datos | Pandas, OpenPyXL, xmltodict |
| Conexiones FTP/SFTP | ftplib, Paramiko |
| E-commerce APIs | WooCommerce, Shopify, PrestaShop |
| Pagos | Stripe |
| Email | SMTP + Jinja2 |

### Frontend
| Componente | Tecnología |
|-----------|-----------|
| Framework | React 19.0.0 |
| Enrutamiento | React Router DOM 7 |
| Componentes UI | Radix UI (20+ paquetes) |
| Estilos | Tailwind CSS 3.4 |
| Formularios | React Hook Form + Zod |
| Gráficos | Recharts |
| Cliente HTTP | Axios |
| Notificaciones | Sonner |
| Arrastrar y soltar | DND Kit |

### Infraestructura
| Componente | Tecnología |
|-----------|-----------|
| Servidor web | Nginx |
| Proxy inverso | Nginx (para WebSocket y API) |
| Gestor de servicios | systemd |
| SO soportados | Ubuntu 20.04+, Debian 11+, CentOS 8+, Rocky Linux 8+ |

---

## 📦 Requisitos del Sistema

### Servidor
- **CPU**: 1 core (recomendado 2+)
- **RAM**: 1 GB mínimo (recomendado 2-4 GB)
- **Disco**: 10 GB libres (más para uploads de catálogos)
- **Puertos**: 80 (HTTP), 443 (HTTPS), 8001 (backend interno)

### Software
- **Node.js**: 20+ (para el frontend)
- **Python**: 3.9+
- **MongoDB**: 4.4+
- **Nginx**: 1.18+

### Opcional
- **Docker**: no requerido (despliegue directo en SO)

---

## 🚀 Instalación Rápida

La forma más fácil es usar el script de instalación automática. Ejecuta un único comando en tu servidor:

### Opción 1: Desde Git
```bash
git clone https://github.com/global-digitals/syncstock.git
cd SyncStock
sudo bash install.sh
```

### Opción 2: Desde URL
```bash
curl -sSL https://raw.githubusercontent.com/global-digitals/syncstock/master/install.sh | sudo bash
```

El script realizará automáticamente:
- ✅ Instalación de dependencias (Python 3, Node.js 20, MongoDB)
- ✅ Configuración del backend FastAPI
- ✅ Compilación del frontend React
- ✅ Configuración de Nginx y SSL
- ✅ Creación de almacenamiento persistente en `/etc/syncstock/`
- ✅ Habilitación del servicio systemd

### Después de la Instalación

1. **Abre tu navegador** en `https://tu-dominio.com` (o `http://localhost` si es local)
2. **Completa la configuración inicial** en el asistente de setup:
   - Configurar MongoDB
   - Crear usuario SuperAdmin
   - Configurar opciones generales
3. **¡Listo!** Comienza a gestionar tus catálogos

---

## 🔧 Instalación Manual

Si prefieres control total sobre el proceso de instalación, consulta la guía completa:

📖 [README-DEPLOY-PLESK.md](README-DEPLOY-PLESK.md)

Esta guía incluye:
- Instalación paso a paso de cada componente
- Configuración manual de Nginx
- Configuración de SSL/TLS
- Integración con Plesk (si aplica)

---

## ⚙️ Configuración Inicial

### 1. Accede al Asistente de Configuración

Después de instalar, la aplicación estará disponible en:
```
https://tu-dominio.com
```

Si es la primera vez, se redirigirá automáticamente al asistente de setup.

### 2. Paso 1: Configuración del Sistema

Configura la conexión a MongoDB:
- **MongoDB URL**: `mongodb://localhost:27017` (o tu servidor remoto)
- **Nombre de BD**: `syncstock_db`
- Prueba la conexión antes de continuar

### 3. Paso 2: Crear SuperAdmin

Crea la cuenta de administrador principal:
- **Nombre**
- **Email**
- **Empresa** (opcional)
- **Contraseña**

### 4. Paso 3: Configuración Avanzada (Opcional)

- **JWT Secret**: Generado automáticamente (personalizable)
- **CORS Origins**: Por defecto `*` (recomendado cambiar en producción)
- **Configuración SMTP**: Para envío de emails

### ✅ ¡Listo!

Una vez completado, accede al dashboard con tus credenciales de SuperAdmin.

---

## 📁 Estructura del Proyecto

```
SyncStock/
├── backend/
│   ├── routes/
│   │   ├── auth.py             # Autenticación y JWT
│   │   ├── suppliers.py        # Gestión de proveedores y sincronización
│   │   ├── products.py         # Inventario de productos
│   │   ├── catalogs.py         # Gestión de catálogos
│   │   ├── competitors.py      # Monitoreo de competidores y alertas
│   │   ├── woocommerce.py      # Integración WooCommerce
│   │   ├── stores.py           # Gestión multi-tienda
│   │   ├── dashboard.py        # Analíticas y métricas
│   │   ├── subscriptions.py    # Planes y facturación
│   │   ├── crm.py              # Integraciones Dolibarr/Odoo
│   │   ├── orders.py           # Gestión de órdenes
│   │   ├── marketplaces.py     # Integraciones de marketplaces
│   │   ├── stripe.py           # Pagos Stripe
│   │   ├── email.py            # Configuración SMTP
│   │   ├── webhooks.py         # Receptores de webhooks
│   │   ├── support.py          # Soporte técnico
│   │   ├── setup.py            # Configuración inicial
│   │   └── admin/              # Panel de superadministración
│   │       ├── branding.py     # Personalización de marca
│   │       ├── content.py      # Gestión de contenido
│   │       ├── email_templates.py
│   │       ├── integrations.py
│   │       ├── plans.py        # Gestión de planes
│   │       └── system.py       # Configuración del sistema
│   ├── repositories/           # Capa de acceso a datos (Repository Pattern)
│   │   ├── supplier_repository.py   # SupplierRepository (incl. atomic try_start_sync)
│   │   ├── product_repository.py    # ProductRepository
│   │   ├── catalog_repository.py    # CatalogRepository
│   │   ├── competitor_repository.py # CompetitorRepository, CrawlJobRepository,
│   │   │                            # UserMonitoringConfigRepository
│   │   ├── store_repository.py      # StoreRepository
│   │   ├── notification_repository.py # NotificationRepository
│   │   └── __init__.py         # Exportaciones centralizadas
│   ├── services/
│   │   ├── sync/               # Paquete de sincronización de proveedores
│   │   │   ├── downloaders.py  # Descargadores FTP/SFTP/HTTP/URL
│   │   │   ├── parsers.py      # Parseo CSV/XLSX/XLS/XML
│   │   │   ├── normalizer.py   # Normalización y limpieza de datos
│   │   │   ├── product_sync.py # Upsert de productos en MongoDB
│   │   │   ├── notifications.py # Disparadores de notificaciones de sync
│   │   │   ├── woocommerce_sync.py # Sincronización WooCommerce
│   │   │   ├── ftp_browser.py  # Navegación de directorios FTP
│   │   │   └── utils.py        # Utilidades compartidas de sync
│   │   ├── platforms/          # Integraciones de plataformas e-commerce
│   │   │   ├── base.py         # Clase base abstracta
│   │   │   ├── factory.py      # Factory pattern para plataformas
│   │   │   ├── shopify_client.py
│   │   │   ├── prestashop.py
│   │   │   ├── magento.py
│   │   │   └── wix.py
│   │   ├── crm_clients/        # Clientes CRM
│   │   │   ├── base.py         # Interfaz base CRM
│   │   │   ├── factory.py      # Factory pattern para CRM
│   │   │   ├── dolibarr.py     # Cliente Dolibarr REST
│   │   │   ├── odoo.py         # Cliente Odoo XML-RPC
│   │   │   └── basic_clients.py
│   │   ├── orders/             # Gestión de órdenes
│   │   │   ├── order_service.py
│   │   │   ├── order_sync.py
│   │   │   ├── normalizer.py
│   │   │   ├── models.py
│   │   │   └── retry_manager.py
│   │   ├── auth.py             # Lógica de autenticación y RBAC
│   │   ├── database.py         # Pool MongoDB e índices
│   │   ├── email_service.py    # Envío de emails con plantillas Jinja2
│   │   ├── config_manager.py   # Configuración persistente en /etc/syncstock/
│   │   ├── encryption.py       # Encriptación de credenciales de terceros
│   │   ├── cache.py            # Capa de caché
│   │   ├── error_monitor.py    # Monitor de errores
│   │   ├── crm_scheduler.py    # Jobs programados de sincronización CRM
│   │   ├── crm_sync.py         # Orquestación de sincronización CRM
│   │   ├── multi_store_sync.py # Sincronización multi-tienda
│   │   └── unified_sync.py     # Planificador general de sincronizaciones
│   ├── middleware/             # Middlewares de seguridad
│   │   ├── csrf.py             # Protección CSRF
│   │   ├── security_headers.py # Cabeceras HTTP de seguridad
│   │   └── uuid_validation.py  # Validación de UUIDs en rutas
│   ├── security_config/        # Configuración de seguridad
│   │   ├── cors.py             # Política CORS
│   │   └── rate_limits.py      # Límites de peticiones por endpoint
│   ├── models/                 # Esquemas Pydantic por dominio
│   │   ├── schemas.py          # Esquemas compartidos
│   │   ├── supplier.py
│   │   ├── product.py
│   │   ├── catalog.py
│   │   ├── store.py
│   │   ├── competitor.py
│   │   ├── subscription.py
│   │   └── user.py
│   ├── tests/                  # Suite de tests pytest (50+ archivos)
│   │   ├── conftest.py         # Fixtures compartidos
│   │   ├── test_repositories.py        # Tests del Repository Pattern
│   │   ├── test_sprint5_security.py    # Tests de seguridad
│   │   ├── test_catalogs.py
│   │   ├── test_products_sorting_price_history.py
│   │   ├── test_roles_users_websocket.py
│   │   ├── test_crm_dolibarr.py
│   │   ├── test_stores_multiplatform.py
│   │   ├── test_stripe_checkout_sftp.py
│   │   ├── test_competitors_unit.py
│   │   ├── test_url_connection.py
│   │   └── ... (40+ archivos de test más)
│   ├── server.py               # Punto de entrada FastAPI
│   ├── config.py               # Variables de configuración
│   ├── requirements.txt        # Dependencias Python
│   ├── DATABASE.md             # Esquema de MongoDB
│   └── uploads/                # Imágenes de productos
├── frontend/
│   ├── src/
│   │   ├── pages/              # Componentes de página (20+)
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Suppliers.jsx
│   │   │   ├── SupplierDetail.jsx  # 203 líneas (refactorizado)
│   │   │   ├── Products.jsx
│   │   │   ├── Catalogs.jsx
│   │   │   ├── Stores.jsx
│   │   │   ├── Competitors.jsx     # 268 líneas (refactorizado)
│   │   │   ├── CRM.jsx
│   │   │   └── ... (más páginas)
│   │   ├── components/         # Componentes reutilizables (72+)
│   │   │   ├── ui/             # Wrappers de Radix UI
│   │   │   ├── dialogs/        # Modales
│   │   │   ├── supplier/       # Componentes de detalle de proveedor
│   │   │   └── shared/         # Componentes comunes
│   │   ├── hooks/              # Hooks personalizados (14)
│   │   │   ├── useAsyncData.js          # Loading/error/data para llamadas async
│   │   │   ├── usePagination.js         # Lógica de paginación reutilizable
│   │   │   ├── useDialogState.js        # Estado de apertura/cierre de diálogos
│   │   │   ├── useCompetitorsCRUD.js    # CRUD de competidores
│   │   │   ├── useAlertsCRUD.js         # Alertas de precio CRUD + fetch
│   │   │   ├── useAutomationCRUD.js     # Reglas de automatización y simulación
│   │   │   ├── useCompetitorSupportData.js  # Crawl jobs, matches, dashboard, config
│   │   │   ├── useSupplierData.js       # 9 llamadas paralelas, paginación, filtros
│   │   │   ├── useProductSelectionHandlers.js  # 7 handlers de selección de productos
│   │   │   ├── useSupplierSyncHandlers.js      # Sync, preset, subida de archivos
│   │   │   ├── useCatalogHandlers.js    # Diálogo de selección y adición a catálogos
│   │   │   ├── useCustomIcons.js        # Iconos personalizados SVG
│   │   │   ├── useGoogleScripts.js      # Carga de scripts de Google
│   │   │   └── use-toast.js             # Hook de notificaciones toast
│   │   ├── contexts/           # Contextos React
│   │   │   └── SyncProgressContext.jsx  # Progreso de sincronización en tiempo real
│   │   ├── lib/                # Utilidades
│   │   ├── utils/              # Funciones auxiliares
│   │   ├── App.jsx             # Router + Auth Context + WebSocket Context
│   │   └── index.js            # Punto de entrada
│   ├── package.json
│   └── build/                  # Build de producción (gitignored)
├── landing/                    # Página de marketing
├── install.sh                  # Script de instalación automática
├── update.sh                   # Script de actualización
├── backend_test.py             # Suite de tests de integración
├── design_guidelines.json      # Especificación de diseño UI/UX
├── DATABASE.md                 # Referencia de esquema MongoDB
├── CLAUDE.md                   # Guía para asistentes IA
├── ODOO_INTEGRATION.md         # Documentación Odoo
├── README-DEPLOY-PLESK.md      # Guía de despliegue Plesk
└── README.md                   # Este archivo
```

---

## 💻 Desarrollo Local

### Requisitos Previos
- Python 3.9+
- Node.js 20+
- MongoDB 4.4+ (local o remoto)
- Git

### Setup Inicial

#### 1. Clonar el repositorio
```bash
git clone https://github.com/global-digitals/syncstock.git
cd SyncStock
```

#### 2. Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env (opcional)
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=syncstock_dev
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(64))")
CORS_ORIGINS=http://localhost:3000
EOF

# Iniciar servidor
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

El backend estará disponible en: `http://localhost:8001`

#### 3. Configurar el Frontend

```bash
cd frontend

# Instalar dependencias
npm install  # o: yarn install

# Crear archivo .env (opcional)
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Iniciar servidor de desarrollo
npm start  # o: yarn start
```

El frontend estará disponible en: `http://localhost:3000`

### Ejecutar Tests

```bash
# Tests del backend (pytest)
cd backend
pytest tests/
pytest tests/test_catalogs.py        # Módulo específico
pytest tests/ -v                     # Verbose
pytest tests/ -k "test_auth"         # Filtrar por nombre

# Tests de integración API
python backend_test.py

# Tests del frontend (opcional)
cd frontend
npm test  # o: yarn test
```

### Comandos Útiles

```bash
# Health check del backend
curl http://localhost:8001/health
curl http://localhost:8001/api/health

# Rebuildar frontend
cd frontend
npm run build
```

---

## 🚀 Despliegue en Producción

### Instalación Automática (Recomendado)

```bash
sudo bash install.sh
```

### Actualización sin Tiempo de Inactividad

```bash
sudo bash update.sh
```

El script preserva automáticamente:
- Configuración en `/etc/syncstock/config.json`
- Base de datos MongoDB
- Credenciales y secretos

### Configuración de Nginx en Plesk

**⚠️ IMPORTANTE**: Si usas Plesk, debes configurar manualmente los directives de Nginx:

1. Ve a **Plesk → Dominios → tu-dominio.com**
2. Haz clic en **"Apache & nginx Settings"**
3. En **"Additional nginx directives"**, añade:

```nginx
# API Backend - Proxy a FastAPI
location /api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
    proxy_send_timeout 300s;
}

# WebSocket - Notificaciones en tiempo real
location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 86400s;
}

# Health Check
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

4. Haz clic en **OK/Apply**

### Verificar Instalación

```bash
# Estado del servicio
sudo systemctl status syncstock-backend

# Ver logs
sudo journalctl -u syncstock-backend -f

# Health check
curl http://localhost:8001/health

# Información de configuración
curl http://localhost:8001/api/setup/config-info
```

### Variables de Entorno (Producción)

```env
# Base de datos
MONGO_URL=mongodb://user:pass@host:27017
DB_NAME=syncstock_prod

# JWT
JWT_SECRET=<cadena hex de 128 caracteres>
JWT_EXPIRATION_HOURS=168

# Seguridad
CORS_ORIGINS=https://tu-dominio.com
ALLOW_ORIGINS=https://tu-dominio.com

# Sincronización
PRICE_CHANGE_THRESHOLD_PERCENT=10
LOW_STOCK_THRESHOLD=5
SUPPLIER_SYNC_INTERVAL_HOURS=6
WOOCOMMERCE_SYNC_INTERVAL_HOURS=12

# SMTP (Email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-app
SMTP_FROM=noreply@tu-dominio.com

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Timeouts
MONGO_CONNECT_TIMEOUT_MS=5000
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
MONGO_MAX_POOL_SIZE=10
```

### Persistencia de Configuración

La configuración se guarda en `/etc/syncstock/config.json` (fuera del directorio de la app):

```bash
# Ver configuración
cat /etc/syncstock/config.json

# Ver backups automáticos
ls -la /etc/syncstock/backups/

# Recarga dinámica de configuración (sin reiniciar)
curl -X POST http://localhost:8001/api/setup/reload-database
```

---

## 🔗 Integraciones

### E-commerce

#### WooCommerce
- ✅ Sincronización bidireccional de productos
- ✅ Actualización de stock en tiempo real
- ✅ Sincronización de categorías
- **Documentación**: Ver `backend/routes/woocommerce.py`

#### Shopify
- ✅ Conectar tienda Shopify
- ✅ Publicar catálogos personalizados
- **Documentación**: Ver `backend/services/platforms/shopify_client.py`

#### PrestaShop
- ✅ Sincronización de stock y precios
- **Documentación**: Ver `backend/services/platforms/prestashop.py`

### CRM/ERP

#### Dolibarr
- ✅ Sincronización de productos y proveedores
- ✅ Importación de órdenes
- ✅ Gestión de almacenes y stock
- **Documentación**: Ver `backend/routes/crm.py`

#### Odoo
- ✅ Sincronización REST API
- ✅ XML-RPC para operaciones avanzadas
- ✅ Configuración de módulos
- 📖 **Documentación Completa**: [ODOO_INTEGRATION.md](ODOO_INTEGRATION.md)

### Pagos

#### Stripe
- ✅ Sesiones de checkout
- ✅ Webhooks de eventos
- ✅ Gestión de suscripciones
- **Documentación**: Ver `backend/routes/stripe.py`

---

## 📡 API Endpoints

### Autenticación
```
POST   /api/auth/register           Registrar usuario
POST   /api/auth/login              Iniciar sesión
POST   /api/auth/logout             Cerrar sesión
POST   /api/auth/refresh            Refrescar token JWT
GET    /api/auth/me                 Obtener usuario actual
POST   /api/auth/forgot-password    Solicitar reset de contraseña
POST   /api/auth/reset-password     Cambiar contraseña
```

### Proveedores
```
GET    /api/suppliers               Listar proveedores
POST   /api/suppliers               Crear proveedor
GET    /api/suppliers/{id}          Obtener detalles
PUT    /api/suppliers/{id}          Actualizar proveedor
DELETE /api/suppliers/{id}          Eliminar proveedor
POST   /api/suppliers/{id}/sync     Sincronizar proveedor (operación atómica)
GET    /api/supplier/{id}/products  Obtener productos del proveedor (paginado)
GET    /api/supplier/{id}/products/count  Total de productos con filtros
```

### Productos
```
GET    /api/products                Listar productos
GET    /api/products-unified        Búsqueda unificada con filtros avanzados
POST   /api/products/search         Búsqueda global
GET    /api/products/{id}           Obtener detalles
PUT    /api/products/{id}           Actualizar producto
DELETE /api/products/{id}           Eliminar producto
GET    /api/products/{id}/history   Historial de precios
POST   /api/products/select         Añadir productos a sección principal
POST   /api/products/deselect       Quitar productos de sección principal
POST   /api/products/select-by-supplier  Seleccionar por proveedor/categoría
GET    /api/products/category-hierarchy  Jerarquía de categorías
GET    /api/products/brands         Marcas disponibles por proveedor
```

### Catálogos
```
GET    /api/catalogs                Listar catálogos
POST   /api/catalogs                Crear catálogo
GET    /api/catalogs/{id}           Obtener detalles
PUT    /api/catalogs/{id}           Actualizar catálogo
DELETE /api/catalogs/{id}           Eliminar catálogo
GET    /api/catalogs/{id}/items     Listar ítems del catálogo
POST   /api/catalogs/{id}/products  Añadir productos al catálogo
POST   /api/catalogs/{id}/export    Exportar catálogo
```

### Competidores
```
GET    /api/competitors             Listar competidores
POST   /api/competitors             Crear competidor
PUT    /api/competitors/{id}        Actualizar competidor
DELETE /api/competitors/{id}        Eliminar competidor
GET    /api/competitors/crawl-jobs  Listar jobs de rastreo (paginado)
GET    /api/competitors/alerts      Listar alertas de precio
POST   /api/competitors/alerts      Crear alerta
GET    /api/competitors/automation  Reglas de automatización
POST   /api/competitors/automation  Crear regla de automatización
GET    /api/competitors/monitoring-config  Config de catálogo de monitoreo
PUT    /api/competitors/monitoring-config  Actualizar config de monitoreo
```

### Dashboard
```
GET    /api/dashboard/metrics       Analíticas principales
GET    /api/dashboard/products      Estadísticas de productos
GET    /api/dashboard/activity      Actividad reciente
GET    /api/dashboard/alerts        Alertas activas
```

### CRM
```
GET    /api/crm/connections         Listar conexiones CRM
POST   /api/crm/connections         Crear conexión
GET    /api/crm/connections/{id}    Obtener detalles
POST   /api/crm/connections/{id}/sync  Sincronizar
POST   /api/crm/connections/{id}/test  Test de conexión
```

### WebSocket
```
WS     /ws/notifications/{user_id}  Notificaciones en tiempo real
```

**Documentación API Completa**: Disponible en `http://tu-dominio.com/docs` (Swagger/OpenAPI)

---

## ⚙️ Configuración Avanzada

### Planificación de Sincronización

Configura intervalos automáticos en `backend/services/unified_sync.py`:

```python
SUPPLIER_SYNC_INTERVAL_HOURS = 6      # Sincronizar proveedores cada 6h
WOOCOMMERCE_SYNC_INTERVAL_HOURS = 12  # WooCommerce cada 12h
CRM_SYNC_INTERVAL_HOURS = 24          # CRM cada 24h
```

### Sincronización Atómica de Proveedores

El inicio de sincronización usa una operación atómica en MongoDB para evitar condiciones de carrera:

```python
# SupplierRepository.try_start_sync() — marca como "running" solo si no está ya corriendo
matched = await SupplierRepository.try_start_sync(supplier_id, user["id"])
if matched == 0:
    raise HTTPException(status_code=409, detail="Ya hay una sincronización en curso")
```

### Repository Pattern

Toda la lógica de acceso a MongoDB está encapsulada en `backend/repositories/`:

```python
# Uso en rutas — sin acceso directo a db.*
from repositories import SupplierRepository, ProductRepository

supplier = await SupplierRepository.get_by_id(supplier_id, user["id"])
products = await ProductRepository.get_paginated(filters, skip, limit)
```

### Rate Limiting

Configurado en `backend/security_config/rate_limits.py`. Para ajustar:

```python
# Ejemplo: 5 peticiones por minuto en /auth/register
@limiter.limit("5/minute")
```

### SMTP para Emails

En el panel de administración o en `/etc/syncstock/config.json`:

```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "tu-email@gmail.com",
  "smtp_password": "app-password",
  "smtp_from": "noreply@tu-dominio.com",
  "smtp_tls": true
}
```

### Control de Acceso Basado en Roles (RBAC)

| Rol | Proveedores | Catálogos | WooCommerce | Permisos Especiales |
|-----|-------------|-----------|-------------|---------------------|
| `superadmin` | Ilimitado | Ilimitado | Ilimitado | manage_users, manage_limits, unlimited |
| `admin` | 50 | 20 | 10 | manage_settings |
| `user` | 10 | 5 | 2 | CRUD estándar + sync |
| `viewer` | 0 | 0 | 0 | Solo lectura |

---

## 🔍 Troubleshooting

### El backend no inicia

```bash
# Ver logs detallados
sudo journalctl -u syncstock-backend -n 100

# Verificar que MongoDB está corriendo
sudo systemctl status mongod
mongo --eval "db.adminCommand('ping')"

# Verificar puerto 8001 está disponible
sudo lsof -i :8001
```

### Error 404 en `/api/*` (Plesk)

Asegúrate de haber configurado los directives de Nginx:
```bash
# Ver configuración actual
sudo nginx -T | grep -A 20 "location /api/"
```

Si no aparece, sigue los pasos en [Configuración de Nginx en Plesk](#configuración-de-nginx-en-plesk).

### WebSocket no conecta

Verifica que el proxy de WebSocket está configurado en Nginx:

```nginx
location /ws/ {
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### La base de datos no responde

```bash
# Conectar a MongoDB directamente
mongo <tu-mongo-url>

# Ver colecciones
db.getCollectionNames()

# Verificar usuario de autenticación
db.auth("usuario", "contraseña")
```

### Reiniciar servicios

```bash
# Reiniciar backend
sudo systemctl restart syncstock-backend

# Reiniciar Nginx
sudo systemctl restart nginx

# Reiniciar MongoDB
sudo systemctl restart mongod
```

### Ver archivo de configuración

```bash
# Mostrar configuración actual
cat /etc/syncstock/config.json

# Validar JSON
python3 -m json.tool < /etc/syncstock/config.json

# Ver permisos
ls -la /etc/syncstock/
```

---

## 📝 Convenciones de Código

### Python (Backend)
- snake_case para funciones y variables
- SCREAMING_SNAKE_CASE para constantes
- Pydantic v2 `BaseModel` para esquemas
- IDs: siempre strings UUID v4 (nunca MongoDB ObjectId)
- Async/await para operaciones de BD
- Exclusión de `_id` en respuestas API
- Repository Pattern para todo acceso a MongoDB

### JavaScript/React (Frontend)
- camelCase para variables y funciones
- PascalCase para componentes y clases
- Tailwind CSS para estilos (no CSS-in-JS)
- Iconos: Lucide React exclusivamente
- Notificaciones: Sonner (`toast.success`, `toast.error`)
- React Hook Form + Zod para formularios
- `useAsyncData` para gestión de loading/error en llamadas API

---

## 🤝 Contribución

Para contribuir al proyecto:

1. Crea una rama desde `master`: `git checkout -b feature/mi-funcionalidad`
2. Realiza tus cambios siguiendo las convenciones de código
3. Ejecuta los tests: `pytest tests/` (backend) o `npm test` (frontend)
4. Haz commit con mensajes descriptivos
5. Push a la rama y abre un Pull Request

**Nota**: Este proyecto no tiene CI/CD automatizado. Los despliegues son manuales.

---

## 📄 Licencia

Todos los derechos reservados © 2026 **Global-DigitalS**

---

## 📞 Soporte

Para problemas o preguntas:

1. Consulta la documentación: [CLAUDE.md](CLAUDE.md), [DATABASE.md](backend/DATABASE.md), [ODOO_INTEGRATION.md](ODOO_INTEGRATION.md)
2. Revisa los logs del servidor: `sudo journalctl -u syncstock-backend -f`
3. Verifica la sección [Troubleshooting](#troubleshooting)

---

**SyncStock** — Gestión Inteligente de Catálogos de Proveedores

Última actualización: 2026-04-17
