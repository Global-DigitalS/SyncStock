# CLAUDE.md — Guía para Asistentes IA en StockHUB3

Este archivo proporciona contexto para asistentes IA (Claude Code, etc.) que trabajen en el código de StockHUB3.

---

## Descripción General del Proyecto

**StockHUB3** (también llamado "SupplierSync Pro") es una plataforma SaaS B2B para gestión y sincronización de catálogos de proveedores. Permite a las empresas:

- Agregar catálogos de productos de múltiples proveedores (FTP, SFTP, URL, CSV, XLSX, XML)
- Gestionar sincronización multi-tienda (WooCommerce, Shopify, PrestaShop)
- Integrar sistemas CRM (Dolibarr, Odoo)
- Publicar y exportar catálogos personalizados con reglas de margen y precios
- Monitorear historial de precios, niveles de stock y eventos de sincronización en tiempo real
- Procesar pagos vía Stripe

**Idioma**: La UI de la aplicación y la documentación interna están en español (`es`). Todo texto visible al usuario debe estar en español.

---

## Estructura del Repositorio

```
StockHUB3/
├── backend/                    # API REST con FastAPI (Python)
│   ├── routes/                 # 14 módulos de rutas API
│   ├── services/               # Lógica de negocio e integraciones
│   ├── models/                 # Esquemas Pydantic (schemas.py)
│   ├── tests/                  # Suites de pruebas pytest
│   ├── config.py               # Configuración de la app (vars de entorno + config.json)
│   ├── server.py               # Punto de entrada FastAPI
│   ├── requirements.txt        # Dependencias Python
│   ├── DATABASE.md             # Referencia del esquema MongoDB
│   └── uploads/                # Imágenes de productos subidas
├── frontend/                   # SPA React 19
│   ├── src/
│   │   ├── pages/              # 20+ componentes de página
│   │   ├── components/         # 72+ componentes reutilizables
│   │   │   ├── ui/             # Wrappers de Radix UI
│   │   │   ├── dialogs/        # Componentes de diálogo modal
│   │   │   └── shared/         # Componentes compartidos comunes
│   │   ├── hooks/              # Hooks personalizados de React
│   │   ├── lib/                # Utilidades
│   │   ├── utils/              # Funciones auxiliares
│   │   ├── App.js              # Router + Auth Context + WebSocket Context
│   │   └── index.js            # Punto de entrada
│   ├── package.json
│   └── build/                  # Salida del build de producción (en gitignore)
├── landing/                    # Página de marketing (React 18)
├── backend_test.py             # Runner de pruebas de integración API
├── install.sh                  # Script de instalación automatizada para Plesk
├── update.sh                   # Script de actualización sin tiempo de inactividad
├── design_guidelines.json      # Especificación del sistema de diseño UI/UX
├── ODOO_INTEGRATION.md         # Documentación de integración con Odoo CRM
└── README-DEPLOY-PLESK.md      # Guía de despliegue en Plesk
```

---

## Stack Tecnológico

### Backend
| Componente | Tecnología |
|-----------|-----------|
| Framework | FastAPI 0.110+ |
| Servidor | Uvicorn |
| Base de datos | MongoDB (Motor async driver 3.3+) |
| Autenticación | JWT (PyJWT), bcrypt |
| Planificador | APScheduler 3.11 |
| Validación | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Procesamiento de datos | Pandas, OpenPyXL, XlRd, xmltodict |
| FTP/SFTP | ftplib (stdlib), Paramiko |
| E-commerce | WooCommerce API, Shopify API |
| Pagos | Stripe |
| Email | SMTP + plantillas Jinja2 |
| Cliente HTTP | Requests, aiohttp |

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
| Fechas | date-fns |
| Exportación Excel | XLSX |
| Notificaciones | Sonner |
| Iconos | Lucide React |
| Herramienta de build | CRACO (override de CRA) |
| Arrastrar y soltar | DND Kit |

---

## Arquitectura

### Visión General del Sistema
```
SPA React (frontend)
    ↕ HTTPS + WebSocket
FastAPI (backend, puerto 8001)
    ↕ Motor (async)
MongoDB
```

### Módulos de Rutas del Backend (`backend/routes/`)

| Módulo | Prefijo | Responsabilidad Principal |
|--------|---------|--------------------------|
| `auth.py` | `/auth` | Registro, login, logout, JWT, recuperación de contraseña |
| `suppliers.py` | `/suppliers` | CRUD, sincronización FTP/URL, mapeo de columnas |
| `products.py` | `/products` | Inventario de productos, búsqueda, filtrado, subida de imágenes |
| `catalogs.py` | `/catalogs` | CRUD multi-catálogo, ítems, reglas de margen |
| `woocommerce.py` | `/woocommerce` | Conexiones y sincronización con tiendas WooCommerce |
| `stores.py` | `/stores` | Configuración de tiendas multi-plataforma |
| `dashboard.py` | `/dashboard` | Analíticas, métricas, actividad reciente |
| `subscriptions.py` | `/subscriptions` | Planes, facturación, control de límites |
| `crm.py` | `/crm` | Integración y sincronización con Dolibarr y Odoo |
| `email.py` | `/email` | Config SMTP, plantillas, envío de prueba |
| `stripe.py` | `/stripe` | Sesiones de checkout, webhooks |
| `admin.py` | `/admin` | Gestión de usuarios y planes por el superadmin |
| `webhooks.py` | `/webhooks` | Receptores de webhooks de terceros |
| `setup.py` | `/setup` | Asistente de configuración inicial, gestión de config |

**Endpoints especiales:**
- `GET /health` — Health check raíz
- `GET /api/health` — Health check de la API
- `WebSocket /ws/notifications/{user_id}` — Notificaciones en tiempo real

### Servicios del Backend (`backend/services/`)

| Servicio | Responsabilidad |
|---------|----------------|
| `auth.py` | Creación/validación de JWT, hashing bcrypt, comprobación de permisos RBAC |
| `database.py` | Pool de conexiones MongoDB, creación de índices |
| `sync.py` | Descargas FTP/URL, parseo CSV/XLSX/XML, upsert de productos, disparadores de notificaciones |
| `email_service.py` | Integración SMTP, plantillas de email con Jinja2 |
| `config_manager.py` | Config persistente en `/etc/suppliersync/config.json` |
| `platforms.py` | Integraciones con APIs de plataformas e-commerce |
| `crm_scheduler.py` | Jobs programados de sincronización CRM (Dolibarr, Odoo) |
| `unified_sync.py` | Planificación de sincronización de proveedores configurada por el usuario |

### Gestión de Estado en el Frontend

- **Auth Context** (`App.js`) — Objeto de usuario global, login/logout, estado del token
- **WebSocket Context** (`App.js`) — Conexión de notificaciones en tiempo real
- **Local Storage** — Persistencia de sesión (`localStorage.user`)
- **Estado de componente** — `useState` para formularios, modales, tablas
- **Interceptores de Axios** — Manejo automático de cookies JWT

---

## Colecciones MongoDB

Ver `backend/DATABASE.md` para detalles completos del esquema.

| Colección | Propósito |
|-----------|----------|
| `users` | Cuentas de usuario con roles |
| `suppliers` | Fuentes de datos FTP/SFTP/URL |
| `products` | Inventario de productos importados |
| `catalogs` | Definiciones de múltiples catálogos |
| `catalog_items` | Productos en catálogos con precios personalizados |
| `catalog_margin_rules` | Configuraciones de margen de beneficio por catálogo |
| `woocommerce_configs` | Conexiones a tiendas WooCommerce |
| `notifications` | Alertas del sistema (sync, stock, precios) |
| `price_history` | Historial de cambios de precio |
| `subscription_plans` | Definiciones de niveles de plan |
| `subscriptions` | Asignaciones de suscripciones a usuarios |
| `crm_connections` | Configuraciones de conexión Dolibarr/Odoo |

**Convención de IDs**: Todos los registros usan `id` como string UUID v4. El campo `_id` de MongoDB siempre se excluye de las respuestas de la API. Nunca usar MongoDB ObjectId para IDs a nivel de aplicación.

---

## Autenticación y Autorización

### Flujo JWT
1. El usuario inicia sesión → contraseña verificada con bcrypt
2. Se crea token JWT con `user_id`, `role`, expiración (7 días por defecto)
3. Token almacenado en cookie **httpOnly, Secure, SameSite=Lax**
4. El backend valida el token mediante la dependencia `get_current_user()` de FastAPI

### Control de Acceso Basado en Roles (RBAC)

| Rol | Proveedores | Catálogos | WooCommerce | Permisos Especiales |
|-----|-------------|-----------|-------------|---------------------|
| `superadmin` | Ilimitado | Ilimitado | Ilimitado | manage_users, manage_limits, manage_settings, unlimited |
| `admin` | 50 | 20 | 10 | manage_settings |
| `user` | 10 | 5 | 2 | CRUD estándar + sync + export |
| `viewer` | 0 | 0 | 0 | Solo lectura |

### Patrones de Seguridad
- Rate limit: 5 peticiones/minuto en `/auth/register`
- Rate limiting por endpoint via `SlowAPI`
- Contraseñas: validación mínima + hashing bcrypt
- Saneamiento de entrada en todos los inputs de usuario
- CORS: orígenes configurables (por defecto `*` en desarrollo)

---

## Variables de Entorno

### Backend
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=supplier_sync_db
JWT_SECRET=<cadena hex de 128 caracteres>
JWT_EXPIRATION_HOURS=168
CORS_ORIGINS=*
PRICE_CHANGE_THRESHOLD_PERCENT=10
LOW_STOCK_THRESHOLD=5
SUPPLIER_SYNC_INTERVAL_HOURS=6
WOOCOMMERCE_SYNC_INTERVAL_HOURS=12
MONGO_CONNECT_TIMEOUT_MS=5000
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
MONGO_MAX_POOL_SIZE=10
```

### Frontend
```env
REACT_APP_BACKEND_URL=https://tudominio.com
```

### Configuración Persistente
Almacenada en `/etc/suppliersync/config.json` (fuera del directorio de la app, sobrevive a actualizaciones).
Contiene: `mongo_url`, `db_name`, `jwt_secret`, `cors_origins`, credenciales SMTP.

---

## Comandos de Desarrollo

### Backend

```bash
# Instalar dependencias
cd backend
pip install -r requirements.txt

# Servidor de desarrollo
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Ejecutar tests
cd backend
pytest tests/

# Ejecutar tests de integración API
python backend_test.py
```

### Frontend

```bash
# Instalar dependencias
cd frontend
yarn install   # o: npm install

# Servidor de desarrollo
yarn start     # o: npm start

# Build de producción
yarn build     # o: npm build

# Ejecutar tests
yarn test      # o: npm test
```

### Producción (systemd)

```bash
# Gestión del servicio
sudo systemctl start suppliersync-backend
sudo systemctl stop suppliersync-backend
sudo systemctl restart suppliersync-backend
sudo systemctl status suppliersync-backend

# Ver logs
sudo journalctl -u suppliersync-backend -f

# Health checks
curl http://localhost:8001/health
curl http://localhost:8001/api/health
```

---

## Convenciones de Código

### Python (Backend)

- **Estilo**: snake_case para funciones, variables y nombres de módulos
- **Modelos**: Pydantic v2 `BaseModel` en `backend/models/schemas.py`
- **Rutas**: Un archivo por dominio funcional en `backend/routes/`
- **Dependencias**: Usar `Depends()` de FastAPI para auth (`get_current_user`), DB, servicios
- **IDs**: Siempre strings UUID v4, nunca MongoDB ObjectId
- **Respuestas API**: Excluir `_id`, siempre devolver `id`
- **Manejo de errores**: `raise HTTPException(status_code=..., detail="...")`
- **Async**: Todas las operaciones de base de datos usan `await` con el driver async Motor
- **Exclusión de campos**: Usar `response_model_exclude` o limpieza manual del dict para ocultar `_id`

```python
# Ejemplo: patrón estándar de ruta
@router.get("/{item_id}")
async def get_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    item = await db.collection.find_one({"id": item_id, "user_id": current_user["id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")
    item.pop("_id", None)  # Siempre eliminar _id de MongoDB
    return item
```

### JavaScript/React (Frontend)

- **Estilo**: camelCase para variables/funciones, PascalCase para componentes
- **Nombres de archivo**: PascalCase para componentes (`ProductCard.js`), camelCase para hooks (`useProducts.js`)
- **Llamadas API**: Axios con `withCredentials: true` para auth basada en cookies
- **Formularios**: React Hook Form + validación con esquema Zod
- **Toasts**: `import { toast } from "sonner"` — usar `toast.success()`, `toast.error()`
- **Iconos**: Lucide React (`import { NombreIcono } from "lucide-react"`)
- **Estilos**: Clases utilitarias de Tailwind CSS; usar `cn()` de `lib/utils` para clases condicionales
- **Componentes UI**: Preferir los wrappers de Radix UI existentes en `components/ui/`

```javascript
// Ejemplo: patrón estándar de llamada API
const fetchData = async () => {
  try {
    const response = await axios.get(`${backendUrl}/api/recurso`, {
      withCredentials: true,
    });
    setData(response.data);
  } catch (error) {
    toast.error("Error al cargar los datos");
    console.error(error);
  }
};
```

### Patrones de Diseño de API

- Convenciones REST: `GET` listar, `POST` crear, `GET /{id}` individual, `PUT /{id}` actualizar, `DELETE /{id}` eliminar
- Todas las rutas con prefijo `/api/` (montadas en `server.py`)
- Paginación: parámetros de query `skip` y `limit` (no cursor-based)
- Filtrado: parámetros de query (`?search=`, `?category=`, `?supplier_id=`)
- Ordenación: `?sort_by=campo&sort_order=asc|desc`

---

## Testing

### Tests del Backend (`backend/tests/`)

```bash
cd backend
pytest tests/
pytest tests/test_catalogs.py        # Módulo específico
pytest tests/ -v                     # Verbose
pytest tests/ -k "test_auth"         # Filtrar por nombre
```

Archivos de test cubren:
- `test_admin_panel.py` — Gestión de usuarios admin
- `test_catalogs.py` — CRUD de catálogos e ítems
- `test_crm_dolibarr.py` — Integración CRM
- `test_product_detail.py` — Operaciones de producto
- `test_products_sorting_price_history.py` — Ordenación e historial de precios
- `test_roles_users_websocket.py` — RBAC y WebSocket
- `test_stripe_checkout_sftp.py` — Stripe y SFTP
- `test_stores_multiplatform.py` — Sincronización multi-tienda
- `test_url_connection.py` — Conexiones de proveedores por URL
- Y más...

Los resultados de tests se archivan en `test_reports/` como archivos JSON.

### Tests de Integración

```bash
# Suite completa de tests de integración API
python backend_test.py
```

---

## Despliegue

### Entornos Objetivo
- Plesk Obsidian 18.0+ (principal)
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / Rocky Linux 8+
- Mínimo: 1 GB RAM, 10 GB disco, puertos 80/443/8001 abiertos

### Instalación
```bash
sudo bash install.sh   # Configuración automática completa
```

### Actualizaciones (sin tiempo de inactividad)
```bash
sudo bash update.sh    # Preserva /etc/suppliersync/config.json
```

### Configuración Nginx
- Archivos estáticos del frontend servidos desde Nginx
- Backend proxied en `/api/` → `http://127.0.0.1:8001`
- WebSocket proxied en `/ws/` → `http://127.0.0.1:8001`

### Sin Docker
El proyecto no está containerizado. Se despliega directamente en el SO host con Nginx + systemd + MongoDB.

---

## Archivos Clave para Tareas Comunes

| Tarea | Archivos Clave |
|-------|---------------|
| Añadir una nueva ruta API | `backend/routes/<nuevo>.py`, registrar en `backend/server.py` |
| Añadir un modelo Pydantic | `backend/models/schemas.py` |
| Añadir una nueva página | `frontend/src/pages/<NuevaPagina>.js`, añadir ruta en `frontend/src/App.js` |
| Añadir un componente UI | `frontend/src/components/ui/<Componente>.js` |
| Modificar esquema de BD | Actualizar colección + documentar en `backend/DATABASE.md` |
| Añadir variable de entorno | `backend/config.py` + docs de despliegue |
| Añadir plantilla de email | `backend/services/email_service.py` |
| Añadir un cron job | `backend/services/unified_sync.py` o `crm_scheduler.py` |
| Modificar auth/RBAC | `backend/services/auth.py` |
| Añadir un nuevo test | `backend/tests/test_<funcionalidad>.py` |

---

## Sistema de Diseño

Ver `design_guidelines.json` para la especificación completa. Puntos clave:

- **Fuente principal**: Sistema/Tailwind por defecto
- **Idioma de la UI**: Español (todas las etiquetas, mensajes y botones en `es`)
- **Librería de componentes**: Primitivos de Radix UI envueltos en `components/ui/`
- **Colores**: Colores semánticos de Tailwind (sin hex hardcodeado en JSX)
- **Iconos**: Lucide React exclusivamente
- **Notificaciones toast**: Sonner (`toast.success`, `toast.error`, `toast.warning`, `toast.info`)
- **Estados vacíos**: Usar `<EmptyState />` de `components/shared/`
- **Modales**: Usar `<Dialog>` de `components/ui/dialog`

---

## Errores Comunes a Evitar

1. **Nunca usar MongoDB ObjectId** como ID de aplicación — siempre usar strings UUID v4
2. **Siempre eliminar `_id`** de los documentos MongoDB antes de devolver en respuestas API
3. **Usar `withCredentials: true`** en todas las llamadas Axios — la auth es basada en cookies, no en headers
4. **Texto de UI en español** — todos los strings visibles al usuario deben estar en español
5. **Verificar límites de suscripción** antes de crear recursos (proveedores, catálogos, tiendas WooCommerce)
6. **Usar async/await** consistentemente en rutas Python — nunca usar llamadas síncronas bloqueantes con Motor
7. **No modificar la ruta `/etc/suppliersync/config.json`** — es la ubicación de configuración persistente
8. **Ejecutar `item.pop("_id", None)`** en cada documento MongoDB devuelto al cliente API
9. **Rate limiting** — tener en cuenta los decoradores SlowAPI al hacer pruebas con endpoints rápidamente
10. **El build del frontend no está en el repo** — ejecutar `yarn build` antes del despliegue

---

## Notificaciones en Tiempo Real por WebSocket

El backend mantiene un `ConnectionManager` que difunde notificaciones a los usuarios conectados.

- Endpoint: `ws://<host>/ws/notifications/{user_id}`
- Eventos: finalización de sync, cambios de precio, alertas de stock bajo, errores de importación
- Conexión del frontend gestionada en el WebSocket Context de `App.js`
- Reconexión: gestionada automáticamente por el frontend

---

## Integraciones CRM

### Dolibarr
- Integración REST API v1
- Sincroniza: productos, clientes, pedidos
- Config almacenada en la colección `crm_connections`
- Rutas: `backend/routes/crm.py`

### Odoo
- Protocolo XML-RPC
- Sincroniza: productos, partners, facturas
- Documentación detallada: `ODOO_INTEGRATION.md`
- Config almacenada en la colección `crm_connections`

---

## Sistema de Suscripciones y Límites

Verificar límites antes de crear recursos:

```python
# Patrón usado en todas las rutas
subscription = await get_user_subscription(user_id, db)
current_count = await db.suppliers.count_documents({"user_id": user_id})
if current_count >= subscription["max_suppliers"]:
    raise HTTPException(status_code=403, detail="Has alcanzado el límite de proveedores")
```

Los planes se almacenan en la colección `subscription_plans` y se asignan mediante la colección `subscriptions`.

---

## Flujo de Trabajo Git

- Rama principal: `master`
- Ramas de funcionalidades/IA: `claude/<descripcion>-<session-id>`
- Mensajes de commit: descriptivos, pueden estar en español
- Sin pipeline CI/CD — despliegue manual mediante scripts
