# SupplierSync Pro - Guía de Instalación

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

### Después de la instalación:

1. Abre `https://tu-dominio.com/setup` en tu navegador
2. Configura MongoDB (si no lo hiciste durante la instalación)
3. Crea tu usuario SuperAdmin
4. ¡Listo!

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
└── README.md              # Este archivo
```

---

## Comandos Útiles

```bash
# Estado del backend
sudo systemctl status suppliersync-backend

# Ver logs en tiempo real
sudo journalctl -u suppliersync-backend -f

# Reiniciar backend
sudo systemctl restart suppliersync-backend

# Health check
curl http://localhost:8001/health
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
│  │  • Nombre de BD        [supplier_sync_db             ]     │ │
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
sudo journalctl -u suppliersync-backend --no-pager -n 50

# Logs de Nginx
sudo tail -50 /var/log/nginx/error.log

# Estado de MongoDB
sudo systemctl status mongod
```

---

**SupplierSync Pro** © 2026 - Gestión inteligente de catálogos de proveedores
