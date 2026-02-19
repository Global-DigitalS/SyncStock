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
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Auth**: JWT con bcrypt

## Funcionalidades Implementadas

### Backend
- [x] Autenticación JWT (registro/login)
- [x] CRUD de proveedores con configuración FTP/SFTP
- [x] Importación de productos (CSV, XLSX, XLS, XML)
- [x] Normalización automática de campos
- [x] Catálogo personal con precios personalizados
- [x] Reglas de margen (porcentaje/fijo, por categoría/proveedor)
- [x] Exportación a Prestashop, WooCommerce, Shopify
- [x] Dashboard con estadísticas
- [x] Historial de precios
- [x] Notificaciones de stock
- [x] Sincronización FTP/SFTP automática cada 12 horas (APScheduler)
- [x] Sincronización manual desde el frontend
- [x] Mapeo de columnas personalizado

### Frontend
- [x] Login/Registro con diseño profesional
- [x] Dashboard con estadísticas y alertas
- [x] Gestión de proveedores con formulario de pestañas
- [x] Configuración FTP (schema, host, port, user, password, path, modo)
- [x] Configuración CSV (separador, enclosure, header row, formato)
- [x] Detalle de proveedor con catálogo de productos
- [x] Selección múltiple para añadir al catálogo
- [x] Productos con filtros (búsqueda, categoría, stock)
- [x] Mi Catálogo con precios finales
- [x] Reglas de margen configurables
- [x] Exportación a 3 plataformas
- [x] Historial de precios con gráficos
- [x] Centro de notificaciones

## Última Actualización: 19 Feb 2026
### Bug Fixes (Sesión Actual)
- ✅ Corregido bug crítico en POST /api/suppliers (csv_field_mapping → column_mapping)
- ✅ Corregido endpoint de sync para devolver JSON con errores en lugar de HTTP 500
- ✅ Aumentado JWT_SECRET a 32+ bytes para mayor seguridad
- ✅ Reducido timeout de FTP a 15s para evitar timeouts de Cloudflare

### Testing
- 100% tests pasados (19/19 backend, todos los flujos frontend)
- Ver: /app/test_reports/iteration_2.json

## Próximas Tareas (P1)
- [ ] Implementar UI de mapeo de columnas (arrastrar y soltar columnas del proveedor a campos del sistema)
- [ ] Crear sección de catálogo personal mejorada
- [ ] Desarrollar UI para reglas de márgenes

## Backlog (P2)
- [ ] Alertas por email
- [ ] Historial de cambios por producto
- [ ] API pública para integraciones
- [ ] Múltiples usuarios por cuenta
- [ ] Roles y permisos
