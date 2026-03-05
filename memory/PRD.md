# SupplierSync Pro - Product Requirements Document (PRD)

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos de productos desde FTP/SFTP o URL, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Estado Actual
**Versión:** 3.1.0  
**Última actualización:** 2026-03-05  
**Estado:** ✅ Producción - Funcionando en menuboard.es

---

## Funcionalidades Implementadas

### Core
- [x] Autenticación JWT con sistema de roles (Viewer, User, Admin, SuperAdmin)
- [x] **Recuperación de Contraseña** (2026-03-05)
  - Solicitud de reset: POST /api/auth/forgot-password
  - Reset con token: POST /api/auth/reset-password
  - Tokens con expiración de 1 hora
  - Email con plantilla HTML profesional
  - Protección contra enumeración de emails
  - Páginas: /forgot-password y /forgot-password?token=xxx
- [x] **Mensajes de Error Inteligentes en Login** (2026-03-05)
  - Usuario no encontrado: Sugerencia para registrarse o verificar email
  - Contraseña incorrecta: Sugerencia para recuperar contraseña
  - Backend diferencia errores: USER_NOT_FOUND, INVALID_PASSWORD
- [x] Gestión de proveedores con soporte FTP/SFTP/FTPS/URL
- [x] **Soporte Completo SFTP** (NUEVO - 2026-03-05)
  - Protocolo SFTP vía paramiko
  - Navegación de directorios SFTP
  - Descarga de archivos desde SFTP
  - Prueba de conexión SFTP
- [x] Importación de productos desde CSV con mapeo de columnas
- [x] **Reglas de Margen por Catálogo** (2026-03-04)
  - Cada catálogo tiene sus propias reglas de margen independientes
  - Soporte para porcentajes y cantidades fijas
  - Filtros por categoría, proveedor o marca
  - Tramos de precios (precio mínimo y máximo)
  - Sistema de prioridades
- [x] **Categorías de Catálogo** (2026-03-04)
  - Sistema jerárquico de categorías y subcategorías (máximo 4 niveles)
  - Un producto puede pertenecer a múltiples categorías
  - Ordenación de categorías (mover arriba/abajo)
  - Filtrado de productos por categoría
  - Asignación de categorías desde el detalle del catálogo
- [x] **Asignación Masiva de Categorías** (2026-03-04)
  - Selección múltiple de productos en vista de catálogo
  - Botón "Asignar a Categorías" que aparece al seleccionar productos
  - 3 modos de asignación: Añadir, Reemplazar, Quitar
  - Diálogo con selector de modo y categorías jerárquicas
  - Endpoint: POST /api/catalogs/{catalog_id}/products/bulk-categories
- [x] **Drag & Drop para Categorías** (2026-03-04)
  - Reordenación de categorías mediante arrastrar y soltar
  - Usa librería @dnd-kit/core y @dnd-kit/sortable
  - Indicadores visuales durante el arrastre
- [x] **Exportación de Categorías a Tiendas** (2026-03-04)
  - Endpoint: POST /api/stores/configs/{config_id}/export-categories
  - Soporte para WooCommerce (completo)
  - Soporte para PrestaShop (categorías jerárquicas)
  - Soporte para Shopify (como colecciones)
  - UI integrada en diálogo de categorías
- [x] Exportación de catálogos a CSV
- [x] Unificación de productos por EAN
- [x] Paginación y ordenación en listas

### Navegador FTP/SFTP (ACTUALIZADO - 2026-03-05)
- [x] **Selección Múltiple de Archivos** (NUEVO - 2026-03-05)
  - Botón "Múltiple" para activar modo de selección múltiple
  - Checkboxes en cada archivo soportado
  - "Seleccionar todos" para marcar todos los archivos soportados
  - Botón "Añadir (N)" para agregar todos los archivos seleccionados
  - Barra de acciones con contador de selección
- [x] Navegación de directorios
- [x] Soporte para FTP, FTPS y SFTP
- [x] Buscar en subcarpetas (máximo 3 niveles)
- [x] Indicadores de archivos soportados (CSV, XLSX, XLS, XML)

### Panel de Administración SuperAdmin (ACTUALIZADO - 2026-03-05)
- [x] **Sección de Administración en Sidebar** (visible solo para SuperAdmin)
  - **Administración** (link directo a Dashboard Admin)
  - Usuarios
  - Suscripciones (renombrado de "Planes")
  - **Config. Stripe**
  - Personalización (Branding)
  - Config. Email
  - Plantillas Email

- [x] **Integración Stripe Completa** (ACTUALIZADO - 2026-03-05)
  - Ubicación: Administración → Config. Stripe (`/admin/stripe`)
  - Configuración de claves API (Pública, Secreta, Webhook Secret)
  - Switch para habilitar/deshabilitar pagos
  - Switch para modo producción (pagos reales)
  - Prueba de conexión con Stripe API
  - **Flujo de Pago Real con Stripe Checkout** (NUEVO)
    - Usa emergentintegrations para crear sesiones de checkout
    - Redirección a Stripe para pago seguro
    - Polling de estado de pago al regresar
    - Actualización automática de suscripción tras pago exitoso
    - Soporte para ciclos mensual y anual
  - Endpoints:
    - GET /api/stripe/config/status - Estado público de Stripe (enabled/configured)
    - GET /api/admin/stripe/config - Obtener configuración (SuperAdmin)
    - PUT /api/admin/stripe/config - Actualizar configuración (SuperAdmin)
    - POST /api/admin/stripe/test-connection - Probar conexión
    - POST /api/stripe/create-checkout - Crear sesión de checkout (auth requerido)
    - GET /api/stripe/checkout-status/{session_id} - Verificar estado de pago
    - POST /api/stripe/webhook - Webhook para eventos de Stripe
    - GET /api/stripe/plans - Listar planes disponibles
    - GET /api/stripe/my-subscription - Obtener suscripción del usuario

- [x] **Reiniciar Aplicación (Zona de Peligro)** (2026-03-04)
  - Ubicación: Dashboard Admin (`/admin/dashboard`) - Sección "Zona de Peligro"
  - Permite al SuperAdmin borrar TODA la base de datos excepto los usuarios
  - Botón "Reiniciar App" con confirmación obligatoria
  - Diálogo de confirmación que requiere escribir "RESET" exactamente
  - Lista de datos que serán eliminados (proveedores, productos, catálogos, tiendas, etc.)
  - Los usuarios se preservan para mantener el acceso
  - Endpoint: POST /api/admin/system/reset (requiere `{"confirmation_text": "RESET"}`)
  - Registro de auditoría (quién ejecutó y cuándo)

- [x] **Personalización/Branding** (`/admin/branding`)
  - Nombre de la aplicación
  - Slogan/descripción
  - Logo y Favicon (upload de imágenes)
  - Colores personalizados (primario, secundario, acento)
  - 7 Temas predefinidos: Índigo, Océano, Bosque, Atardecer, Real, Pizarra, Rosa
  - Vista previa en tiempo real
  - Texto del footer

- [x] **Gestión de Suscripciones** (`/admin/subscriptions`) - Renombrado de "Planes"
  - CRUD completo de planes de suscripción
  - Configuración de límites (proveedores, catálogos, productos, tiendas)
  - Precios mensuales y anuales
  - Lista de características por plan
  - Marcar plan como predeterminado

- [x] **Cuentas de Email Múltiples** (NUEVO - 2026-03-05)
  - Ubicación: Administración → Config. Email (`/admin/email-config`)
  - 3 tipos de cuentas independientes:
    - **Transaccional**: Registro, reset de contraseña, notificaciones del sistema
    - **Soporte**: Comunicación con usuarios, tickets de soporte
    - **Facturación**: Facturas, confirmaciones de pago, cambio de plan
  - Cada cuenta con su propia configuración SMTP
  - Switch para habilitar/deshabilitar cada cuenta
  - Fallback automático a cuenta Transaccional si otra no está habilitada
  - Prueba de conexión y envío de email de prueba por cuenta
  - Endpoints:
    - GET /api/email/accounts - Obtener todas las configuraciones
    - PUT /api/email/accounts/{type} - Actualizar configuración
    - POST /api/email/accounts/{type}/test-connection - Probar conexión
    - POST /api/email/accounts/{type}/send-test - Enviar email de prueba

- [x] **Plantillas de Email** (`/admin/email-templates`)
  - 3 plantillas predeterminadas (Bienvenida, Reset Password, Cambio Suscripción)
  - Editor HTML con syntax
  - Variables disponibles: {name}, {email}, {app_name}, {app_url}, {primary_color}, etc.
  - Vista previa renderizada
  - Opción de restablecer a valores predeterminados
  - Posibilidad de crear nuevas plantillas

### Integraciones eCommerce
- [x] WooCommerce (API REST completa + exportación de categorías)
- [x] PrestaShop (via prestapyt + exportación de categorías)
- [x] Shopify (via ShopifyAPI + colecciones)
- [ ] Wix eCommerce (solo UI/modelo)
- [ ] Magento (solo UI/modelo)

### Sistema de Configuración (Actualizado 2026-03-03)
- [x] **Configuración persistente** en `/etc/suppliersync/config.json`
- [x] **Migración automática** de configuración antigua
- [x] **Backups automáticos** en `/etc/suppliersync/backups/`
- [x] **Scripts de instalación/actualización** que preservan configuración
- [x] Endpoints de gestión de configuración:
  - `GET /api/setup/status` - Estado de configuración
  - `GET /api/setup/config-info` - Info de ubicación de config
  - `POST /api/setup/backup` - Crear backup
  - `GET /api/setup/backups` - Listar backups

### Administración
- [x] Dashboard SuperAdmin con estadísticas
- [x] Gestión de usuarios y límites de recursos
- [x] Gestión de planes de suscripción
- [x] Configuración SMTP para emails transaccionales
- [x] Logs de sincronización e historial

---

## Despliegue en Producción (Plesk)

### Configuración Actual
- **Dominio:** menuboard.es
- **Backend:** FastAPI en puerto 8001 (systemd service)
- **Frontend:** React build en `/var/www/vhosts/menuboard.es/app/frontend/build`
- **MongoDB:** Docker container con autenticación
- **Configuración:** `/etc/suppliersync/config.json` (persistente)

### IMPORTANTE: Configuración de Nginx en Plesk
Plesk NO carga automáticamente `nginx_custom.conf`. Se debe configurar manualmente:

1. Plesk → Dominios → menuboard.es → Apache & nginx Settings
2. Sección "Additional nginx directives"
3. Añadir configuración de proxy para `/api/` y `/health`

---

## Tareas Pendientes

### Completadas en esta sesión (Fork actual - 2026-03-05)
- [x] ✅ **Integración Stripe Completa en Suscripciones (P0)**
  - Checkout sessions con emergentintegrations
  - Redirección a Stripe para pago seguro
  - Polling de estado de pago
  - Actualización automática de suscripción
  - Soporte para billing mensual y anual
  - 100% tests passed (12/12 backend, frontend OK)

- [x] ✅ **Soporte SFTP (P1)**
  - Protocolo SFTP via paramiko
  - Navegación y descarga de archivos
  - Integrado en prueba de conexión
  - Soporta FTP, FTPS y SFTP

- [x] ✅ **Selección Múltiple en Navegador FTP (P2)**
  - Botón "Múltiple" para activar modo
  - Checkboxes por archivo
  - "Seleccionar todos" y "Añadir" masivo
  - Barra de acciones con contador

### Completadas en sesión anterior (2026-03-04/05)
- [x] ✅ Asignación masiva de categorías a productos
- [x] ✅ Exportación de categorías a tiendas online
- [x] ✅ Panel de Administración SuperAdmin completo
- [x] ✅ Recuperación de contraseña
- [x] ✅ Mensajes de error inteligentes en login
- [x] ✅ Sistema multi-email para SuperAdmin

### P2 - Media Prioridad
- [ ] Completar integración Wix eCommerce
- [ ] Completar integración Magento
- [ ] APIs directas como fuentes de datos

### P3 - Baja Prioridad
- [ ] Autenticación de dos factores (2FA)
- [ ] Ampliar dashboard SuperAdmin con más estadísticas
- [ ] Webhooks para notificaciones de eventos

---

## Arquitectura

```
/var/www/vhosts/menuboard.es/app/
├── backend/
│   ├── routes/          # Endpoints API
│   ├── services/        # Lógica de negocio
│   ├── models/          # Esquemas Pydantic
│   └── server.py        # Entrada FastAPI
├── frontend/
│   ├── src/pages/       # Páginas React
│   ├── src/components/  # Componentes
│   └── build/           # Producción
├── install.sh           # Instalación inicial
├── update.sh            # Actualizaciones
└── README.md

/etc/suppliersync/        # Configuración persistente
├── config.json          # Config principal
└── backups/             # Backups automáticos
```

---

## Credenciales de Prueba
- **Email:** test@test.com
- **Password:** test123
- **Rol:** superadmin

---

## Historial de Cambios

### 2026-03-04 (Fork actual - Asignación Masiva de Categorías)
- ✅ **Asignación Masiva de Categorías a Productos**
  - Nuevo modelo Pydantic: `BulkCategoryAssignment`
  - Nuevo endpoint: `POST /api/catalogs/{catalog_id}/products/bulk-categories`
  - 3 modos de asignación:
    - `add`: Añade categorías a las existentes (usa $addToSet para evitar duplicados)
    - `replace`: Reemplaza todas las categorías por las seleccionadas
    - `remove`: Elimina las categorías seleccionadas de los productos
  - Frontend: Botón "Asignar a Categorías" aparece al seleccionar productos
  - Frontend: Diálogo con selector de modo y categorías jerárquicas
  - Tests: 15/15 backend, 100% frontend (testing_agent_v3_fork)

### 2026-03-04 (Sesión actual - Parte 2)
- ✅ **Sistema de Categorías por Catálogo**
  - CRUD completo de categorías (crear, leer, actualizar, eliminar)
  - Jerarquía de hasta 4 niveles (Categoría > Subcategoría > Sub-sub > ...)
  - Un producto puede pertenecer a múltiples categorías
  - Reordenación de categorías (subir/bajar)
  - Filtrado de productos por categoría en detalle del catálogo
  - Asignación de categorías desde icono de etiqueta en cada producto
  - Backend: 9 nuevos endpoints para gestión de categorías
  - Frontend: Nuevo componente `CatalogCategories.jsx`
  - Tests: 19/19 backend, 100% frontend

### 2026-03-04 (Sesión actual - Parte 1)
- ✅ **Reglas de Margen movidas a nivel de Catálogo**
  - Eliminada la sección global "Reglas de Margen" del menú lateral
  - Las reglas ahora se configuran dentro de cada catálogo
  - Añadidos campos para tramos de precios (min_price, max_price)
  - UI mejorada con selectores de categorías y proveedores
  - Funcionalidad de edición de reglas existentes
  - Nuevo endpoint PUT `/api/catalogs/{catalog_id}/margin-rules/{rule_id}`
- ✅ Ruta `/margin-rules` ahora redirige a `/catalogs`
- ✅ Validados scripts de despliegue multi-dominio (confirmado por usuario)
- ✅ Verificada conexión FTP (confirmado por usuario)

### 2026-03-04 (Fork anterior)
- ✅ Solucionado problema de instalación en subdominios de Plesk
- ✅ Actualizado `install.sh` para detectar automáticamente subdominios (ej: app.sync-stock.com)
- ✅ Añadido soporte para múltiples instalaciones con puertos dinámicos (8001, 8002, etc.)
- ✅ Cada instalación ahora tiene su propio servicio systemd con nombre único
- ✅ Configuración persistente ahora separada por dominio (`/etc/suppliersync/DOMINIO/`)
- ✅ Mejorado el sistema de recarga de conexión MongoDB (`reload_database_config()`)
- ✅ Nuevo endpoint `POST /api/setup/reload-database` para recargar config sin reiniciar

### 2026-03-03
- ✅ Solucionado problema de configuración de nginx en Plesk
- ✅ Actualizados scripts install.sh y update.sh con instrucciones claras
- ✅ Actualizado README.md con sección de configuración de Plesk
- ✅ Verificada conexión a MongoDB en producción
- ✅ Confirmado sistema de configuración persistente funcionando

### 2026-03-02
- ✅ Implementado sistema de configuración persistente
- ✅ Creado script update.sh para actualizaciones seguras
- ✅ Añadidos endpoints de backup de configuración
