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

### Frontend
- [x] Login/Registro con diseño profesional
- [x] Dashboard con estadísticas y alertas
- [x] Gestión de proveedores con formulario de pestañas
- [x] **Página Catálogos** - Gestión completa de múltiples catálogos
- [x] **Detalle de Catálogo** - Ver y gestionar productos por catálogo
- [x] **Exportar a WooCommerce** - Selector de catálogo para exportar
- [x] **Selección múltiple de productos en Proveedores** - Añadir a varios catálogos
- [x] **Selección múltiple de productos en Productos** - Añadir a varios catálogos
- [x] Reglas de margen configurables
- [x] Exportación a 3 plataformas (CSV)
- [x] Historial de precios
- [x] Centro de notificaciones

## Última Actualización: 19 Feb 2026

### Sesión Actual - Selección Múltiple de Catálogos
1. ✅ **SupplierDetail.jsx**: Dialog para añadir productos a múltiples catálogos
2. ✅ **Products.jsx**: 
   - Checkboxes para seleccionar productos
   - Banner de "X productos seleccionados" 
   - Botón "Añadir a Catálogos"
   - Dialog con checkboxes para seleccionar múltiples catálogos
3. ✅ Icono actualizado de Plus a BookOpen para claridad visual

### Testing
- Frontend verificado visualmente con screenshots
- Flujo completo: seleccionar productos → abrir dialog → seleccionar catálogos → confirmar

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
