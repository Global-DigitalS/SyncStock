# StockHub - Product Requirements Document

## Problema Original
Software SaaS para gestión de catálogos de productos con proveedores:
- Descargar archivos de productos (CSV, Excel, XML, FTP)
- Ver precios, stocks y fichas de productos
- Crear catálogo propio sincronizado con proveedores
- Configurar precios de venta con reglas de márgenes
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
- [x] **NUEVO: Soporte para importar desde URL directa HTTP/HTTPS**
- [x] Importación de productos (CSV, XLSX, XLS, XML)
- [x] Normalización automática de campos
- [x] Catálogo personal con precios personalizados
- [x] Reglas de margen (porcentaje/fijo, por categoría/proveedor)
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
  - Exportación directa de productos vía API
  - Soporte para actualizar productos existentes por SKU

### Frontend
- [x] Login/Registro con diseño profesional
- [x] Dashboard con estadísticas y alertas
- [x] Gestión de proveedores con formulario de pestañas
- [x] **Selector de tipo de conexión (FTP/SFTP o URL Directa)**
- [x] Configuración FTP (schema, host, port, user, password, path, modo)
- [x] Configuración CSV (separador, enclosure, header row, formato)
- [x] Detalle de proveedor con catálogo de productos
- [x] Selección múltiple para añadir al catálogo
- [x] Productos con filtros (búsqueda, categoría, stock)
- [x] Mi Catálogo con filtros por proveedor/estado y estadísticas
- [x] Reglas de margen configurables
- [x] Exportación a 3 plataformas (CSV)
- [x] Historial de precios con gráficos
- [x] Centro de notificaciones
- [x] Página WooCommerce Export
- [x] Componente ColumnMappingDialog para mapeo visual de columnas
  - Añadir/editar/eliminar tiendas
  - Probar conexión
  - Exportar productos directamente
  - Estadísticas de sincronización
- [x] **NUEVO: Componente ColumnMappingDialog** para mapeo visual de columnas

## Última Actualización: 19 Feb 2026

### Tareas P1 Completadas (Sesión Actual)
1. ✅ **UI Mapeo de Columnas**: Componente ColumnMappingDialog.jsx con auto-detección y mapeo visual
2. ✅ **Mejoras en Mi Catálogo**: 4 tarjetas de estadísticas, filtros por proveedor/estado
3. ✅ **Exportar a WooCommerce API REST**: Nueva sección completa con integración real

### Testing
- 100% tests pasados en todas las iteraciones
- Ver: /app/test_reports/iteration_3.json

## Próximas Tareas (P1)
- [ ] Integración API REST con Prestashop
- [ ] Integración API REST con Shopify

## Backlog (P2)
- [ ] Alertas por email
- [ ] Historial de cambios por producto
- [ ] API pública para integraciones externas
- [ ] Múltiples usuarios por cuenta
- [ ] Roles y permisos
- [ ] Refactorizar server.py en módulos separados
