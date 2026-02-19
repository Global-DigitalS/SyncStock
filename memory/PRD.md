# StockHub - Product Requirements Document

## Problema Original
Software SaaS para gestión de catálogos de productos con proveedores:
- Descargar archivos de productos (CSV, Excel, XML, FTP)
- Ver precios, stocks y fichas de productos
- Crear múltiples catálogos personalizados sincronizados con proveedores
- Configurar precios de venta con reglas de márgenes por catálogo
- Exportar catálogo a Prestashop, WooCommerce, Shopify

## Preferencias del Usuario
- Formatos: CSV, Excel (XLSX/XLS), XML, FTP
- Autenticación: JWT
- Dashboard con estadísticas, historial de precios, notificaciones
- Diseño profesional/corporativo
- Idioma: Solo español

## Arquitectura
- **Backend**: FastAPI + MongoDB + WooCommerce API
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Auth**: JWT con bcrypt

## Funcionalidades Implementadas

### Backend
- [x] Autenticación JWT (registro/login)
- [x] CRUD de proveedores con configuración FTP/SFTP
- [x] Soporte para importar desde URL directa HTTP/HTTPS
- [x] Importación de productos (CSV, XLSX, XLS, XML)
- [x] Normalización automática de campos
- [x] **MÚLTIPLES CATÁLOGOS** con productos y reglas independientes
- [x] Reglas de margen por catálogo (porcentaje/fijo, por categoría/proveedor)
- [x] Exportación a Prestashop, WooCommerce, Shopify (CSV)
- [x] Dashboard con estadísticas
- [x] Historial de precios
- [x] Notificaciones de stock
- [x] Sincronización FTP/SFTP automática cada 12 horas (APScheduler)
- [x] Sincronización manual desde el frontend
- [x] Mapeo de columnas personalizado
- [x] Integración WooCommerce API REST
  - CRUD de configuraciones de tiendas
  - Test de conexión
  - Exportación directa seleccionando catálogo
  - Soporte para actualizar productos existentes por SKU

### Frontend
- [x] Login/Registro con diseño profesional
- [x] Dashboard con estadísticas y alertas
- [x] Gestión de proveedores con formulario de pestañas
- [x] Selector de tipo de conexión (FTP/SFTP o URL Directa)
- [x] Configuración FTP y CSV detallada
- [x] Detalle de proveedor con catálogo de productos
- [x] **NUEVA: Página Catálogos** (`Catalogs.jsx`)
  - Listado de catálogos con estadísticas
  - Crear/editar/eliminar catálogos
  - Configurar reglas de margen por catálogo
  - Badge de catálogo por defecto
- [x] **NUEVA: Detalle de Catálogo** (`CatalogDetail.jsx`)
  - Ver productos de un catálogo específico
  - Añadir/eliminar productos del catálogo
  - Búsqueda y filtros
- [x] **ACTUALIZADO: Exportar a WooCommerce** (`WooCommerceExport.jsx`)
  - Selector de catálogo a exportar
  - Indicador de productos a enviar
- [x] Reglas de margen configurables
- [x] Exportación a 3 plataformas (CSV)
- [x] Historial de precios
- [x] Centro de notificaciones

## Última Actualización: 19 Feb 2026

### Sesión Actual - Múltiples Catálogos
1. ✅ **Página Catalogs.jsx**: Gestión completa de múltiples catálogos
2. ✅ **Página CatalogDetail.jsx**: Ver y gestionar productos por catálogo
3. ✅ **WooCommerceExport.jsx actualizado**: Selector de catálogo antes de exportar
4. ✅ **App.js actualizado**: Rutas /catalogs, /catalogs/:catalogId, redirect /catalog
5. ✅ **Sidebar actualizado**: Navegación a Catálogos

### Testing
- Backend: 90.9% tests pasados
- Frontend: 100% flujos UI verificados
- Ver: /app/test_reports/iteration_5.json

## Próximas Tareas (P1)
- [ ] Sincronización de proveedores a catálogos específicos
- [ ] Integración API REST con Prestashop
- [ ] Integración API REST con Shopify

## Backlog (P2)
- [ ] Alertas por email
- [ ] Historial de cambios por producto
- [ ] API pública para integraciones externas
- [ ] Múltiples usuarios por cuenta
- [ ] Roles y permisos
- [ ] Refactorizar server.py en módulos separados

## Notas Técnicas
- El archivo antiguo `Catalog.jsx` puede eliminarse (la ruta /catalog redirige a /catalogs)
- Las colecciones de MongoDB usadas:
  - `catalogs`: Metadatos de catálogos
  - `catalog_items`: Productos en cada catálogo
  - `catalog_margin_rules`: Reglas de margen por catálogo
