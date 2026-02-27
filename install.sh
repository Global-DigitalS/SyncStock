#!/bin/bash

#===============================================================================
#
#          FILE: install.sh
#
#         USAGE: sudo bash install.sh
#                sudo bash install.sh --fix-plesk
#
#   DESCRIPTION: Script de instalación automática de SupplierSync Pro
#                Optimizado para Plesk Obsidian con Document Root en app/
#
#       VERSION: 2.0.0
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
IS_PLESK="no"
PLESK_USER=""

#-------------------------------------------------------------------------------
# Funciones de utilidad
#-------------------------------------------------------------------------------
print_header() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}        ${CYAN}SupplierSync Pro - Instalación Automática${NC}            ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}              ${YELLOW}Optimizado para Plesk Obsidian${NC}                 ${PURPLE}║${NC}"
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

detect_plesk() {
    if [ -d "/etc/nginx/plesk.conf.d" ] || [ -d "/var/www/vhosts/system" ]; then
        IS_PLESK="yes"
        print_success "Plesk detectado"
    else
        IS_PLESK="no"
        print_info "Plesk no detectado - usando configuración estándar"
    fi
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
                python3 python3-pip python3-venv
            # Solo instalar nginx si no es Plesk (Plesk ya lo tiene)
            if [ "$IS_PLESK" != "yes" ]; then
                apt-get install -y -qq nginx certbot python3-certbot-nginx
            fi
            print_success "Dependencias instaladas (apt)"
            ;;
        centos|rhel|fedora|rocky|almalinux)
            yum install -y -q epel-release 2>/dev/null || true
            yum install -y -q curl wget git gcc make \
                python3 python3-pip python3-devel
            if [ "$IS_PLESK" != "yes" ]; then
                yum install -y -q nginx certbot python3-certbot-nginx
            fi
            print_success "Dependencias instaladas (yum)"
            ;;
        *)
            print_warning "Sistema no reconocido. Continuando..."
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
    npm install -g yarn --silent 2>/dev/null || npm install -g yarn
    
    print_success "Node.js $(node -v) instalado"
}

#-------------------------------------------------------------------------------
# Instalación de MongoDB
#-------------------------------------------------------------------------------
install_mongodb() {
    print_step "Configuración de MongoDB"
    
    echo ""
    echo -e "${YELLOW}  ¿Cómo deseas configurar MongoDB?${NC}"
    echo ""
    echo "    1) Usar MongoDB Atlas (recomendado para producción)"
    echo "    2) Instalar MongoDB localmente"
    echo "    3) Configurar más tarde desde la interfaz web (/setup)"
    echo ""
    read -p "  Selecciona una opción [1-3]: " mongo_choice
    
    case $mongo_choice in
        1)
            echo ""
            echo -e "${CYAN}  Introduce la URL de MongoDB Atlas:${NC}"
            echo -e "${YELLOW}  Ejemplo: mongodb+srv://usuario:password@cluster.mongodb.net/dbname${NC}"
            echo ""
            read -p "  URL: " MONGODB_URL
            print_success "MongoDB Atlas configurado"
            ;;
        2)
            if command -v mongod &> /dev/null; then
                print_success "MongoDB ya está instalado"
            else
                print_info "Instalando MongoDB..."
                install_mongodb_local
            fi
            MONGODB_URL="mongodb://localhost:27017"
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
            curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg 2>/dev/null || true
            CODENAME=$(lsb_release -cs)
            # Usar jammy si el codename no está soportado
            if [[ ! "$CODENAME" =~ ^(focal|jammy|noble)$ ]]; then
                CODENAME="jammy"
            fi
            echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu $CODENAME/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
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
        print_warning "MongoDB instalado pero puede requerir configuración manual"
    fi
}

#-------------------------------------------------------------------------------
# Configuración de la aplicación
#-------------------------------------------------------------------------------
setup_application() {
    print_step "Configurando la aplicación"
    
    # Determinar directorio de instalación para Plesk
    if [ "$IS_PLESK" == "yes" ]; then
        # En Plesk, el Document Root está configurado como app/
        APP_DIR="/var/www/vhosts/$DOMAIN/app"
        
        # Detectar el usuario de Plesk
        if [ -d "/var/www/vhosts/$DOMAIN" ]; then
            PLESK_USER=$(stat -c '%U' "/var/www/vhosts/$DOMAIN")
        fi
    else
        APP_DIR="/var/www/$APP_NAME"
    fi
    
    print_info "Directorio de instalación: $APP_DIR"
    
    # Crear directorio si no existe
    mkdir -p "$APP_DIR"
    
    # Verificar si el código ya existe
    if [ ! -f "$APP_DIR/backend/server.py" ]; then
        echo ""
        echo -e "${YELLOW}  No se encontró el código fuente en $APP_DIR${NC}"
        echo ""
        echo "    1) Clonar desde repositorio Git"
        echo "    2) El código ya está subido (verificar ruta)"
        echo "    3) Salir y subir el código manualmente"
        echo ""
        read -p "  Selecciona una opción [1-3]: " code_choice
        
        case $code_choice in
            1)
                read -p "  URL del repositorio Git: " GIT_URL
                # Clonar en directorio temporal y mover
                TEMP_DIR=$(mktemp -d)
                git clone "$GIT_URL" "$TEMP_DIR"
                cp -r "$TEMP_DIR"/* "$APP_DIR/"
                rm -rf "$TEMP_DIR"
                ;;
            2)
                echo ""
                read -p "  Ruta completa al código: " CODE_PATH
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
    
    print_success "Código fuente verificado en $APP_DIR"
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
    
    # Crear archivo .env para el backend
    cat > .env << EOF
MONGO_URL=${MONGODB_URL:-mongodb://localhost:27017}
DB_NAME=supplier_sync_db
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
EOF
    
    # NO crear config.json - dejar que se configure desde /setup
    # Esto asegura que el usuario configure MongoDB Atlas desde la UI
    
    print_success "Backend configurado"
    
    # Crear servicio systemd
    print_info "Creando servicio systemd..."
    
    # Determinar usuario para el servicio
    if [ "$IS_PLESK" == "yes" ] && [ -n "$PLESK_USER" ]; then
        SERVICE_USER="$PLESK_USER"
        SERVICE_GROUP="psacln"
    else
        SERVICE_USER="www-data"
        SERVICE_GROUP="www-data"
    fi
    
    cat > /etc/systemd/system/${APP_NAME}-backend.service << EOF
[Unit]
Description=SupplierSync Pro Backend
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Ajustar permisos
    chown -R $SERVICE_USER:$SERVICE_GROUP "$APP_DIR/backend"
    
    # Habilitar e iniciar servicio
    systemctl daemon-reload
    systemctl enable ${APP_NAME}-backend
    systemctl start ${APP_NAME}-backend
    
    sleep 3
    
    if systemctl is-active --quiet ${APP_NAME}-backend; then
        print_success "Backend ejecutándose correctamente"
    else
        print_error "Error al iniciar el backend"
        journalctl -u ${APP_NAME}-backend --no-pager -n 30
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
    cat > .env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false
EOF
    
    # Instalar dependencias
    print_info "Instalando dependencias de Node.js..."
    yarn install --silent 2>/dev/null || yarn install
    
    # Compilar para producción
    print_info "Compilando para producción (esto puede tardar unos minutos)..."
    yarn build
    
    if [ ! -d "build" ]; then
        print_error "Error al compilar el frontend"
        exit 1
    fi
    
    print_success "Frontend compilado correctamente"
}

#-------------------------------------------------------------------------------
# Configuración de Nginx para Plesk
#-------------------------------------------------------------------------------
setup_nginx_plesk() {
    print_step "Configurando Nginx para Plesk (Document Root: app/frontend/build)"
    
    FRONTEND_BUILD="$APP_DIR/frontend/build"
    
    if [ ! -d "$FRONTEND_BUILD" ]; then
        print_error "No se encontró el build del frontend en $FRONTEND_BUILD"
        exit 1
    fi
    
    # Establecer permisos correctos para Plesk
    if [ -n "$PLESK_USER" ]; then
        chown -R "$PLESK_USER:psacln" "$APP_DIR"
        chmod -R 755 "$APP_DIR"
        print_success "Permisos establecidos para usuario $PLESK_USER"
    fi
    
    # Crear configuración de Nginx para Plesk
    # Con HashRouter no necesitamos configuración especial para SPA
    # Solo proxy para el API
    PLESK_NGINX_DIR="/var/www/vhosts/system/$DOMAIN/conf"
    
    if [ ! -d "$PLESK_NGINX_DIR" ]; then
        mkdir -p "$PLESK_NGINX_DIR"
    fi
    
    print_info "Creando configuración de Nginx..."
    
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << 'NGINX_EOF'
# SupplierSync Pro - Configuración Nginx para Plesk
# Document Root: app/frontend/build
# Nota: Usamos HashRouter, no se requiere configuración especial para SPA

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
NGINX_EOF
    
    print_success "Configuración de Nginx creada"
    
    # Verificar y recargar Nginx
    print_info "Verificando configuración de Nginx..."
    
    if nginx -t 2>&1; then
        systemctl reload nginx 2>/dev/null || service nginx reload 2>/dev/null
        print_success "Nginx recargado correctamente"
    else
        print_warning "Advertencia en configuración de Nginx"
        print_info "Puede ser necesario recargar manualmente desde Plesk"
    fi
    
    # Crear script de actualización para futuros deploys
    cat > "$APP_DIR/update-frontend.sh" << EOF
#!/bin/bash
# Script para actualizar el frontend después de cambios
# Uso: sudo bash update-frontend.sh

echo "Actualizando frontend..."

cd $APP_DIR/frontend

# Instalar nuevas dependencias si las hay
yarn install

# Compilar
GENERATE_SOURCEMAP=false yarn build

# Establecer permisos
chown -R $PLESK_USER:psacln $APP_DIR
chmod -R 755 $APP_DIR

echo "Frontend actualizado correctamente"
EOF
    chmod +x "$APP_DIR/update-frontend.sh"
    
    print_success "Script de actualización creado: $APP_DIR/update-frontend.sh"
    
    # Mostrar instrucciones para configurar Document Root en Plesk
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  ⚠ IMPORTANTE: Configurar en Plesk${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${CYAN}1. Ve a Plesk → Dominios → $DOMAIN${NC}"
    echo -e "  ${CYAN}2. Haz clic en 'Hosting Settings'${NC}"
    echo -e "  ${CYAN}3. Cambia 'Document Root' a:${NC}"
    echo ""
    echo -e "     ${GREEN}app/frontend/build${NC}"
    echo ""
    echo -e "  ${CYAN}4. Guarda los cambios${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# Configuración de Nginx estándar (sin Plesk)
#-------------------------------------------------------------------------------
setup_nginx_standard() {
    print_step "Configurando Nginx estándar"
    
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirigir a HTTPS (descomentar después de configurar SSL)
    # return 301 https://\$server_name\$request_uri;

    root $APP_DIR/frontend/build;
    index index.html;

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

    # SPA Fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Cache para estáticos
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Habilitar sitio
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Eliminar default si existe
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    
    # Verificar y recargar
    nginx -t
    systemctl reload nginx
    
    print_success "Nginx configurado correctamente"
}

#-------------------------------------------------------------------------------
# Configuración de SSL
#-------------------------------------------------------------------------------
setup_ssl() {
    print_step "Configuración de SSL"
    
    if [ "$IS_PLESK" == "yes" ]; then
        echo ""
        print_info "Para configurar SSL en Plesk:"
        echo ""
        echo -e "    1. Ve a ${CYAN}Plesk → Dominios → $DOMAIN${NC}"
        echo -e "    2. Haz clic en ${CYAN}SSL/TLS Certificates${NC}"
        echo -e "    3. Selecciona ${CYAN}Let's Encrypt${NC}"
        echo -e "    4. Marca ${CYAN}Redirect from HTTP to HTTPS${NC}"
        echo -e "    5. Haz clic en ${CYAN}Get it free${NC}"
        echo ""
        return
    fi
    
    echo ""
    echo -e "${YELLOW}  ¿Deseas configurar SSL con Let's Encrypt?${NC}"
    echo ""
    echo "    1) Sí, configurar SSL ahora"
    echo "    2) No, lo haré más tarde"
    echo ""
    read -p "  Selecciona una opción [1-2]: " ssl_choice
    
    if [ "$ssl_choice" == "1" ]; then
        read -p "  Email para Let's Encrypt: " SSL_EMAIL
        
        if [ -n "$SSL_EMAIL" ]; then
            certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $SSL_EMAIL
            print_success "SSL configurado correctamente"
        fi
    fi
}

#-------------------------------------------------------------------------------
# Resumen final
#-------------------------------------------------------------------------------
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}            ${CYAN}¡Instalación Completada!${NC}                           ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${PURPLE}Accede a tu aplicación:${NC}"
    echo ""
    echo -e "    ${CYAN}https://$DOMAIN/#/setup${NC}  ← Configuración inicial"
    echo -e "    ${CYAN}https://$DOMAIN/#/login${NC}  ← Iniciar sesión"
    echo -e "    ${CYAN}https://$DOMAIN${NC}          ← Aplicación"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${YELLOW}Comandos útiles:${NC}"
    echo ""
    echo -e "    Ver logs del backend:"
    echo -e "    ${CYAN}journalctl -u ${APP_NAME}-backend -f${NC}"
    echo ""
    echo -e "    Reiniciar backend:"
    echo -e "    ${CYAN}systemctl restart ${APP_NAME}-backend${NC}"
    echo ""
    echo -e "    Actualizar frontend después de cambios:"
    echo -e "    ${CYAN}sudo bash $APP_DIR/update-frontend.sh${NC}"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -z "$MONGODB_URL" ]; then
        echo -e "  ${YELLOW}⚠ IMPORTANTE:${NC}"
        echo -e "    Debes configurar MongoDB en ${CYAN}https://$DOMAIN/#/setup${NC}"
        echo ""
    fi
    
    if [ "$IS_PLESK" == "yes" ]; then
        echo -e "  ${YELLOW}Configuración de Plesk:${NC}"
        echo -e "    • Document Root: ${CYAN}app/frontend/build${NC}"
        echo -e "    • SSL: Configurar desde Plesk → SSL/TLS Certificates"
        echo ""
    fi
}

#-------------------------------------------------------------------------------
# Función de reparación rápida para Plesk
#-------------------------------------------------------------------------------
fix_plesk() {
    print_header
    echo -e "${CYAN}  Modo: Reparación rápida para Plesk${NC}"
    echo ""
    
    read -p "  Introduce tu dominio: " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        print_error "El dominio es obligatorio"
        exit 1
    fi
    
    APP_DIR="/var/www/vhosts/$DOMAIN/app"
    PLESK_USER=$(stat -c '%U' "/var/www/vhosts/$DOMAIN" 2>/dev/null)
    
    print_info "Dominio: $DOMAIN"
    print_info "Directorio: $APP_DIR"
    print_info "Usuario Plesk: $PLESK_USER"
    echo ""
    
    # 1. Verificar que existe el código
    if [ ! -d "$APP_DIR/frontend" ]; then
        print_error "No se encontró el frontend en $APP_DIR/frontend"
        exit 1
    fi
    
    # 2. Compilar frontend si no existe el build
    if [ ! -d "$APP_DIR/frontend/build" ]; then
        print_info "Compilando frontend..."
        cd "$APP_DIR/frontend"
        
        # Crear .env si no existe
        if [ ! -f ".env" ]; then
            echo "REACT_APP_BACKEND_URL=https://$DOMAIN" > .env
        fi
        
        yarn install
        GENERATE_SOURCEMAP=false yarn build
    fi
    
    print_success "Frontend build existe en $APP_DIR/frontend/build"
    
    # 3. Establecer permisos
    if [ -n "$PLESK_USER" ] && [ "$PLESK_USER" != "root" ]; then
        chown -R "$PLESK_USER:psacln" "$APP_DIR"
        chmod -R 755 "$APP_DIR"
        print_success "Permisos establecidos"
    fi
    
    # 4. Configurar Nginx - Solo proxy para API (HashRouter no necesita más)
    PLESK_NGINX_DIR="/var/www/vhosts/system/$DOMAIN/conf"
    mkdir -p "$PLESK_NGINX_DIR"
    
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << 'NGINX_EOF'
# SupplierSync Pro - Configuración para Plesk
# Document Root: app/frontend/build
# Nota: Usamos HashRouter, no se requiere configuración especial para SPA

location /api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}

location /health {
    proxy_pass http://127.0.0.1:8001/health;
}

location /ws/ {
    proxy_pass http://127.0.0.1:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
NGINX_EOF
    
    print_success "Configuración Nginx actualizada"
    
    # 5. Recargar Nginx
    if nginx -t 2>&1; then
        systemctl reload nginx 2>/dev/null || service nginx reload
        print_success "Nginx recargado"
    else
        print_warning "Verifica la configuración de Nginx manualmente"
    fi
    
    # 6. Verificar backend
    if systemctl is-active --quiet ${APP_NAME}-backend 2>/dev/null; then
        print_success "Backend está corriendo"
    else
        print_warning "Backend no está corriendo"
        print_info "Iniciando backend..."
        systemctl start ${APP_NAME}-backend 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✓ Reparación completada${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}  ⚠ IMPORTANTE: Verifica en Plesk${NC}"
    echo ""
    echo -e "  ${CYAN}1. Ve a Plesk → Dominios → $DOMAIN → Hosting Settings${NC}"
    echo -e "  ${CYAN}2. Document Root debe ser: ${GREEN}app/frontend/build${NC}"
    echo -e "  ${CYAN}3. Guarda si hiciste cambios${NC}"
    echo ""
    echo -e "  ${GREEN}Accede a: https://$DOMAIN/#/setup${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# Función principal
#-------------------------------------------------------------------------------
main() {
    print_header
    check_root
    detect_os
    detect_plesk
    
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
    
    # Configurar Nginx según el entorno
    if [ "$IS_PLESK" == "yes" ]; then
        setup_nginx_plesk
    else
        setup_nginx_standard
    fi
    
    # SSL
    setup_ssl
    
    # Mostrar resumen
    print_summary
}

#-------------------------------------------------------------------------------
# Punto de entrada
#-------------------------------------------------------------------------------
case "${1:-}" in
    --fix-plesk|-f)
        check_root
        fix_plesk
        ;;
    --help|-h)
        echo ""
        echo "SupplierSync Pro - Script de Instalación"
        echo ""
        echo "Uso:"
        echo "  sudo bash install.sh              Instalación completa"
        echo "  sudo bash install.sh --fix-plesk  Reparar configuración en Plesk"
        echo "  sudo bash install.sh --help       Mostrar esta ayuda"
        echo ""
        ;;
    *)
        main
        ;;
esac
