# SupplierSync Pro - PRD

## Descripción del Producto
Aplicación SaaS para gestionar catálogos de productos de proveedores. Permite descargar archivos CSV de productos desde FTP/SFTP o URL, ver precios y stocks, crear catálogos personalizados con reglas de márgenes, y exportar a múltiples plataformas de eCommerce.

## Usuarios y Roles
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **SuperAdmin** | Administrador global | Gestión de usuarios, límites, planes, SMTP |
| **Admin** | Administrador de organización | Gestión completa de proveedores, productos, catálogos |
| **User** | Usuario operativo | CRUD dentro de sus límites |
| **Viewer** | Solo lectura | Visualización sin modificación |

## Funcionalidades Implementadas

### ✅ Core
- [x] Login/Registro con JWT
- [x] Sistema de roles
- [x] Límites de recursos por usuario
- [x] Botón mostrar/ocultar contraseña
- [x] Recuperación de contraseña vía email
- [x] CRUD de proveedores (FTP, URL)
- [x] Sincronización de archivos CSV
- [x] Mapeo de columnas flexible
- [x] Explorador FTP mejorado
- [x] Selección de productos desde proveedor
- [x] Catálogos con reglas de margen
- [x] Exportación a CSV
- [x] Tiendas multi-plataforma (WooCommerce, PrestaShop, Shopify)

### ✅ Configuración Web (/setup)
- [x] Paso 1: Configuración MongoDB y JWT
- [x] Paso 2: Creación de SuperAdmin
- [x] Paso 3: Configuración SMTP (opcional)
- [x] Test de conexión MongoDB
- [x] Guardado en config.json Y .env automáticamente

### ✅ Sistema de Email
- [x] Configuración SMTP genérica
- [x] Email de bienvenida
- [x] Email de recuperación de contraseña
- [x] Email de cambio de suscripción

### ✅ Optimizado para Plesk
- [x] HashRouter para URLs con # (no requiere configuración especial de nginx)
- [x] Document Root: `app/frontend/build`
- [x] Script de instalación automática (`install.sh`)
- [x] Script de reparación (`install.sh --fix-plesk`)

## Arquitectura

```
/app/
├── backend/
│   ├── config.json          # Configuración principal (MongoDB, JWT, SMTP)
│   ├── .env                  # Variables de entorno (auto-actualizado)
│   ├── services/
│   │   ├── database.py      # Conexión MongoDB (lee de config.json primero)
│   │   ├── config_manager.py # Guarda en config.json Y .env
│   │   └── email_service.py
│   ├── routes/
│   │   ├── setup.py         # Configuración inicial vía web
│   │   ├── auth.py
│   │   ├── products.py
│   │   └── ...
│   └── server.py
└── frontend/
    ├── src/
    │   ├── App.js           # HashRouter para compatibilidad con Plesk
    │   └── pages/
    │       ├── Setup.jsx    # 3 pasos de configuración
    │       └── ...
    └── build/               # Document Root para Plesk
```

## URLs de la Aplicación (HashRouter)
- `https://tudominio.com/#/setup` - Configuración inicial
- `https://tudominio.com/#/login` - Iniciar sesión
- `https://tudominio.com/#/register` - Registro
- `https://tudominio.com/#/` - Dashboard

## Instalación en Plesk

### Instalación Automática
```bash
sudo bash install.sh
```

### Reparación Rápida
```bash
sudo bash install.sh --fix-plesk
```

### Configuración Manual en Plesk
1. Document Root: `app/frontend/build`
2. En "Apache & nginx Settings" → "Additional nginx directives":
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 300s;
}

location /health {
    proxy_pass http://127.0.0.1:8001/health;
}
```

## Credenciales de Prueba
- **Email**: test@test.com
- **Password**: test123
- **Rol**: superadmin

## Historial de Cambios

### 27/02/2026
- ✅ Cambiado a HashRouter para compatibilidad con Plesk
- ✅ config_manager.py ahora guarda en config.json Y .env
- ✅ database.py prioriza config.json sobre variables de entorno
- ✅ Simplificado install.sh para Plesk

### 26/02/2026
- ✅ Configuración SMTP en página /setup (paso 3)
- ✅ Email de notificación al cambiar de plan
- ✅ Refactorización con componentes compartidos
- ✅ Corrección de N+1 queries en productos y catálogos

## Tareas Pendientes

### P2 - Media
- [ ] Verificar corrección FTP con datos reales
- [ ] Integración SFTP
- [ ] Selección múltiple de archivos en navegador FTP

### P3 - Backlog
- [ ] Autenticación 2FA
- [ ] Integración real con Wix y Magento
- [ ] Dashboard SuperAdmin ampliado
