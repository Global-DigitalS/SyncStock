# SupplierSync Pro - Product Requirements Document (PRD)

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos de productos desde FTP/SFTP o URL, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Estado Actual
**Versión:** 3.5.0  
**Última actualización:** 2026-03-07  
**Estado:** ✅ Producción - Funcionando en menuboard.es

---

## Cambios Recientes (2026-03-07)

### Webhook de Stripe - VERIFICADO
- ✅ Endpoint `/api/stripe/webhook` ya implementado y funcional
- Maneja eventos: `checkout.session.completed`, `checkout.session.expired`
- Activa suscripciones automáticamente al completar pago
- Verifica firma del webhook si está configurada
- Actualiza `payment_transactions` y aplica suscripción al usuario

### Landing Page Separada - NUEVO
- ✅ Creada aplicación independiente en `/app/landing/`
- Aplicación React standalone lista para desplegar en dominio separado
- Consume APIs del backend para contenido dinámico
- Configurable via `.env` para diferentes entornos
- README con instrucciones de despliegue (Vercel, Netlify, etc.)

### Configuración
- ✅ Añadida `STRIPE_API_KEY=sk_test_emergent` al backend

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

### Edición Completa de Productos (NUEVO - 2026-03-05)
- [x] **Campos de Edición Extendidos**
  - Nombre del producto
  - Descripción corta (short_description) - máximo 500 caracteres
  - Descripción larga (long_description) - sin límite
  - Marca (brand)
  - Imagen principal (image_url) - URL o upload
  - Imágenes secundarias/Galería (gallery_images) - array de URLs
- [x] **Endpoints de API**
  - PUT /api/products/{id} - Actualizar producto con todos los campos
  - POST /api/products/{id}/upload-image?image_type=main - Subir imagen principal
  - POST /api/products/{id}/upload-image?image_type=gallery - Añadir imagen a galería
  - DELETE /api/products/{id}/gallery-image?image_url=... - Eliminar de galería
- [x] **Componente ProductDetailDialog Mejorado**
  - 3 pestañas: Info/Proveedores, Editar, Imágenes
  - Pestaña Info: Muestra datos del producto y proveedores
  - Pestaña Editar: Nombre, marca, categoría, descripción corta/larga, precio, stock, etc.
  - Pestaña Imágenes: Vista previa de imagen principal, upload, galería con add/remove
- [x] **Integración en Páginas**
  - SupplierDetail.jsx: Diálogo completo al ver producto de proveedor
  - Products.jsx: Botón "Editar" para modificar producto del mejor proveedor
- [x] **Sincronización con Tiendas Online** (ACTUALIZADO - 2026-03-06)
  - **WooCommerce**: Exporta nombre, short_description, long_description, brand, images (principal + galería)
  - **NUEVO: Creación Automática de Categorías** - Ahora crea las categorías en WooCommerce automáticamente antes de exportar productos, soportando jerarquías con separador '>'
  - **NUEVO: Campo Personalizado Proveedor** - Añade campos `_supplier_name` y `supplier_name` con el nombre del proveedor de origen
  - **PrestaShop**: Exporta nombre, description, description_short, EAN, peso, imágenes (principal + galería)
  - **Shopify**: Exporta título, body_html, vendor (brand), categoría, SKU, EAN, peso, imágenes (principal + galería), metafields para short_description
  - **Magento**: Exporta nombre, short_description, description, marca (manufacturer), EAN, peso, imágenes (codificadas en base64)
  - **Wix**: Exporta nombre, descripción, marca, precio, SKU, peso, imágenes (principal + galería), additionalInfoSections para descripción corta

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
  - **Flujo de Pago Real con Stripe Checkout** (ACTUALIZADO)
    - Usa SDK oficial de Stripe (stripe==14.3.0)
    - Redirección a Stripe para pago seguro
    - Polling de estado de pago al regresar
    - Actualización automática de suscripción tras pago exitoso
    - Soporte para ciclos mensual y anual
    - Webhooks para procesar pagos completados
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

- [x] **Personalización/Branding** (`/admin/branding`) - ACTUALIZADO 2026-03-05
  - Nombre de la aplicación
  - Slogan/descripción
  - **Título de Página** (pestaña del navegador) - NUEVO
  - Logo y Favicon (upload de imágenes)
  - **Imagen Hero para Login/Registro** (upload de imagen) - NUEVO
  - **Texto Hero (título y subtítulo)** - NUEVO
  - Colores personalizados (primario, secundario, acento)
  - 7 Temas predefinidos: Índigo, Océano, Bosque, Atardecer, Real, Pizarra, Rosa
  - Vista previa en tiempo real
  - Texto del footer
  - Endpoints adicionales:
    - POST /api/admin/branding/upload-hero - Subir imagen Hero

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
- [x] Magento (REST API con soporte de imágenes base64)
- [x] Wix eCommerce (REST API completa)

### Integraciones CRM (ACTUALIZADO - 2026-03-06)
- [x] **Módulo CRM Completo** (`/crm`)
  - Menú "Conexiones" en el sidebar con:
    - Tiendas (movido desde el nivel principal)
    - CRM (nueva sección)
  - **Dolibarr ERP/CRM - IMPLEMENTACIÓN COMPLETA CON CORRECCIONES**:
    - DolibarrClient class completa con todos los métodos de API
    - Conexión vía API REST con header DOLAPIKEY
    - **Sincronización de Productos** (MEJORADO 2026-03-06):
      - Crear/actualizar productos (ref, label, description, price, stock, barcode, weight)
      - **NUEVO: Precio de compra** (`cost_price`) - El precio del proveedor se guarda como precio de compra
      - Descripciones cortas/largas combinadas en campo description
      - Marca y proveedor guardados en note_public
      - Upload de imágenes vía API documents/upload (base64)
    - **Sincronización de Stock** (MEJORADO 2026-03-06):
      - Movimientos de stock via /stockmovements
      - Calcula diferencia entre stock actual y deseado
      - **Contador de stocks sincronizados en respuesta**
      - Fallback a actualización directa del producto
    - **Sincronización de Proveedores** (MEJORADO 2026-03-06):
      - Crear/actualizar thirdparties con fournisseur=1
      - Mapeo de campos: name, email, phone, address, city, zip, country_code
      - Búsqueda por nombre para evitar duplicados
      - **NUEVO: Vinculación de productos a proveedores** con precio de compra
      - Guarda dolibarr_id en registro local
    - **Sincronización de Imágenes** (MEJORADO 2026-03-06):
      - Descarga imagen desde URL
      - Conversión a base64 con detección de formato (png, gif, jpg)
      - Upload a Dolibarr via documents/upload
      - **Contador de imágenes sincronizadas en respuesta**
    - **Importación de Pedidos** desde WooCommerce:
      - Obtiene pedidos processing/pending de tiendas WooCommerce
      - Mapea líneas de pedido con productos de Dolibarr por SKU
      - Guarda registro en crm_synced_orders para evitar reimportación
    - Estadísticas: productos, clientes, proveedores, pedidos
    - Prueba de conexión con mensaje de versión
    - 7 opciones de sincronización configurables: productos, stock, precios, descripciones, imágenes, proveedores, pedidos
  - **UI Frontend Completa**:
    - Página CRM.jsx con lista de conexiones en cards
    - Stats grid: productos, proveedores, clientes, pedidos
    - Quick sync expandible por tipo
    - Sync completo con diálogo de opciones
    - Formulario de configuración con campos de Dolibarr
    - Instrucciones para obtener API Key
  - Endpoints:
    - GET /api/crm/connections - Listar conexiones CRM con stats
    - POST /api/crm/connections - Crear conexión (test automático)
    - PUT /api/crm/connections/{id} - Actualizar conexión
    - DELETE /api/crm/connections/{id} - Eliminar conexión
    - POST /api/crm/test-connection - Probar conexión sin guardar
    - POST /api/crm/connections/{id}/sync - Sincronizar (all/products/suppliers/orders)
    - GET /api/crm/connections/{id}/orders - Listar pedidos sincronizados
    - GET /api/crm/auto-sync-permissions - Permisos de auto-sync del usuario

### Sincronización Unificada (ACTUALIZADO - 2026-03-06)
- [x] **Sistema de Sincronización Automática Unificada**
  - Un único intervalo configurable para TODOS los servicios: Proveedores, Tiendas y CRM
  - Intervalos disponibles: 1 hora, 6 horas, 12 horas, 24 horas
  - Configurable por SuperAdmin a nivel de plan de suscripción
  - **Campos en SubscriptionPlan**:
    - `auto_sync_enabled`: boolean - habilita/deshabilita auto-sync para el plan
    - `sync_intervals`: array [1, 6, 12, 24] - intervalos permitidos en horas
  - **Campos en User (sync_config)**:
    - `interval`: int - intervalo seleccionado (1, 6, 12, 24)
    - `sync_suppliers`: boolean - sincronizar proveedores
    - `sync_stores`: boolean - sincronizar tiendas
    - `sync_crm`: boolean - sincronizar CRM
    - `last_sync`: timestamp - última sincronización
    - `next_sync`: timestamp - próxima sincronización programada
  - **Servicio unified_sync.py**:
    - `get_user_sync_settings()`: Obtiene configuración y permisos del plan
    - `update_user_sync_settings()`: Actualiza configuración del usuario
    - `sync_user_suppliers()`: Sincroniza proveedores del usuario
    - `sync_user_stores()`: Sincroniza tiendas del usuario
    - `sync_user_crm()`: Sincroniza conexiones CRM del usuario
    - `run_user_sync()`: Ejecuta sincronización completa
    - `run_scheduled_syncs()`: Job que verifica y ejecuta syncs pendientes
  - **Endpoints**:
    - GET /api/sync/settings - Configuración actual del usuario
    - PUT /api/sync/settings - Actualizar configuración
    - POST /api/sync/run-now - Sincronización manual inmediata
  - **APScheduler**: Job `unified_sync` ejecuta cada hora
  - **UI Frontend**:
    - SyncSettings.jsx: Página de configuración con selector de intervalo y toggles por servicio
    - AdminPlans.jsx: Sección "Sincronización Automática" con switch e intervalos
    - Sidebar: Nuevo enlace "Sincronización"

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

### Completadas en esta sesión (Fork actual - 2026-03-06)
- [x] ✅ **Integración Dolibarr CRM Completa (P0)**
  - DolibarrClient con CRUD completo de productos, proveedores, pedidos
  - Sincronización de stock vía movimientos o directa
  - Upload de imágenes a Dolibarr (base64)
  - Importación de pedidos desde WooCommerce a Dolibarr
  - UI completa con opciones de sincronización
  - 100% tests passed (16/16 backend, frontend OK)

- [x] ✅ **Sincronización Unificada (P1)**
  - Un único intervalo para sincronizar TODO: Proveedores, Tiendas y CRM
  - Intervalos: 1h, 6h, 12h, 24h configurables por plan
  - Nueva página SyncSettings.jsx con configuración centralizada
  - SuperAdmin configura intervalos permitidos por plan
  - Scheduler ejecuta verificación cada hora
  - 100% tests passed (17/17 backend, frontend OK)

### Completadas en sesión anterior (2026-03-05)
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

### 2026-03-06 (Fork actual - Integración CRM Dolibarr)
- ✅ **Implementación Completa de Integración CRM con Dolibarr**
  - DolibarrClient class (líneas 23-510 en crm.py):
    - test_connection(): Prueba API con versión
    - CRUD de productos: get_products, get_product_by_ref/id, create_product, update_product
    - upload_product_image(): Sube imágenes base64 a Dolibarr
    - update_stock(): Actualiza stock via movimientos
    - CRUD de proveedores (thirdparties): get_suppliers, create_supplier, update_supplier
    - Pedidos: get_orders, get_supplier_orders, create_order, create_supplier_order
    - get_stats(): Estadísticas para cards de UI
  - Funciones de sincronización:
    - sync_products_to_dolibarr(): Sincroniza productos con todas las opciones
    - sync_suppliers_to_dolibarr(): Sincroniza proveedores
    - sync_orders_to_dolibarr(): Importa pedidos de WooCommerce a registro local
  - Frontend CRM.jsx: UI completa con cards, stats, sync options, diálogos
  - Sidebar actualizado: Menú "Conexiones" con Tiendas y CRM
  - Tests: 16/16 backend, 100% frontend pasados

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

### 2026-03-07
- ✅ **Verificado Webhook de Stripe**
  - Endpoint `/api/stripe/webhook` ya funcional
  - Maneja `checkout.session.completed` y `checkout.session.expired`
  - Activa suscripciones automáticamente
- ✅ **Landing Page Separada**
  - Creada `/app/landing/` como app React independiente
  - Lista para desplegar en dominio separado
  - README con instrucciones de despliegue
- ✅ Añadida `STRIPE_API_KEY` al backend
- ✅ **CRM: Selección de Catálogo Obligatoria**
  - Eliminada opción "Todos los productos"
  - Ahora es obligatorio seleccionar un catálogo para sincronizar
  - Botón deshabilitado si no hay catálogo seleccionado
  - Mensaje de advertencia visible
- ✅ **Landing Page: Logo y Favicon Dinámicos**
  - Carga automática del logo desde configuración de branding
  - Favicon dinámico desde `/api/branding/public`
  - Título de página personalizable
- ✅ **Landing Page: Tema Claro/Oscuro**
  - Toggle de tema en la barra de navegación
  - Persistencia en localStorage
  - Transiciones suaves entre temas
  - Diseño adaptado para ambos modos
- ✅ **Planes: Límite de Conexiones CRM**
  - Nuevo campo `max_crm_connections` en límites del plan
  - Visible en tarjetas de planes y formulario de edición
- ✅ **Planes: Ordenación Manual de Características**
  - Drag & drop para reordenar características
  - Flechas arriba/abajo como alternativa
  - Mensaje instructivo "Arrastra para reordenar"

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
