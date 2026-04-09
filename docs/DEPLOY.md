# Guía de Despliegue en Plesk - SyncStock

Esta guía detalla cómo desplegar SyncStock en un servidor Plesk. **Toda la configuración se realiza desde la interfaz web** - no necesitas editar archivos de configuración manualmente.

## Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Despliegue Rápido (TL;DR)](#despliegue-rápido)
3. [Despliegue del Backend](#despliegue-del-backend)
4. [Despliegue del Frontend](#despliegue-del-frontend)
5. [Configuración Inicial desde la Web](#configuración-inicial-desde-la-web)
6. [Verificación](#verificación)
7. [Solución de Problemas](#solución-de-problemas)

---

## Requisitos Previos

### Servidor
- Plesk Obsidian 18.0+ con acceso SSH
- Python 3.9+
- Node.js 18+
- Nginx o Apache

### Base de Datos
- MongoDB 5.0+ (local o MongoDB Atlas)
- **Nota**: La URL de conexión se configura desde la interfaz web

### Dominio
- Un dominio o subdominio configurado en Plesk
- Certificado SSL (recomendado Let's Encrypt)

---

## Despliegue Rápido

```bash
# 1. Subir código al servidor
cd /var/www/vhosts/tu-dominio.com/app

# 2. Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Crear servicio (ver sección Backend)
sudo systemctl enable --now syncstock-backend

# 4. Frontend
cd ../frontend
yarn install && yarn build

# 5. Configurar Nginx en Plesk (ver sección Frontend)

# 6. Abrir https://tu-dominio.com/setup en el navegador
# 7. Configurar MongoDB + Crear SuperAdmin desde la web
# ¡Listo!
```

---

## Despliegue del Backend

### 1. Preparar el entorno
```bash
cd /var/www/vhosts/tu-dominio.com/app/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Crear el servicio systemd
```bash
sudo nano /etc/systemd/system/syncstock-backend.service
```

Contenido:
```ini
[Unit]
Description=SyncStock Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/tu-dominio.com/app/backend
Environment="PATH=/var/www/vhosts/tu-dominio.com/app/backend/venv/bin"
ExecStart=/var/www/vhosts/tu-dominio.com/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Iniciar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable syncstock-backend
sudo systemctl start syncstock-backend
```

### 4. Verificar
```bash
curl http://localhost:8001/health
# Respuesta: {"status": "healthy", "service": "SyncStock API"}
```

**⚠️ NOTA IMPORTANTE**: No necesitas crear ningún archivo `.env`. Toda la configuración (MongoDB, JWT, CORS) se realiza desde la interfaz web en el primer acceso.

---

## Despliegue del Frontend

### 1. Instalar dependencias y compilar
```bash
cd /var/www/vhosts/tu-dominio.com/app/frontend

# Crear archivo .env con la URL del backend
echo "REACT_APP_BACKEND_URL=https://tu-dominio.com" > .env

# Instalar y compilar
yarn install
yarn build
```

### 2. Configurar Nginx en Plesk

En Plesk: **Dominios** → Tu dominio → **Configuración de Apache y Nginx**

Añadir en "Directivas adicionales de nginx":

```nginx
# API Backend
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
}

# Health check
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}

# WebSocket
location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}

# Frontend
location / {
    root /var/www/vhosts/tu-dominio.com/app/frontend/build;
    try_files $uri $uri/ /index.html;
}
```

### 3. Aplicar cambios
```bash
sudo systemctl reload nginx
```

---

## Configuración Inicial desde la Web

### 🎉 ¡Todo desde el navegador!

Al acceder a `https://tu-dominio.com` por primera vez, serás redirigido automáticamente a la página de configuración (`/setup`).

### Paso 1: Configuración del Sistema

![Setup Step 1](https://via.placeholder.com/800x400?text=Configuración+del+Sistema)

1. **URL de MongoDB**: Introduce tu cadena de conexión
   - MongoDB Local: `mongodb://localhost:27017`
   - MongoDB Atlas: `mongodb+srv://usuario:contraseña@cluster.mongodb.net`

2. **Nombre de la base de datos**: Por defecto `syncstock_db`

3. **Probar Conexión**: Verifica que la conexión funciona antes de continuar

4. **Seguridad (Opcional)**:
   - **JWT Secret**: Se genera automáticamente, o puedes usar uno personalizado
   - **CORS Origins**: Por defecto `*` (todos). Para producción, especifica tu dominio

5. Click en **"Continuar"**

### Paso 2: Crear SuperAdmin

1. **Nombre completo**: Tu nombre
2. **Email**: admin@tu-empresa.com
3. **Empresa**: (opcional)
4. **Contraseña**: Mínimo 6 caracteres

5. Click en **"Completar Configuración"**

### ¡Listo! 🚀

La aplicación te redirigirá automáticamente al dashboard.

---

## Verificación

### Comprobar estado del sistema
```bash
# Health check
curl https://tu-dominio.com/health

# Estado de configuración
curl https://tu-dominio.com/api/setup/status
```

Respuesta cuando está configurado:
```json
{
  "is_configured": true,
  "has_database": true,
  "has_superadmin": true,
  "database_name": "syncstock_db",
  "message": "Aplicación configurada correctamente."
}
```

---

## Solución de Problemas

### El backend no inicia
```bash
# Ver logs
sudo journalctl -u syncstock-backend -f

# Verificar permisos
sudo chown -R www-data:www-data /var/www/vhosts/tu-dominio.com/app/backend
```

### Error de conexión a MongoDB

1. **MongoDB Local**: Verifica que está corriendo
   ```bash
   sudo systemctl status mongod
   ```

2. **MongoDB Atlas**: 
   - Verifica que tu IP está en la whitelist de Atlas
   - Verifica usuario y contraseña

### La página de setup no aparece

Si ya existe configuración pero no puedes acceder:

1. Eliminar el archivo de configuración para resetear:
   ```bash
   rm /var/www/vhosts/tu-dominio.com/app/backend/config.json
   sudo systemctl restart syncstock-backend
   ```

2. Acceder a `https://tu-dominio.com/setup`

### Error 502 Bad Gateway
```bash
# Verificar backend
curl http://localhost:8001/health

# Verificar Nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

---

## Archivos de Configuración

La aplicación guarda su configuración en:

```
/var/www/vhosts/tu-dominio.com/app/backend/config.json
```

Estructura del archivo (se genera automáticamente):
```json
{
  "mongo_url": "mongodb://...",
  "db_name": "syncstock_db",
  "jwt_secret": "...(generado automáticamente)...",
  "cors_origins": "*",
  "is_configured": true
}
```

**⚠️ No edites este archivo manualmente**. Usa siempre la interfaz web o elimínalo para resetear la configuración.

---

## Comandos Útiles

```bash
# Reiniciar backend
sudo systemctl restart syncstock-backend

# Ver logs en tiempo real
sudo journalctl -u syncstock-backend -f

# Reiniciar Nginx
sudo systemctl reload nginx

# Actualizar aplicación
cd /var/www/vhosts/tu-dominio.com/app
git pull
cd backend && source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart syncstock-backend
cd ../frontend && yarn install && yarn build
```

---

## Resumen del Flujo

```
1. Subir código al servidor
         ↓
2. Instalar dependencias (backend + frontend)
         ↓
3. Configurar servicios (systemd + nginx)
         ↓
4. Acceder a https://tu-dominio.com/setup
         ↓
5. Configurar MongoDB (URL, nombre DB)
         ↓
6. Configurar seguridad (JWT, CORS) - opcional
         ↓
7. Crear usuario SuperAdmin
         ↓
8. ¡Aplicación lista para usar!
```

---

**SyncStock** - Gestión inteligente de catálogos de proveedores

© 2026 - Toda la configuración desde la web, sin archivos de configuración manuales.
