# SyncStock - Guía de Instalación

## Instalación Automática (Recomendado)

### Un solo comando:

```bash
# Descargar y ejecutar el instalador
curl -sSL https://tu-repo.com/install.sh | sudo bash

# O si ya tienes el código:
cd /ruta/al/codigo
sudo bash install.sh
```

El script automáticamente:
- ✅ Instala Python 3, Node.js 20, MongoDB (opcional)
- ✅ Configura el backend con FastAPI y systemd
- ✅ Compila el frontend con React
- ✅ Configura Nginx (detecta Plesk automáticamente)
- ✅ Opcionalmente configura SSL con Let's Encrypt
- ✅ **Configura almacenamiento persistente** para la configuración

### Después de la instalación:

1. Abre `https://tu-dominio.com/#/setup` en tu navegador
2. Configura MongoDB (si no lo hiciste durante la instalación)
3. Crea tu usuario SuperAdmin
4. ¡Listo!

---

## ⚠️ IMPORTANTE: Configuración de Nginx en Plesk

**Plesk NO carga automáticamente los archivos `nginx_custom.conf`.**

Después de instalar, **DEBES** añadir manualmente la configuración del proxy:

### Pasos:

1. Ve a **Plesk → Dominios → tu-dominio.com**
2. Haz clic en **"Apache & nginx Settings"**
3. Busca la sección **"Additional nginx directives"**
4. **Copia y pega** el siguiente contenido:

```nginx
# API Backend - Proxy a FastAPI (puerto 8001)
location /api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
    proxy_send_timeout 300s;
}

# Health Check
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 10s;
}
```

5. Haz clic en **OK** o **Apply**

**Sin esta configuración, las llamadas a `/api/*` devolverán error 404.**

---

## 🔒 Configuración Persistente

**Tu configuración NO se perderá al actualizar la aplicación.**

La configuración (MongoDB, JWT, SMTP, etc.) se guarda en:
```
/etc/syncstock/config.json
```

Esta ubicación está **fuera** del directorio de la aplicación, por lo que:
- ✅ Actualizar el código no afecta tu configuración
- ✅ El SuperAdmin y conexión a MongoDB se preservan
- ✅ Los backups automáticos se guardan en `/etc/syncstock/backups/`

### Recarga Dinámica de Configuración

Si cambias la configuración de MongoDB y no quieres reiniciar el servidor:

```bash
curl -X POST http://localhost:8001/api/setup/reload-database
```

O desde la URL externa:
```bash
curl -X POST https://tu-dominio.com/api/setup/reload-database
```

---

## 🔄 Actualizar la Aplicación

Para actualizar sin perder la configuración:

```bash
sudo bash update.sh
```

El script de actualización:
- Crea un backup automático de tu configuración
- Actualiza el código (git pull o manual)
- Reinstala dependencias si es necesario
- Recompila el frontend
- **Preserva toda tu configuración**

---

## Instalación Manual

Si prefieres control total, consulta [README-DEPLOY-PLESK.md](README-DEPLOY-PLESK.md)

---

## Requisitos del Servidor

- **Sistema Operativo**: Ubuntu 20.04+, Debian 11+, CentOS 8+, Rocky Linux 8+
- **RAM**: Mínimo 1GB (recomendado 2GB)
- **Disco**: Mínimo 10GB libres
- **Puertos**: 80, 443, 8001

---

## Estructura del Proyecto

```
/
├── backend/                 # API FastAPI
│   ├── routes/             # Endpoints de la API
│   ├── services/           # Lógica de negocio
│   ├── models/             # Esquemas Pydantic
│   └── server.py           # Punto de entrada
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── pages/         # Páginas de la aplicación
│   │   └── components/    # Componentes reutilizables
│   └── build/             # Archivos compilados
├── install.sh             # Script de instalación automática
├── update.sh              # Script de actualización (preserva config)
└── README.md              # Este archivo

/etc/syncstock/          # Configuración persistente (fuera del app)
├── config.json            # Configuración principal
└── backups/               # Backups automáticos
```

---

## Comandos Útiles

```bash
# Estado del backend
sudo systemctl status syncstock-backend

# Ver logs en tiempo real
sudo journalctl -u syncstock-backend -f

# Reiniciar backend
sudo systemctl restart syncstock-backend

# Health check
curl http://localhost:8001/health

# Ver información de configuración
curl http://localhost:8001/api/setup/config-info

# Crear backup manual de configuración
curl -X POST http://localhost:8001/api/setup/backup

# Ver backups disponibles
curl http://localhost:8001/api/setup/backups

# Recargar configuración de MongoDB sin reiniciar el servidor
curl -X POST http://localhost:8001/api/setup/reload-database
```

---

## Flujo de Configuración Web

```
┌─────────────────────────────────────────────────────────────────┐
│                    https://tu-dominio.com/setup                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Paso 1: Configuración del Sistema                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • URL de MongoDB      [mongodb://localhost:27017    ]     │ │
│  │  • Nombre de BD        [syncstock_db             ]     │ │
│  │  • [Probar Conexión]                                       │ │
│  │                                                             │ │
│  │  Seguridad (opcional):                                     │ │
│  │  • JWT Secret          [Auto] o [Personalizado]            │ │
│  │  • CORS Origins        [*] o [https://midominio.com]       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                         [Continuar →]                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Paso 2: Crear SuperAdmin                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Nombre              [Tu nombre                    ]     │ │
│  │  • Email               [admin@empresa.com            ]     │ │
│  │  • Empresa             [Mi Empresa (opcional)        ]     │ │
│  │  • Contraseña          [••••••••                     ]     │ │
│  │  • Confirmar           [••••••••                     ]     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                    [Completar Configuración →]                   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ¡Configuración Completada!                    │
│                  Redirigiendo al Dashboard...                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Soporte

¿Problemas con la instalación? Revisa los logs:

```bash
# Logs del backend
sudo journalctl -u syncstock-backend --no-pager -n 50

# Logs de Nginx
sudo tail -50 /var/log/nginx/error.log

# Estado de MongoDB
sudo systemctl status mongod
```

---

## 🔗 Integraciones CRM

SyncStock incluye integraciones con los principales ERPs/CRMs del mercado para sincronización automática de productos, proveedores y órdenes.

### Plataformas Soportadas

#### 🏢 Dolibarr
- **Versión**: 15.0+
- **Autenticación**: API Key
- **Características**: Productos, Proveedores, Órdenes, Stock, Almacenes
- **Estado**: ✅ Estable

#### ⚙️ Odoo (NUEVO)
- **Versión**: 17.0+
- **Autenticación**: API Token (Bearer)
- **Características**: Productos, Proveedores, Órdenes, Stock, Almacenes
- **Estado**: ✅ Implementado y Probado

### Configurar una Integración CRM

1. Ve al Dashboard → CRM → Nueva Conexión
2. Selecciona la plataforma (Dolibarr u Odoo)
3. Ingresa los datos de conexión:
   - **URL base** de tu instancia
   - **API Key** (Dolibarr) o **API Token** (Odoo)
4. Haz clic en "Test Connection"
5. Si es exitosa, guarda y configura opciones de sincronización

### Opciones de Sincronización

```json
{
  "products": true,      // Sincronizar productos
  "stock": true,         // Sincronizar niveles de stock
  "prices": true,        // Sincronizar precios
  "descriptions": true,  // Sincronizar descripciones
  "images": true,        // Sincronizar imágenes de productos
  "suppliers": true,     // Sincronizar proveedores
  "orders": true         // Importar órdenes
}
```

### Sincronización Automática

- **Intervalo**: 1, 6, 12 o 24 horas
- **Tipo**: Completo o parcial (solo productos, solo proveedores, etc.)
- **Monitoreo**: Ve el progreso en tiempo real
- **Historial**: Registro de todos los syncronizaciones

### Documentación Detallada

Para información completa sobre:
- **Configuración**: Ver [ODOO_INTEGRATION.md](ODOO_INTEGRATION.md)
- **Guía Técnica**: Ver [ODOO_INTEGRATION_SUMMARY.md](ODOO_INTEGRATION_SUMMARY.md)

### Limitaciones Conocidas

- Las órdenes se importan desde WooCommerce hacia el CRM (unidireccional)
- No se sincronizan atributos de productos (variantes, colores, etc.)
- No hay descuentos ni promociones automáticas
- Clientes/contactos se crean pero no se actualizan completamente

### Próximas Integraciones Planeadas

- [ ] SAP Business One
- [ ] NetSuite
- [ ] Microsoft Dynamics 365
- [ ] QuickBooks Enterprise

---

**SyncStock** © 2026 - Gestión inteligente de catálogos de proveedores
