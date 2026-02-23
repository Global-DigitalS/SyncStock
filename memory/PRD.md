# SupplierSync Pro - PRD

## Problema Original
Aplicación SaaS para gestionar catálogos de productos de proveedores con las siguientes funcionalidades:
1. Descargar archivos de productos (CSV) desde FTP/SFTP o URL
2. Ver precios y stocks de proveedores
3. Crear múltiples catálogos de productos personalizados
4. Asignar reglas de márgenes de beneficio a catálogos
5. Exportar catálogos a CSV y a WooCommerce vía API REST
6. Autenticación JWT
7. Sincronización automática de datos de proveedores
8. Mapeo de columnas para archivos CSV
9. Unificar productos por EAN, mostrando el mejor proveedor
10. Sincronización automática con WooCommerce cada 12 horas
11. Al exportar a WooCommerce, usar EAN como identificador único (GTIN)
12. Ficha de producto con dos pestañas: Proveedores y Datos editables

## Arquitectura Técnica
- **Backend**: FastAPI (modular) + MongoDB + APScheduler
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Estructura modular**:
  - `/app/backend/server.py` - Orquestador principal
  - `/app/backend/routes/` - auth, suppliers, products, catalogs, woocommerce, dashboard
  - `/app/backend/models/schemas.py` - Modelos Pydantic
  - `/app/backend/services/` - database, auth, sync

## Funcionalidades Implementadas

### Completado
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
- [x] UI de configuración WooCommerce (selector catálogo + switch auto-sync)
- [x] Dashboard mejorado con stats WooCommerce y alertas de stock
- [x] Sistema de notificaciones (stock bajo, sincronización, exportación)
- [x] Página de notificaciones con filtros
- [x] Refactorización completa del backend a arquitectura modular
- [x] Ficha de producto con 2 pestañas: Proveedores (mejor oferta + comparativa) y Datos editables (formulario extenso con 40+ campos)
- [x] PUT /api/products/{id} - Endpoint para editar datos extendidos del producto

## Backlog Futuro
- [ ] Fix React setState warning en Login.jsx
- [ ] Gráficas de evolución de precios
- [ ] Sistema de roles de usuario
- [ ] API keys management para integraciones externas
- [ ] Historial de sincronizaciones detallado
