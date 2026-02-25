# Guía de Despliegue en Plesk - SupplierSync Pro

Esta guía detalla cómo desplegar SupplierSync Pro en un servidor Plesk con la nueva funcionalidad de configuración inicial simplificada.

## Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Despliegue del Backend](#despliegue-del-backend)
4. [Despliegue del Frontend](#despliegue-del-frontend)
5. [Configuración Inicial de la Aplicación](#configuración-inicial-de-la-aplicación)
6. [Verificación](#verificación)
7. [Solución de Problemas](#solución-de-problemas)

---

## Requisitos Previos

### Servidor
- Plesk Obsidian 18.0+ con acceso SSH
- Python 3.9+ instalado
- Node.js 18+ instalado
- Nginx o Apache configurado

### Base de Datos
- MongoDB 5.0+ (puede ser local o MongoDB Atlas)
- Si usas MongoDB Atlas, necesitarás la URL de conexión

### Dominio
- Un dominio o subdominio configurado en Plesk
- Certificado SSL (recomendado Let's Encrypt)

---

## Preparación del Servidor

### 1. Acceder por SSH
```bash
ssh usuario@tu-servidor.com
```

### 2. Crear estructura de directorios
```bash
mkdir -p /var/www/vhosts/tu-dominio.com/app
cd /var/www/vhosts/tu-dominio.com/app
```

### 3. Clonar o subir el código
```bash
# Opción 1: Git
git clone tu-repositorio.git .

# Opción 2: Subir archivos via SFTP/FTP
# Sube las carpetas 'backend' y 'frontend'
```

---

## Despliegue del Backend

### 1. Crear entorno virtual de Python
```bash
cd /var/www/vhosts/tu-dominio.com/app/backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea el archivo `.env` en la carpeta `backend`:

```bash
nano .env
```

**⚠️ IMPORTANTE: Configuración Mínima Inicial**

Para el primer inicio, solo necesitas configurar:

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=suppliersync_db
CORS_ORIGINS=https://tu-dominio.com
JWT_SECRET=genera-una-clave-secreta-larga-y-aleatoria
```

> **Nota**: La URL de MongoDB y la creación del SuperAdmin se pueden configurar desde la interfaz web en el primer inicio. Ver sección [Configuración Inicial](#configuración-inicial-de-la-aplicación).

**Para MongoDB Atlas:**
```env
MONGO_URL=mongodb+srv://usuario:contraseña@cluster.mongodb.net
DB_NAME=suppliersync_db
CORS_ORIGINS=https://tu-dominio.com
JWT_SECRET=genera-una-clave-secreta-larga-y-aleatoria
```

### 4. Configurar el servicio systemd

Crea un archivo de servicio:

```bash
sudo nano /etc/systemd/system/suppliersync-backend.service
```

Contenido:
```ini
[Unit]
Description=SupplierSync Pro Backend
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

### 5. Iniciar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable suppliersync-backend
sudo systemctl start suppliersync-backend
```

### 6. Verificar que el backend está corriendo
```bash
sudo systemctl status suppliersync-backend
curl http://localhost:8001/health
```

Respuesta esperada:
```json
{"status": "healthy", "service": "SupplierSync Pro API"}
```

---

## Despliegue del Frontend

### 1. Instalar dependencias
```bash
cd /var/www/vhosts/tu-dominio.com/app/frontend
npm install
# o usar yarn
yarn install
```

### 2. Configurar variables de entorno

Crea el archivo `.env`:
```bash
nano .env
```

Contenido:
```env
REACT_APP_BACKEND_URL=https://tu-dominio.com
```

### 3. Compilar para producción
```bash
npm run build
# o
yarn build
```

### 4. Configurar Nginx en Plesk

En Plesk, ve a:
- **Dominios** → Tu dominio → **Configuración de Apache y Nginx**
- En "Directivas adicionales de nginx", añade:

```nginx
# Proxy para el backend API
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
}

# Health check endpoint
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}

# WebSocket para notificaciones en tiempo real
location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}

# Servir frontend estático
location / {
    root /var/www/vhosts/tu-dominio.com/app/frontend/build;
    try_files $uri $uri/ /index.html;
}
```

### 5. Aplicar cambios
Guarda la configuración en Plesk y reinicia Nginx:
```bash
sudo systemctl reload nginx
```

---

## Configuración Inicial de la Aplicación

### 🎉 ¡Nueva Funcionalidad! Configuración desde la Web

Al acceder a la aplicación por primera vez, serás redirigido automáticamente a la **página de configuración inicial** (`/setup`).

### Paso 1: Configurar MongoDB

1. Accede a `https://tu-dominio.com/setup`
2. Introduce la **URL de conexión a MongoDB**:
   - **MongoDB Local**: `mongodb://localhost:27017`
   - **MongoDB Atlas**: `mongodb+srv://usuario:contraseña@cluster.mongodb.net`
3. Opcionalmente, cambia el **nombre de la base de datos** (por defecto: `supplier_sync_db`)
4. Haz clic en **"Probar Conexión"**
5. Si la conexión es exitosa ✅, haz clic en **"Continuar"**

### Paso 2: Crear Usuario SuperAdmin

1. Completa el formulario:
   - **Nombre completo**: Tu nombre
   - **Email**: admin@tu-empresa.com
   - **Empresa**: (opcional) Nombre de tu empresa
   - **Contraseña**: Mínimo 6 caracteres
   - **Confirmar contraseña**

2. Haz clic en **"Completar Configuración"**

### ¡Listo! 🚀

Serás redirigido automáticamente al dashboard con tu nueva cuenta SuperAdmin.

---

## Verificación

### 1. Verificar el health check
```bash
curl https://tu-dominio.com/health
```

### 2. Verificar estado de configuración
```bash
curl https://tu-dominio.com/api/setup/status
```

Respuesta cuando está configurado:
```json
{
  "is_configured": true,
  "has_database": true,
  "has_superadmin": true,
  "database_name": "supplier_sync_db",
  "message": "Aplicación configurada correctamente."
}
```

### 3. Probar login
```bash
curl -X POST https://tu-dominio.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tu-empresa.com","password":"tu-contraseña"}'
```

---

## Solución de Problemas

### El backend no inicia

1. Verificar logs:
```bash
sudo journalctl -u suppliersync-backend -f
```

2. Verificar permisos:
```bash
sudo chown -R www-data:www-data /var/www/vhosts/tu-dominio.com/app/backend
```

3. Verificar el archivo .env:
```bash
cat /var/www/vhosts/tu-dominio.com/app/backend/.env
```

### Error de conexión a MongoDB

1. Si usas MongoDB local, verifica que está corriendo:
```bash
sudo systemctl status mongod
```

2. Si usas MongoDB Atlas:
   - Verifica que tu IP está en la whitelist
   - Verifica usuario y contraseña
   - Prueba la conexión desde la terminal:
   ```bash
   mongosh "mongodb+srv://usuario:contraseña@cluster.mongodb.net"
   ```

### La página de setup no aparece

Si ya existe un SuperAdmin pero no puedes acceder:

1. Verificar en MongoDB:
```bash
mongosh
use supplier_sync_db
db.users.find({role: "superadmin"})
```

2. Si necesitas resetear, elimina el usuario:
```bash
db.users.deleteOne({role: "superadmin"})
```

### Error 502 Bad Gateway

1. Verificar que el backend está corriendo:
```bash
curl http://localhost:8001/health
```

2. Verificar configuración de Nginx:
```bash
sudo nginx -t
```

3. Revisar logs de Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
```

### Frontend no carga correctamente

1. Verificar que el build se completó:
```bash
ls -la /var/www/vhosts/tu-dominio.com/app/frontend/build
```

2. Verificar permisos:
```bash
sudo chown -R www-data:www-data /var/www/vhosts/tu-dominio.com/app/frontend/build
```

---

## Comandos Útiles

### Reiniciar servicios
```bash
# Backend
sudo systemctl restart suppliersync-backend

# Nginx
sudo systemctl reload nginx
```

### Ver logs en tiempo real
```bash
# Backend
sudo journalctl -u suppliersync-backend -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Actualizar la aplicación
```bash
cd /var/www/vhosts/tu-dominio.com/app

# Obtener cambios
git pull origin main

# Actualizar backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart suppliersync-backend

# Actualizar frontend
cd ../frontend
yarn install
yarn build
```

---

## Resumen del Flujo de Despliegue

```
1. Subir código al servidor
         ↓
2. Configurar backend (.env mínimo + systemd)
         ↓
3. Compilar frontend (yarn build)
         ↓
4. Configurar Nginx en Plesk
         ↓
5. Acceder a https://tu-dominio.com/setup
         ↓
6. Configurar MongoDB + Crear SuperAdmin
         ↓
7. ¡Listo! Usar la aplicación
```

---

## Soporte

Si tienes problemas con el despliegue:
1. Revisa los logs del backend y Nginx
2. Verifica la conectividad a MongoDB
3. Asegúrate de que los puertos necesarios están abiertos

---

**SupplierSync Pro** - Gestión inteligente de catálogos de proveedores
