#!/bin/bash

#===============================================================================
#
#          FILE: install.sh
#
#         USAGE: curl -sSL https://tu-repo.com/install.sh | sudo bash
#                o
#                sudo bash install.sh
#
#   DESCRIPTION: Script de instalación automática de SupplierSync Pro
#                Configura backend, frontend, MongoDB y Nginx automáticamente.
#
#       VERSION: 1.0.0
#        AUTHOR: SupplierSync Pro
#
#===============================================================================

set -e

#-------------------------------------------------------------------------------
# Colores para output
#-------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# Variables de configuración
#-------------------------------------------------------------------------------
APP_NAME="suppliersync"
APP_DIR=""
DOMAIN=""
INSTALL_MONGODB="no"
MONGODB_URL=""
NGINX_CONFIGURED="no"

#-------------------------------------------------------------------------------
# Funciones de utilidad
#-------------------------------------------------------------------------------
print_header() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}        ${CYAN}SupplierSync Pro - Instalación Automática${NC}            ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  ➤ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}  ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        OS_ID=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="Red Hat"
        OS_ID="rhel"
    else
        OS=$(uname -s)
        OS_ID="unknown"
    fi
    
    print_info "Sistema detectado: $OS"
}

#-------------------------------------------------------------------------------
# Instalación de dependencias del sistema
#-------------------------------------------------------------------------------
install_system_deps() {
    print_step "Instalando dependencias del sistema"
    
    case $OS_ID in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq curl wget git build-essential software-properties-common \
                python3 python3-pip python3-venv \
                nginx certbot python3-certbot-nginx
            print_success "Dependencias instaladas (apt)"
            ;;
        centos|rhel|fedora|rocky|almalinux)
            yum install -y -q epel-release
            yum install -y -q curl wget git gcc make \
                python3 python3-pip python3-devel \
                nginx certbot python3-certbot-nginx
            print_success "Dependencias instaladas (yum)"
            ;;
        *)
            print_warning "Sistema no reconocido. Instalando manualmente..."
            ;;
    esac
}

#-------------------------------------------------------------------------------
# Instalación de Node.js
#-------------------------------------------------------------------------------
install_nodejs() {
    print_step "Verificando Node.js"
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_success "Node.js $(node -v) ya instalado"
            return
        fi
    fi
    
    print_info "Instalando Node.js 20 LTS..."
    
    case $OS_ID in
        ubuntu|debian)
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
            apt-get install -y -qq nodejs
            ;;
        centos|rhel|fedora|rocky|almalinux)
            curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
            yum install -y -q nodejs
            ;;
    esac
    
    # Instalar yarn
    npm install -g yarn --silent
    
    print_success "Node.js $(node -v) instalado"
    print_success "Yarn $(yarn -v) instalado"
}

#-------------------------------------------------------------------------------
# Instalación de MongoDB
#-------------------------------------------------------------------------------
install_mongodb() {
    print_step "Configuración de MongoDB"
    
    if command -v mongod &> /dev/null; then
        print_success "MongoDB ya está instalado"
        MONGODB_URL="mongodb://localhost:27017"
        return
    fi
    
    echo ""
    echo -e "${YELLOW}  MongoDB no está instalado. ¿Qué deseas hacer?${NC}"
    echo ""
    echo "    1) Instalar MongoDB localmente (recomendado para desarrollo)"
    echo "    2) Usar MongoDB Atlas u otro servidor externo"
    echo "    3) Configurar más tarde desde la interfaz web"
    echo ""
    read -p "  Selecciona una opción [1-3]: " mongo_choice
    
    case $mongo_choice in
        1)
            print_info "Instalando MongoDB..."
            install_mongodb_local
            MONGODB_URL="mongodb://localhost:27017"
            ;;
        2)
            echo ""
            read -p "  Introduce la URL de MongoDB: " MONGODB_URL
            print_info "Usarás: $MONGODB_URL"
            ;;
        3)
            print_info "Configurarás MongoDB desde https://$DOMAIN/setup"
            MONGODB_URL=""
            ;;
    esac
}

install_mongodb_local() {
    case $OS_ID in
        ubuntu|debian)
            # Importar clave GPG
            curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
            
            # Añadir repositorio
            echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
            
            apt-get update -qq
            apt-get install -y -qq mongodb-org
            
            systemctl enable mongod
            systemctl start mongod
            ;;
        centos|rhel|fedora|rocky|almalinux)
            cat > /etc/yum.repos.d/mongodb-org-7.0.repo << 'EOF'
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
EOF
            yum install -y -q mongodb-org
            systemctl enable mongod
            systemctl start mongod
            ;;
    esac
    
    sleep 2
    
    if systemctl is-active --quiet mongod; then
        print_success "MongoDB instalado y ejecutándose"
    else
        print_warning "MongoDB instalado pero no se pudo iniciar automáticamente"
    fi
}

#-------------------------------------------------------------------------------
# Configuración de la aplicación
#-------------------------------------------------------------------------------
setup_application() {
    print_step "Configurando la aplicación"
    
    # Determinar directorio de instalación
    if [ -z "$APP_DIR" ]; then
        if [ -d "/var/www/vhosts/$DOMAIN" ]; then
            APP_DIR="/var/www/vhosts/$DOMAIN/app"
        elif [ -d "/var/www/$DOMAIN" ]; then
            APP_DIR="/var/www/$DOMAIN/app"
        else
            APP_DIR="/var/www/$APP_NAME"
        fi
    fi
    
    print_info "Directorio de instalación: $APP_DIR"
    
    # Crear directorio si no existe
    mkdir -p "$APP_DIR"
    
    # Si el código no existe, preguntar cómo obtenerlo
    if [ ! -f "$APP_DIR/backend/server.py" ]; then
        echo ""
        echo -e "${YELLOW}  No se encontró el código fuente en $APP_DIR${NC}"
        echo ""
        echo "    1) Clonar desde repositorio Git"
        echo "    2) El código ya está en otro directorio"
        echo "    3) Salir y subir el código manualmente"
        echo ""
        read -p "  Selecciona una opción [1-3]: " code_choice
        
        case $code_choice in
            1)
                read -p "  URL del repositorio Git: " GIT_URL
                git clone "$GIT_URL" "$APP_DIR"
                ;;
            2)
                read -p "  Ruta al directorio con el código: " CODE_PATH
                if [ -d "$CODE_PATH/backend" ]; then
                    cp -r "$CODE_PATH"/* "$APP_DIR/"
                else
                    print_error "No se encontró el código en $CODE_PATH"
                    exit 1
                fi
                ;;
            3)
                echo ""
                print_info "Sube el código a $APP_DIR y vuelve a ejecutar el script"
                exit 0
                ;;
        esac
    fi
    
    print_success "Código fuente verificado"
}

#-------------------------------------------------------------------------------
# Configuración del Backend
#-------------------------------------------------------------------------------
setup_backend() {
    print_step "Configurando Backend (Python/FastAPI)"
    
    cd "$APP_DIR/backend"
    
    # Crear entorno virtual
    print_info "Creando entorno virtual de Python..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependencias
    print_info "Instalando dependencias de Python..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    
    # Crear archivo de configuración inicial si MongoDB está configurado
    if [ -n "$MONGODB_URL" ]; then
        cat > config.json << EOF
{
  "mongo_url": "$MONGODB_URL",
  "db_name": "supplier_sync_db",
  "jwt_secret": "",
  "cors_origins": "https://$DOMAIN",
  "is_configured": false
}
EOF
        print_success "Configuración inicial creada"
    fi
    
    # Crear servicio systemd
    print_info "Creando servicio systemd..."
    
    cat > /etc/systemd/system/${APP_NAME}-backend.service << EOF
[Unit]
Description=SupplierSync Pro Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Ajustar permisos
    chown -R www-data:www-data "$APP_DIR/backend"
    
    # Habilitar e iniciar servicio
    systemctl daemon-reload
    systemctl enable ${APP_NAME}-backend
    systemctl start ${APP_NAME}-backend
    
    sleep 2
    
    if systemctl is-active --quiet ${APP_NAME}-backend; then
        print_success "Backend ejecutándose correctamente"
    else
        print_error "Error al iniciar el backend"
        journalctl -u ${APP_NAME}-backend --no-pager -n 20
        exit 1
    fi
}

#-------------------------------------------------------------------------------
# Configuración del Frontend
#-------------------------------------------------------------------------------
setup_frontend() {
    print_step "Configurando Frontend (React)"
    
    cd "$APP_DIR/frontend"
    
    # Crear archivo .env
    echo "REACT_APP_BACKEND_URL=https://$DOMAIN" > .env
    
    # Instalar dependencias
    print_info "Instalando dependencias de Node.js..."
    yarn install --silent
    
    # Compilar para producción
    print_info "Compilando para producción (esto puede tardar unos minutos)..."
    yarn build
    
    # Ajustar permisos
    chown -R www-data:www-data "$APP_DIR/frontend"
    
    print_success "Frontend compilado correctamente"
}

#-------------------------------------------------------------------------------
# Configuración de Nginx
#-------------------------------------------------------------------------------
setup_nginx() {
    print_step "Configurando Nginx"
    
    # Detectar si es Plesk
    if [ -d "/etc/nginx/plesk.conf.d" ]; then
        print_info "Detectado Plesk - Configurando vía includes..."
        setup_nginx_plesk
    else
        print_info "Configurando Nginx estándar..."
        setup_nginx_standard
    fi
}

setup_nginx_plesk() {
    # Para Plesk, configurar correctamente el frontend SPA y el proxy del API
    print_info "Configurando Nginx para Plesk..."
    
    # Directorios de Plesk
    PLESK_NGINX_DIR="/var/www/vhosts/system/$DOMAIN/conf"
    PLESK_HTTPDOCS="/var/www/vhosts/$DOMAIN/httpdocs"
    
    # 1. Copiar el frontend build a httpdocs (donde Plesk sirve los archivos)
    if [ -d "$APP_DIR/frontend/build" ]; then
        print_info "Copiando frontend build a httpdocs..."
        
        # Hacer backup del httpdocs actual si existe contenido
        if [ -d "$PLESK_HTTPDOCS" ] && [ "$(ls -A $PLESK_HTTPDOCS 2>/dev/null)" ]; then
            BACKUP_DIR="/var/www/vhosts/$DOMAIN/httpdocs_backup_$(date +%Y%m%d_%H%M%S)"
            mv "$PLESK_HTTPDOCS" "$BACKUP_DIR"
            print_info "Backup creado en: $BACKUP_DIR"
        fi
        
        # Crear httpdocs y copiar el build
        mkdir -p "$PLESK_HTTPDOCS"
        cp -r "$APP_DIR/frontend/build/"* "$PLESK_HTTPDOCS/"
        
        # Establecer permisos correctos para Plesk
        PLESK_USER=$(stat -c '%U' "/var/www/vhosts/$DOMAIN")
        if [ -n "$PLESK_USER" ] && [ "$PLESK_USER" != "root" ]; then
            chown -R "$PLESK_USER:psacln" "$PLESK_HTTPDOCS"
        fi
        chmod -R 755 "$PLESK_HTTPDOCS"
        
        print_success "Frontend copiado a httpdocs"
    else
        print_warning "No se encontró el build del frontend en $APP_DIR/frontend/build"
        print_info "Ejecuta 'cd $APP_DIR/frontend && npm run build' primero"
    fi
    
    # 2. Crear configuración de Nginx para el proxy del API
    if [ -d "$PLESK_NGINX_DIR" ]; then
        cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << 'NGINX_EOF'
# SupplierSync Pro - Configuración Nginx para Plesk
# Generado automáticamente por install.sh
# =====================================================

# API Backend - Proxy a FastAPI
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
    
    # Buffer settings para respuestas grandes
    proxy_buffering on;
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;
}

# Health check endpoint
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 10s;
}

# WebSocket para notificaciones en tiempo real
location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}

# SPA Fallback - Todas las rutas no encontradas van a index.html
# Esto es CRÍTICO para que funcionen las rutas de React Router
location / {
    try_files $uri $uri/ /index.html;
}

# Cache para archivos estáticos
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
}
NGINX_EOF
        
        print_success "Configuración de Nginx creada en $PLESK_NGINX_DIR/nginx_custom.conf"
    else
        print_warning "No se encontró el directorio de configuración de Plesk: $PLESK_NGINX_DIR"
        print_info "Creando directorio..."
        mkdir -p "$PLESK_NGINX_DIR"
        # Reintentar crear el archivo
        setup_nginx_plesk
        return
    fi
    
    # 3. Crear script de actualización del frontend para futuros deploys
    cat > "$APP_DIR/update-frontend.sh" << EOF
#!/bin/bash
# Script para actualizar el frontend en Plesk
# Uso: sudo bash update-frontend.sh

cd $APP_DIR/frontend
npm run build

# Copiar a httpdocs
rm -rf $PLESK_HTTPDOCS/*
cp -r build/* $PLESK_HTTPDOCS/

# Establecer permisos
PLESK_USER=\$(stat -c '%U' "/var/www/vhosts/$DOMAIN")
if [ -n "\$PLESK_USER" ] && [ "\$PLESK_USER" != "root" ]; then
    chown -R "\$PLESK_USER:psacln" "$PLESK_HTTPDOCS"
fi
chmod -R 755 $PLESK_HTTPDOCS

echo "Frontend actualizado correctamente"
EOF
    chmod +x "$APP_DIR/update-frontend.sh"
    print_success "Script de actualización creado: $APP_DIR/update-frontend.sh"
    
    # 4. Recargar configuración de Nginx
    print_info "Recargando configuración de Nginx..."
    if nginx -t 2>/dev/null; then
        systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null
        print_success "Nginx recargado correctamente"
    else
        print_error "Error en la configuración de Nginx. Verifica manualmente con: nginx -t"
    fi
    
    # 5. Mostrar instrucciones adicionales para Plesk
    echo ""
    print_info "═══════════════════════════════════════════════════════════════"
    print_info "  CONFIGURACIÓN ADICIONAL EN PLESK (si es necesario):"
    print_info "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${YELLOW}  Si las rutas SPA siguen dando 404, ve a Plesk y:${NC}"
    echo ""
    echo -e "${CYAN}  1. Dominios → $DOMAIN → Apache & nginx Settings${NC}"
    echo -e "${CYAN}  2. En 'Additional nginx directives', verifica que esté:${NC}"
    echo ""
    echo -e "${GREEN}     location / {${NC}"
    echo -e "${GREEN}         try_files \$uri \$uri/ /index.html;${NC}"
    echo -e "${GREEN}     }${NC}"
    echo ""
    echo -e "${CYAN}  3. Guarda y aplica los cambios${NC}"
    echo ""
}

setup_nginx_standard() {
    # Configuración estándar de Nginx
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirigir HTTP a HTTPS (descomentar después de obtener certificado SSL)
    # return 301 https://\$server_name\$request_uri;

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8001/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }

    # Frontend
    location / {
        root $APP_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

    # Habilitar sitio
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Verificar configuración
    nginx -t
    
    # Recargar Nginx
    systemctl reload nginx
    
    print_success "Nginx configurado correctamente"
    NGINX_CONFIGURED="yes"
}

#-------------------------------------------------------------------------------
# Configuración de SSL (Let's Encrypt)
#-------------------------------------------------------------------------------
setup_ssl() {
    print_step "Configuración de SSL"
    
    echo ""
    echo -e "${YELLOW}  ¿Deseas configurar SSL con Let's Encrypt?${NC}"
    echo ""
    echo "    1) Sí, configurar SSL ahora"
    echo "    2) No, lo haré más tarde"
    echo ""
    read -p "  Selecciona una opción [1-2]: " ssl_choice
    
    if [ "$ssl_choice" == "1" ]; then
        read -p "  Email para Let's Encrypt: " SSL_EMAIL
        
        certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $SSL_EMAIL
        
        if [ $? -eq 0 ]; then
            print_success "Certificado SSL instalado correctamente"
        else
            print_warning "No se pudo instalar el certificado SSL automáticamente"
            print_info "Puedes instalarlo manualmente con: certbot --nginx -d $DOMAIN"
        fi
    else
        print_info "Puedes configurar SSL más tarde con: certbot --nginx -d $DOMAIN"
    fi
}

#-------------------------------------------------------------------------------
# Resumen final
#-------------------------------------------------------------------------------
print_summary() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}              ${GREEN}¡Instalación Completada!${NC}                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}  Resumen de la instalación:${NC}"
    echo ""
    echo -e "    ${GREEN}✓${NC} Backend:   http://localhost:8001"
    echo -e "    ${GREEN}✓${NC} Frontend:  $APP_DIR/frontend/build"
    echo -e "    ${GREEN}✓${NC} Servicio:  ${APP_NAME}-backend.service"
    
    if [ -n "$MONGODB_URL" ]; then
        echo -e "    ${GREEN}✓${NC} MongoDB:   $MONGODB_URL"
    else
        echo -e "    ${YELLOW}⚠${NC} MongoDB:   Configurar desde la web"
    fi
    
    echo ""
    echo -e "${CYAN}  Próximos pasos:${NC}"
    echo ""
    echo -e "    ${BLUE}1.${NC} Abre tu navegador y ve a:"
    echo ""
    echo -e "       ${GREEN}https://$DOMAIN/setup${NC}"
    echo ""
    echo -e "    ${BLUE}2.${NC} Configura MongoDB (si no lo hiciste)"
    echo -e "    ${BLUE}3.${NC} Crea tu usuario SuperAdmin"
    echo -e "    ${BLUE}4.${NC} ¡Comienza a usar SupplierSync Pro!"
    echo ""
    echo -e "${CYAN}  Comandos útiles:${NC}"
    echo ""
    echo -e "    Ver estado:     ${YELLOW}systemctl status ${APP_NAME}-backend${NC}"
    echo -e "    Ver logs:       ${YELLOW}journalctl -u ${APP_NAME}-backend -f${NC}"
    echo -e "    Reiniciar:      ${YELLOW}systemctl restart ${APP_NAME}-backend${NC}"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# Función principal
#-------------------------------------------------------------------------------
main() {
    print_header
    check_root
    detect_os
    
    # Preguntar dominio
    echo ""
    read -p "  Introduce tu dominio (ej: app.miempresa.com): " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        print_error "El dominio es obligatorio"
        exit 1
    fi
    
    print_info "Dominio: $DOMAIN"
    
    # Instalar dependencias
    install_system_deps
    install_nodejs
    install_mongodb
    
    # Configurar aplicación
    setup_application
    setup_backend
    setup_frontend
    setup_nginx
    
    # SSL opcional
    if [ "$NGINX_CONFIGURED" == "yes" ]; then
        setup_ssl
    fi
    
    # Mostrar resumen
    print_summary
}

#-------------------------------------------------------------------------------
# Función de reparación rápida para Plesk (ejecutar si hay problemas)
#-------------------------------------------------------------------------------
fix_plesk_spa() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}     ${CYAN}SupplierSync Pro - Reparación SPA para Plesk${NC}             ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    read -p "  Introduce tu dominio: " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}  ✗ El dominio es obligatorio${NC}"
        exit 1
    fi
    
    # Detectar directorio de la app
    APP_DIR="/var/www/vhosts/$DOMAIN/app"
    if [ ! -d "$APP_DIR" ]; then
        APP_DIR="/var/www/vhosts/$DOMAIN/httpdocs/app"
    fi
    
    PLESK_HTTPDOCS="/var/www/vhosts/$DOMAIN/httpdocs"
    PLESK_NGINX_DIR="/var/www/vhosts/system/$DOMAIN/conf"
    
    echo ""
    echo -e "${CYAN}  ℹ Directorio de la app: $APP_DIR${NC}"
    echo -e "${CYAN}  ℹ Httpdocs: $PLESK_HTTPDOCS${NC}"
    echo -e "${CYAN}  ℹ Nginx config: $PLESK_NGINX_DIR${NC}"
    echo ""
    
    # 1. Verificar que existe el build
    if [ ! -d "$APP_DIR/frontend/build" ]; then
        echo -e "${YELLOW}  ⚠ No se encontró el build del frontend${NC}"
        echo -e "${CYAN}  ℹ Compilando frontend...${NC}"
        cd "$APP_DIR/frontend"
        npm run build
    fi
    
    # 2. Copiar build a httpdocs
    echo -e "${CYAN}  ℹ Copiando frontend a httpdocs...${NC}"
    
    # Limpiar httpdocs pero mantener archivos ocultos importantes
    find "$PLESK_HTTPDOCS" -mindepth 1 -maxdepth 1 ! -name '.*' -exec rm -rf {} \; 2>/dev/null || true
    
    # Copiar build
    cp -r "$APP_DIR/frontend/build/"* "$PLESK_HTTPDOCS/"
    
    # Establecer permisos
    PLESK_USER=$(stat -c '%U' "/var/www/vhosts/$DOMAIN")
    if [ -n "$PLESK_USER" ] && [ "$PLESK_USER" != "root" ]; then
        chown -R "$PLESK_USER:psacln" "$PLESK_HTTPDOCS"
    fi
    chmod -R 755 "$PLESK_HTTPDOCS"
    
    echo -e "${GREEN}  ✓ Frontend copiado${NC}"
    
    # 3. Crear/actualizar configuración de Nginx
    echo -e "${CYAN}  ℹ Actualizando configuración de Nginx...${NC}"
    
    mkdir -p "$PLESK_NGINX_DIR"
    
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << 'NGINX_CONF'
# SupplierSync Pro - Configuración Nginx para Plesk
# Reparación automática

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
    proxy_connect_timeout 75s;
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

# SPA Fallback - CRÍTICO para React Router
location / {
    try_files $uri $uri/ /index.html;
}

# Cache para estáticos
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
}
NGINX_CONF

    echo -e "${GREEN}  ✓ Configuración de Nginx actualizada${NC}"
    
    # 4. Recargar Nginx
    echo -e "${CYAN}  ℹ Recargando Nginx...${NC}"
    
    if nginx -t 2>/dev/null; then
        systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null
        echo -e "${GREEN}  ✓ Nginx recargado${NC}"
    else
        echo -e "${RED}  ✗ Error en configuración de Nginx${NC}"
        nginx -t
        exit 1
    fi
    
    # 5. Verificar que el backend está corriendo
    echo -e "${CYAN}  ℹ Verificando backend...${NC}"
    
    if systemctl is-active --quiet suppliersync-backend 2>/dev/null; then
        echo -e "${GREEN}  ✓ Backend está corriendo${NC}"
    else
        echo -e "${YELLOW}  ⚠ Backend no está corriendo. Iniciando...${NC}"
        systemctl start suppliersync-backend 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✓ Reparación completada${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  Prueba acceder a: ${CYAN}https://$DOMAIN/setup${NC}"
    echo ""
    echo -e "  Si sigue sin funcionar, ve a Plesk:"
    echo -e "    ${YELLOW}Dominios → $DOMAIN → Apache & nginx Settings${NC}"
    echo -e "    Y asegúrate de que 'Proxy mode' esté ${GREEN}DESACTIVADO${NC}"
    echo ""
}

# Verificar si se ejecutó con argumento --fix-plesk
if [ "$1" == "--fix-plesk" ] || [ "$1" == "-f" ]; then
    fix_plesk_spa
    exit 0
fi

# Ejecutar instalación normal
main "$@"
