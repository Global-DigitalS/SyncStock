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

### Monitoreo en Tiempo Real
- ✅ Dashboard con analíticas (productos, stock, ingresos)
- ✅ Notificaciones por WebSocket
- ✅ Alertas de cambios de precio (con umbral configurable)
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
- ✅ Encriptación de credenciales de terceros
- ✅ Logs de auditoría

---

## 🛠️ Stack Tecnológico

### Backend
| Componente | Tecnología |
|-----------|-----------|
| Framework | FastAPI 0.110+ |
| Servidor | Uvicorn |
| Base de datos | MongoDB (Motor async driver) |
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
│   │   ├── suppliers.py        # Gestión de proveedores
│   │   ├── products.py         # Inventario de productos
│   │   ├── catalogs.py         # Gestión de catálogos
│   │   ├── woocommerce.py      # Integración WooCommerce
│   │   ├── stores.py           # Gestión multi-tienda
│   │   ├── dashboard.py        # Analíticas y metrics
│   │   ├── subscriptions.py    # Planes y facturación
│   │   ├── crm.py              # Integraciones Dolibarr/Odoo
│   │   ├── stripe.py           # Pagos Stripe
│   │   ├── email.py            # Configuración SMTP
│   │   ├── admin.py            # Panel de administración
│   │   ├── webhooks.py         # Receptores de webhooks
│   │   └── setup.py            # Configuración inicial
│   ├── services/
│   │   ├── auth.py             # Lógica de autenticación
│   │   ├── database.py         # Pool MongoDB y índices
│   │   ├── sync.py             # Sincronización de proveedores
│   │   ├── email_service.py    # Envío de emails
│   │   ├── config_manager.py   # Gestión de configuración
│   │   ├── platforms.py        # APIs de plataformas e-commerce
│   │   ├── crm_scheduler.py    # Sincronización CRM programada
│   │   └── unified_sync.py     # Orquestación de sincronizaciones
│   ├── models/
│   │   └── schemas.py          # Esquemas Pydantic
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_catalogs.py
│   │   ├── test_crm_dolibarr.py
│   │   ├── test_products_sorting_price_history.py
│   │   └── ... más tests
│   ├── server.py               # Punto de entrada FastAPI
│   ├── config.py               # Variables de configuración
│   ├── requirements.txt        # Dependencias Python
│   ├── DATABASE.md             # Esquema de MongoDB
│   └── uploads/                # Imágenes de productos
├── frontend/
│   ├── src/
│   │   ├── pages/              # Componentes de página (20+)
│   │   │   ├── Dashboard.js
│   │   │   ├── Suppliers.js
│   │   │   ├── Products.js
│   │   │   ├── Catalogs.js
│   │   │   ├── Stores.js
│   │   │   ├── CRM.js
│   │   │   └── ... más páginas
│   │   ├── components/         # Componentes reutilizables (72+)
│   │   │   ├── ui/             # Wrappers de Radix UI
│   │   │   ├── dialogs/        # Modales
│   │   │   └── shared/         # Componentes comunes
│   │   ├── hooks/              # Hooks personalizados
│   │   ├── lib/                # Utilidades
│   │   ├── utils/              # Funciones auxiliares
│   │   ├── App.js              # Router + Contextos
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

# Ver logs del backend en tiempo real
# (Accesible desde terminal con --reload)

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
- **Documentación**: Ver `backend/routes/stores.py`

#### PrestaShop
- ✅ Sincronización de stock y precios
- **Documentación**: Ver `backend/services/platforms.py`

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
POST   /api/suppliers/{id}/sync     Sincronizar provedor
GET    /api/suppliers/{id}/products Obtener productos del proveedor
```

### Productos
```
GET    /api/products                Listar productos
POST   /api/products/search         Búsqueda avanzada
GET    /api/products/{id}           Obtener detalles
PUT    /api/products/{id}           Actualizar producto
DELETE /api/products/{id}           Eliminar producto
GET    /api/products/{id}/history   Historial de precios
POST   /api/products/upload         Subir imagen
```

### Catálogos
```
GET    /api/catalogs                Listar catálogos
POST   /api/catalogs                Crear catálogo
GET    /api/catalogs/{id}           Obtener detalles
PUT    /api/catalogs/{id}           Actualizar catálogo
DELETE /api/catalogs/{id}           Eliminar catálogo
GET    /api/catalogs/{id}/items     Listar ítems del catálogo
POST   /api/catalogs/{id}/export    Exportar catálogo
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

### Alertas de Cambios de Precio

En `backend/config.py`:

```env
PRICE_CHANGE_THRESHOLD_PERCENT=10     # Alertar si cambia >10%
LOW_STOCK_THRESHOLD=5                 # Alertar si stock <5 unidades
```

### Rate Limiting

Configurado automáticamente. Para ajustar, ver `backend/server.py`:

```python
limiter = Limiter(key_func=get_remote_address)
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

### JavaScript/React (Frontend)
- camelCase para variables y funciones
- PascalCase para componentes y clases
- Tailwind CSS para estilos (no CSS-in-JS)
- Iconos: Lucide React exclusivamente
- Notificaciones: Sonner (`toast.success`, `toast.error`)
- React Hook Form + Zod para formularios

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

Última actualización: 2026-04-09
