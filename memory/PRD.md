# SupplierSync Pro - Product Requirements Document (PRD)

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos de productos desde FTP/SFTP o URL, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Estado Actual
**Versión:** 2.2.0  
**Última actualización:** 2026-03-04  
**Estado:** ✅ Producción - Funcionando en menuboard.es

---

## Funcionalidades Implementadas

### Core
- [x] Autenticación JWT con sistema de roles (Viewer, User, Admin, SuperAdmin)
- [x] Gestión de proveedores con soporte FTP/URL
- [x] Importación de productos desde CSV con mapeo de columnas
- [x] **Reglas de Margen por Catálogo** (2026-03-04)
  - Cada catálogo tiene sus propias reglas de margen independientes
  - Soporte para porcentajes y cantidades fijas
  - Filtros por categoría, proveedor o marca
  - Tramos de precios (precio mínimo y máximo)
  - Sistema de prioridades
- [x] **Categorías de Catálogo** (NUEVO - 2026-03-04)
  - Sistema jerárquico de categorías y subcategorías (máximo 4 niveles)
  - Un producto puede pertenecer a múltiples categorías
  - Ordenación de categorías (mover arriba/abajo)
  - Filtrado de productos por categoría
  - Asignación de categorías desde el detalle del catálogo
- [x] Exportación de catálogos a CSV
- [x] Unificación de productos por EAN
- [x] Paginación y ordenación en listas

### Integraciones eCommerce
- [x] WooCommerce (API REST completa)
- [x] PrestaShop (via prestapyt)
- [x] Shopify (via ShopifyAPI)
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

### P1 - Alta Prioridad
- [ ] Ampliar fuentes de datos: SFTP y APIs directas
- [ ] Selección múltiple de archivos en navegador FTP

### P2 - Media Prioridad
- [ ] Completar integración Wix eCommerce
- [ ] Completar integración Magento

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
