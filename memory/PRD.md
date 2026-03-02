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
- [x] **Configuración persistente en `/etc/suppliersync/`**
- [x] **Backups automáticos de configuración**
- [x] Información de ubicación de configuración en API

### ✅ Sistema de Actualización
- [x] Script `update.sh` que preserva configuración
- [x] Detección automática de instalación existente
- [x] Migración automática de config.json a ubicación persistente
- [x] Backups previos a actualización

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
- [x] Script de actualización (`update.sh`)

## Arquitectura

```
/app/
├── backend/
│   ├── .env                  # Variables de entorno (auto-actualizado)
│   ├── services/
│   │   ├── database.py      # Conexión MongoDB (lee de config.json primero)
│   │   ├── config_manager.py # Guarda en /etc/suppliersync/config.json
│   │   └── email_service.py
│   ├── routes/
│   │   ├── setup.py         # Configuración inicial vía web + backups
│   │   ├── auth.py
│   │   ├── products.py
│   │   └── ...
│   └── server.py
├── frontend/
│   ├── src/
│   │   ├── App.js           # HashRouter para compatibilidad con Plesk
│   │   └── pages/
│   │       ├── Setup.jsx    # 3 pasos de configuración
│   │       └── ...
│   └── build/               # Document Root para Plesk
├── install.sh               # Instalación inicial
└── update.sh                # Actualización preservando configuración

/etc/suppliersync/            # ⭐ CONFIGURACIÓN PERSISTENTE
├── config.json              # MongoDB, JWT, SMTP (NO se pierde al actualizar)
└── backups/                 # Backups automáticos
```

## Ubicación de Configuración (Persistente)

La configuración ahora se guarda en **`/etc/suppliersync/config.json`**, que es una ubicación:
- ✅ **Fuera del directorio de la aplicación** - No se sobrescribe al actualizar
- ✅ **Estándar de Linux** - `/etc/` es para configuraciones del sistema
- ✅ **Con backups automáticos** - En `/etc/suppliersync/backups/`

### Prioridad de búsqueda de configuración:
1. `/etc/suppliersync/config.json` (producción - persistente)
2. `~/.suppliersync/config.json` (desarrollo local)
3. `[APP_DIR]/backend/config.json` (fallback - se migra automáticamente)

## URLs de la Aplicación (HashRouter)
- `https://tudominio.com/#/setup` - Configuración inicial
- `https://tudominio.com/#/login` - Iniciar sesión
- `https://tudominio.com/#/register` - Registro
- `https://tudominio.com/#/` - Dashboard

## API de Configuración

```bash
# Estado de configuración
GET /api/setup/status

# Información de ubicación de configuración
GET /api/setup/config-info

# Crear backup manual
POST /api/setup/backup

# Listar backups
GET /api/setup/backups
```

## Instalación en Plesk

### Instalación Automática
```bash
sudo bash install.sh
```

### Actualización (Preserva configuración)
```bash
sudo bash update.sh
```

### Reparación Rápida
```bash
sudo bash install.sh --fix-plesk
```

## Credenciales de Prueba
- **Email**: test@test.com
- **Password**: test123
- **Rol**: superadmin

## Historial de Cambios

### 02/03/2026
- ✅ **Configuración persistente en `/etc/suppliersync/`**
- ✅ **Script `update.sh` para actualizar sin perder configuración**
- ✅ Migración automática de config.json a ubicación persistente
- ✅ API para backups de configuración
- ✅ Documentación actualizada

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
