#!/bin/bash

#===============================================================================
#
#          FILE: install.sh
#
#         USAGE: sudo bash install.sh
#                sudo bash install.sh --fix-plesk
#
#   DESCRIPTION: Script de instalación automática de SyncStock
#                Optimizado para Plesk Obsidian con Document Root en app/
#
#       VERSION: 2.0.0
#        AUTHOR: SyncStock
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
APP_NAME="syncstock"
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
    echo -e "${PURPLE}║${NC}        ${CYAN}SyncStock - Instalación Automática${NC}            ${PURPLE}║${NC}"
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
        # Detectar si es un subdominio (ej: app.sync-stock.com)
        # Los subdominios en Plesk se guardan dentro del dominio principal
        SUBDOMAIN_PARTS=$(echo "$DOMAIN" | tr '.' '\n' | wc -l)
        
        if [ "$SUBDOMAIN_PARTS" -ge 3 ]; then
            # Es un subdominio (tiene 3 o más partes: app.sync-stock.com)
            # Extraer el dominio principal (últimas 2 partes)
            MAIN_DOMAIN=$(echo "$DOMAIN" | rev | cut -d'.' -f1-2 | rev)
            IS_SUBDOMAIN="yes"
            
            # En Plesk, subdominios están en: /var/www/vhosts/DOMINIO_PRINCIPAL/SUBDOMINIO/
            if [ -d "/var/www/vhosts/$MAIN_DOMAIN/$DOMAIN" ]; then
                # Estructura de subdominio de Plesk
                APP_DIR="/var/www/vhosts/$MAIN_DOMAIN/$DOMAIN/app"
                PLESK_VHOST_DIR="/var/www/vhosts/$MAIN_DOMAIN"
                print_info "Detectado como subdominio de $MAIN_DOMAIN"
            elif [ -d "/var/www/vhosts/$DOMAIN" ]; then
                # El subdominio tiene su propio vhost (dominio adicional)
                APP_DIR="/var/www/vhosts/$DOMAIN/app"
                PLESK_VHOST_DIR="/var/www/vhosts/$DOMAIN"
                IS_SUBDOMAIN="no"
            else
                print_error "No se encontró el directorio del dominio $DOMAIN"
                echo ""
                echo -e "  ${YELLOW}Rutas buscadas:${NC}"
                echo -e "    - /var/www/vhosts/$MAIN_DOMAIN/$DOMAIN"
                echo -e "    - /var/www/vhosts/$DOMAIN"
                echo ""
                read -p "  Introduce la ruta correcta al vhost: " CUSTOM_VHOST
                if [ -d "$CUSTOM_VHOST" ]; then
                    APP_DIR="$CUSTOM_VHOST/app"
                    PLESK_VHOST_DIR="$CUSTOM_VHOST"
                else
                    print_error "La ruta $CUSTOM_VHOST no existe"
                    exit 1
                fi
            fi
        else
            # Es un dominio principal (solo 2 partes: sync-stock.com)
            IS_SUBDOMAIN="no"
            APP_DIR="/var/www/vhosts/$DOMAIN/app"
            PLESK_VHOST_DIR="/var/www/vhosts/$DOMAIN"
        fi
        
        # Detectar el usuario de Plesk
        if [ -d "$PLESK_VHOST_DIR" ]; then
            PLESK_USER=$(stat -c '%U' "$PLESK_VHOST_DIR")
        fi
        
        print_info "Directorio vhost: $PLESK_VHOST_DIR"
        print_info "Usuario Plesk: $PLESK_USER"
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
    
    # Generar nombre de servicio único basado en el dominio
    # Reemplazar puntos por guiones para el nombre del servicio
    SERVICE_NAME=$(echo "$DOMAIN" | tr '.' '-' | tr '[:upper:]' '[:lower:]')
    SERVICE_NAME="${SERVICE_NAME}-backend"
    
    # Determinar puerto disponible
    # Buscar puertos en uso por otros servicios de la aplicación
    BACKEND_PORT=8001
    while netstat -tuln 2>/dev/null | grep -q ":$BACKEND_PORT " || \
          ss -tuln 2>/dev/null | grep -q ":$BACKEND_PORT " || \
          grep -r "port $BACKEND_PORT\|port=$BACKEND_PORT\|:$BACKEND_PORT" /etc/systemd/system/*-backend.service 2>/dev/null | grep -v "$SERVICE_NAME" | grep -q .; do
        BACKEND_PORT=$((BACKEND_PORT + 1))
        if [ "$BACKEND_PORT" -gt 8099 ]; then
            print_error "No se encontró un puerto disponible entre 8001-8099"
            exit 1
        fi
    done
    
    print_info "Puerto del backend: $BACKEND_PORT"
    print_info "Nombre del servicio: $SERVICE_NAME"
    
    # Guardar el puerto para usarlo en la configuración de nginx
    echo "$BACKEND_PORT" > "$APP_DIR/.backend_port"
    
    # Verificar si existe configuración persistente
    # Usar directorio específico por dominio
    PERSISTENT_CONFIG_DIR="/etc/syncstock/$DOMAIN"
    PERSISTENT_CONFIG="$PERSISTENT_CONFIG_DIR/config.json"
    
    mkdir -p "$PERSISTENT_CONFIG_DIR"
    
    if [ -f "$PERSISTENT_CONFIG" ]; then
        print_success "Configuración existente detectada en $PERSISTENT_CONFIG"
        print_info "La configuración se preservará durante la actualización"
        
        # Extraer MONGO_URL y DB_NAME de la configuración existente para el .env
        if command -v python3 &> /dev/null; then
            EXISTING_MONGO=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('mongo_url',''))" 2>/dev/null || echo "")
            EXISTING_DB=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('db_name','syncstock_db'))" 2>/dev/null || echo "syncstock_db")
            
            if [ -n "$EXISTING_MONGO" ]; then
                MONGODB_URL="$EXISTING_MONGO"
                print_success "Usando MongoDB URL de la configuración existente"
            fi
        fi
    else
        print_info "No se encontró configuración existente"
        print_info "Configurarás la aplicación desde https://$DOMAIN/#/setup"
    fi
    
    # Crear archivo .env para el backend
    cat > .env << EOF
MONGO_URL=${MONGODB_URL:-mongodb://localhost:27017}
DB_NAME=${EXISTING_DB:-syncstock_db}
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CONFIG_PATH=$PERSISTENT_CONFIG
EOF
    
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
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Backend for $DOMAIN
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
Environment="CONFIG_PATH=$PERSISTENT_CONFIG"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Crear directorio de configuración persistente y establecer permisos
    mkdir -p "$PERSISTENT_CONFIG_DIR"
    chown -R $SERVICE_USER:$SERVICE_GROUP "$PERSISTENT_CONFIG_DIR" 2>/dev/null || true
    chmod 755 "$PERSISTENT_CONFIG_DIR"

    # Configurar permisos del archivo de configuración (solo lectura para el servicio)
    if [ -f "$PERSISTENT_CONFIG_DIR/config.json" ]; then
        chmod 600 "$PERSISTENT_CONFIG_DIR/config.json"
        chown $SERVICE_USER:$SERVICE_GROUP "$PERSISTENT_CONFIG_DIR/config.json"
    fi

    # Ajustar permisos del backend
    chown -R $SERVICE_USER:$SERVICE_GROUP "$APP_DIR/backend"

    # Establecer permisos seguros en directorios del backend
    # Directorios: 755 (rwxr-xr-x - propietario: leer+escribir+ejecutar, otros: solo lectura)
    find "$APP_DIR/backend" -type d -exec chmod 755 {} \; 2>/dev/null || true
    # Archivos: 644 (rw-r--r-- - propietario: leer+escribir, otros: solo lectura)
    find "$APP_DIR/backend" -type f -exec chmod 644 {} \; 2>/dev/null || true

    # Directorio de uploads: 755 (necesita escribir nuevos archivos)
    if [ -d "$APP_DIR/backend/uploads" ]; then
        chmod 755 "$APP_DIR/backend/uploads"
        chown $SERVICE_USER:$SERVICE_GROUP "$APP_DIR/backend/uploads"
    fi
    
    # Habilitar e iniciar servicio
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    systemctl start ${SERVICE_NAME}
    
    sleep 3
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_success "Backend ejecutándose correctamente en puerto $BACKEND_PORT"
    else
        print_error "Error al iniciar el backend"
        journalctl -u ${SERVICE_NAME} --no-pager -n 30
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

    # Establecer permisos en el directorio de build (legible por nginx)
    chmod 755 "build"
    find "build" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "build" -type f -exec chmod 644 {} \; 2>/dev/null || true

    print_success "Frontend compilado correctamente"
}

#-------------------------------------------------------------------------------
# Configuración del Landing
#-------------------------------------------------------------------------------
setup_landing() {
    print_step "Configurando Landing (React)"

    if [ ! -d "$APP_DIR/landing" ]; then
        print_info "Directorio landing no encontrado, omitiendo..."
        return
    fi

    cd "$APP_DIR/landing"

    # Crear archivo .env con la URL del dominio
    cat > .env << EOF
REACT_APP_API_URL=https://$DOMAIN
REACT_APP_APP_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false
EOF

    # Instalar dependencias
    print_info "Instalando dependencias del landing..."
    yarn install --silent 2>/dev/null || yarn install

    # Compilar para producción
    print_info "Compilando landing (esto puede tardar unos minutos)..."
    GENERATE_SOURCEMAP=false yarn build

    if [ ! -d "build" ]; then
        print_error "Error al compilar el landing"
        exit 1
    fi

    print_success "Landing compilado correctamente"
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
    
    # Leer el puerto del backend
    if [ -f "$APP_DIR/.backend_port" ]; then
        BACKEND_PORT=$(cat "$APP_DIR/.backend_port")
    else
        BACKEND_PORT=8001
    fi
    
    print_info "Puerto del backend: $BACKEND_PORT"
    
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
    
    # Generar configuración con el puerto correcto
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << EOF
# Configuración Nginx para $DOMAIN
# Document Root: app/frontend/build
# Puerto Backend: $BACKEND_PORT

# API Backend - Proxy a FastAPI (puerto $BACKEND_PORT)
location /api/ {
    proxy_pass http://127.0.0.1:$BACKEND_PORT/api/;
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
    proxy_send_timeout 300s;
}

# Health Check
location /health {
    proxy_pass http://127.0.0.1:$BACKEND_PORT/health;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_read_timeout 10s;
}

# WebSocket para notificaciones en tiempo real
location /ws/ {
    proxy_pass http://127.0.0.1:$BACKEND_PORT/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
EOF
    
    print_success "Archivo de referencia Nginx creado"
    
    # IMPORTANTE: En Plesk, nginx_custom.conf NO se carga automáticamente
    # Hay que añadir la configuración manualmente en el panel de Plesk
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ⚠ PASO OBLIGATORIO: Configurar Nginx en Plesk${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${YELLOW}Plesk NO carga automáticamente archivos nginx_custom.conf${NC}"
    echo -e "  ${YELLOW}Debes añadir la configuración manualmente:${NC}"
    echo ""
    echo -e "  ${CYAN}1. Ve a Plesk → Dominios → $DOMAIN${NC}"
    echo -e "  ${CYAN}2. Haz clic en 'Apache & nginx Settings'${NC}"
    echo -e "  ${CYAN}3. Busca la sección 'Additional nginx directives'${NC}"
    echo -e "  ${CYAN}4. Copia y pega el siguiente contenido:${NC}"
    echo ""
    echo -e "${GREEN}─────────────── INICIO COPIAR ───────────────${NC}"
    cat << EOF
# API Backend - Proxy a FastAPI (puerto $BACKEND_PORT)
location /api/ {
    proxy_pass http://127.0.0.1:$BACKEND_PORT/api/;
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
    proxy_send_timeout 300s;
}

# Health Check
location /health {
    proxy_pass http://127.0.0.1:$BACKEND_PORT/health;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_read_timeout 10s;
}
EOF
    echo -e "${GREEN}─────────────── FIN COPIAR ───────────────${NC}"
    echo ""
    echo -e "  ${CYAN}5. Haz clic en 'OK' o 'Apply'${NC}"
    echo ""
    echo -e "  ${YELLOW}También puedes encontrar este contenido en:${NC}"
    echo -e "  ${CYAN}$PLESK_NGINX_DIR/nginx_custom.conf${NC}"
    echo ""
    
    # Esperar confirmación del usuario
    echo -e "${YELLOW}  Presiona ENTER cuando hayas completado este paso...${NC}"
    read -r
    
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
    echo -e "  ${GREEN}✓ CONFIGURACIÓN PERSISTENTE${NC}"
    echo -e "    La configuración se guardará en: ${CYAN}$PERSISTENT_CONFIG_DIR/${NC}"
    echo -e "    Esta ubicación NO se sobrescribe al actualizar la aplicación."
    echo ""
    echo -e "  ${GREEN}✓ SERVICIO BACKEND${NC}"
    echo -e "    Nombre del servicio: ${CYAN}$SERVICE_NAME${NC}"
    echo -e "    Puerto: ${CYAN}$BACKEND_PORT${NC}"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${YELLOW}Comandos útiles:${NC}"
    echo ""
    echo -e "    Ver logs del backend:"
    echo -e "    ${CYAN}journalctl -u ${SERVICE_NAME} -f${NC}"
    echo ""
    echo -e "    Reiniciar backend:"
    echo -e "    ${CYAN}systemctl restart ${SERVICE_NAME}${NC}"
    echo ""
    echo -e "    ${GREEN}Actualizar la aplicación (preserva configuración):${NC}"
    echo -e "    ${CYAN}sudo bash $APP_DIR/update.sh${NC}"
    echo ""
    echo -e "    Actualizar solo frontend después de cambios:"
    echo -e "    ${CYAN}sudo bash $APP_DIR/update-frontend.sh${NC}"
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -z "$MONGODB_URL" ]; then
        echo -e "  ${YELLOW}⚠ IMPORTANTE:${NC}"
        echo -e "    Debes configurar MongoDB en ${CYAN}https://$DOMAIN/#/setup${NC}"
        echo -e "    Una vez configurado, tu configuración se guardará de forma persistente."
        echo ""
    fi
    
    if [ "$IS_PLESK" == "yes" ]; then
        echo -e "  ${YELLOW}Configuración de Plesk:${NC}"
        echo -e "    • Document Root: ${CYAN}app/frontend/build${NC}"
        echo -e "    • SSL: Configurar desde Plesk → SSL/TLS Certificates"
        if [ "$IS_SUBDOMAIN" == "yes" ]; then
            echo -e "    • Tipo: ${CYAN}Subdominio de $MAIN_DOMAIN${NC}"
        fi
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
# SyncStock - Configuración para Plesk
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
    
    print_success "Archivo de referencia Nginx actualizado"
    
    # IMPORTANTE: Mostrar instrucciones de Plesk
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  ⚠ VERIFICAR: Configuración de Nginx en Plesk${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${CYAN}Si es la PRIMERA instalación, asegúrate de haber añadido${NC}"
    echo -e "  ${CYAN}la configuración de nginx en Plesk:${NC}"
    echo ""
    echo -e "  ${CYAN}1. Ve a Plesk → Dominios → $DOMAIN${NC}"
    echo -e "  ${CYAN}2. Haz clic en 'Apache & nginx Settings'${NC}"
    echo -e "  ${CYAN}3. Verifica que 'Additional nginx directives' contenga:${NC}"
    echo ""
    echo -e "     ${GREEN}location /api/ { proxy_pass http://127.0.0.1:8001/api/; ... }${NC}"
    echo ""
    echo -e "  ${CYAN}Si no está configurado, copia el contenido de:${NC}"
    echo -e "  ${CYAN}$PLESK_NGINX_DIR/nginx_custom.conf${NC}"
    echo ""
    
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
    setup_landing

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
        echo "SyncStock - Script de Instalación"
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
