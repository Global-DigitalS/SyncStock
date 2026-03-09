# =============================================================================
# GUÍA DE DESPLIEGUE Y SOLUCIÓN DE PROBLEMAS - SYNCSTOCK
# =============================================================================

## 📋 ÍNDICE
1. [Diagnóstico de Problemas](#1-diagnóstico-de-problemas)
2. [Actualización del Servidor](#2-actualización-del-servidor)
3. [Configuración de Nginx/WebSockets](#3-configuración-de-nginx-websockets)
4. [Solución de Errores Comunes](#4-solución-de-errores-comunes)

---

## 1. DIAGNÓSTICO DE PROBLEMAS

### Paso 1: Ejecutar script de diagnóstico

```bash
# Descarga y ejecuta el script de diagnóstico
cd /var/www/vhosts/app.sync-stock.com/app
chmod +x scripts/diagnose.sh
./scripts/diagnose.sh > diagnostico.txt 2>&1
cat diagnostico.txt
```

### Paso 2: Verificar logs manualmente

```bash
# Logs del backend (systemd)
journalctl -u suppliersync-backend -f --no-pager -n 100

# Si usas supervisor
tail -f /var/log/supervisor/backend.err.log

# Logs de Nginx
tail -f /var/log/nginx/error.log
```

### Paso 3: Verificar conexión a MongoDB

```bash
# Entrar al entorno virtual
cd /var/www/vhosts/app.sync-stock.com/app/backend
source venv/bin/activate

# Probar conexión
python3 -c "
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.environ.get('MONGO_URL'))
print('Bases de datos:', client.list_database_names())
print('Conexión OK!')
"
```

---

## 2. ACTUALIZACIÓN DEL SERVIDOR

### Opción A: Script automático

```bash
cd /var/www/vhosts/app.sync-stock.com/app
chmod +x scripts/update.sh
APP_DIR=/var/www/vhosts/app.sync-stock.com/app ./scripts/update.sh
```

### Opción B: Actualización manual paso a paso

```bash
# 1. Ir al directorio de la app
cd /var/www/vhosts/app.sync-stock.com/app

# 2. Detener servicio
sudo systemctl stop suppliersync-backend

# 3. Hacer backup
tar -czf /var/backups/syncstock_$(date +%Y%m%d).tar.gz .

# 4. Actualizar código (si usas git)
git pull origin main

# 5. Actualizar dependencias backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 6. Actualizar frontend
cd frontend
yarn install
REACT_APP_BACKEND_URL=https://app.sync-stock.com yarn build
cd ..

# 7. Reiniciar servicio
sudo systemctl start suppliersync-backend

# 8. Verificar
curl http://localhost:8001/api/health
```

---

## 3. CONFIGURACIÓN DE NGINX/WEBSOCKETS

### Para Plesk (método recomendado)

1. **Ir a Plesk** → Dominios → `app.sync-stock.com` → Apache & nginx Settings

2. **En "Additional nginx directives"**, pegar:

```nginx
# WebSocket support
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# API proxy
location /api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

# WebSocket proxy
location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
}

# Health endpoint
location /health {
    proxy_pass http://127.0.0.1:8001/health;
}
```

3. **Guardar** y aplicar los cambios

4. **Verificar** que Nginx no tenga errores:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 4. SOLUCIÓN DE ERRORES COMUNES

### Error 500 en /api/suppliers

**Causa probable:** Problema de conexión a MongoDB o error en el código.

**Solución:**
```bash
# 1. Verificar logs
journalctl -u suppliersync-backend -n 50 --no-pager

# 2. Verificar MongoDB
cd /var/www/vhosts/app.sync-stock.com/app/backend
source venv/bin/activate
python3 -c "
from services.database import db
import asyncio
async def test():
    suppliers = await db.suppliers.find().to_list(1)
    print('Proveedores:', len(suppliers) if suppliers else 0)
asyncio.run(test())
"

# 3. Reiniciar servicio
sudo systemctl restart suppliersync-backend
```

### WebSocket no conecta

**Causa probable:** Nginx no está configurado para WebSockets.

**Solución:** Agregar la configuración de WebSocket en Nginx (ver sección 3).

### Frontend no carga / página en blanco

**Causa probable:** Frontend no compilado o ruta incorrecta.

**Solución:**
```bash
cd /var/www/vhosts/app.sync-stock.com/app/frontend

# Verificar que existe el build
ls -la build/

# Si no existe, compilar
REACT_APP_BACKEND_URL=https://app.sync-stock.com yarn build
```

### Error "Cannot connect to MongoDB"

**Causa probable:** MongoDB no está corriendo o credenciales incorrectas.

**Solución:**
```bash
# Verificar que MongoDB está corriendo
sudo systemctl status mongod
# o si usas Docker
docker ps | grep mongo

# Verificar credenciales en .env
cat /var/www/vhosts/app.sync-stock.com/app/backend/.env | grep MONGO
```

---

## 📞 SOPORTE

Si después de seguir esta guía sigues teniendo problemas:

1. Ejecuta el script de diagnóstico: `./scripts/diagnose.sh > diagnostico.txt`
2. Comparte el archivo `diagnostico.txt` para análisis
3. Incluye el error específico que ves en la consola del navegador

---

*Última actualización: 2026-03-09*
