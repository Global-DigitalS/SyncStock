# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores.

## Funcionalidades Implementadas
- [x] Autenticación JWT (registro, login, token)
- [x] Gestión de proveedores CRUD
- [x] Sincronización FTP/SFTP/URL de productos
- [x] Mapeo de columnas CSV personalizable
- [x] Gestión de múltiples catálogos
- [x] Reglas de margen por catálogo
- [x] Unificación de productos por EAN
- [x] Exportación CSV (PrestaShop, WooCommerce, Shopify)
- [x] Exportación a WooCommerce API (con EAN como GTIN)
- [x] Sincronización automática WooCommerce (cada 12h, precio y stock)
- [x] Dashboard mejorado con stats WooCommerce y alertas de stock
- [x] Sistema de notificaciones
- [x] Refactorización completa del backend a arquitectura modular
- [x] Ficha de producto con 2 pestañas (Proveedores + Datos editables)
- [x] Explorador FTP integrado en configuración de proveedor
- [x] Soporte multi-archivo por proveedor (ej: TechData con Stock + ZIP con Productos/Precios)
- [x] Extracción automática de ZIP y detección de roles de archivo
- [x] Sincronización multi-archivo con fusión de datos por clave común

## Arquitectura
- **Backend**: FastAPI modular + MongoDB + APScheduler
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Estructura**: routes/, models/, services/ (refactorizado desde monolítico)

## Backlog
- [ ] Gráficas de evolución de precios
- [ ] Sistema de roles de usuario
- [ ] Historial de sincronizaciones detallado
