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
- [x] CRUD de proveedores
- [x] Importación de productos (CSV, XLSX, XLS, XML)
- [x] Normalización automática de campos
- [x] Catálogo personal con precios personalizados
- [x] Reglas de margen (porcentaje/fijo, por categoría/proveedor)
- [x] Exportación a Prestashop, WooCommerce, Shopify
- [x] Dashboard con estadísticas
- [x] Historial de precios
- [x] Notificaciones de stock

### Frontend
- [x] Login/Registro con diseño profesional
- [x] Dashboard con estadísticas y alertas
- [x] Gestión de proveedores
- [x] **Detalle de proveedor con catálogo de productos**
- [x] **Selección múltiple para añadir al catálogo**
- [x] Productos con filtros (búsqueda, categoría, stock)
- [x] Mi Catálogo con precios finales
- [x] Reglas de margen configurables
- [x] Exportación a 3 plataformas
- [x] Historial de precios con gráficos
- [x] Centro de notificaciones

## Última Actualización: Feb 2026
- Añadida página de detalle de proveedor (/suppliers/:supplierId)
- Selección múltiple de productos con checkboxes
- Botón "Ver catálogo" en lista de proveedores
- Corregido bug de SelectItem con valores vacíos

## Backlog (P1)
- [ ] Sincronización FTP automática
- [ ] Programación de importaciones
- [ ] Alertas por email
- [ ] Historial de cambios por producto

## Backlog (P2)
- [ ] API pública para integraciones
- [ ] Múltiples usuarios por cuenta
- [ ] Roles y permisos
