#!/bin/bash

#===============================================================================
#
#          FILE: update.sh
#
#         USAGE: sudo bash update.sh
#
#   DESCRIPTION: Script de actualización de SyncStock
#                Preserva la configuración existente (MongoDB, SuperAdmin, etc.)
#
#       VERSION: 1.0.0
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
# Variables
#-------------------------------------------------------------------------------
APP_NAME="syncstock"
PERSISTENT_CONFIG="/etc/syncstock/config.json"
BACKUP_DIR="/etc/syncstock/backups"
AUTO_MODE="no"  # Activar con --auto o -y

#-------------------------------------------------------------------------------
# Funciones de utilidad
#-------------------------------------------------------------------------------
print_header() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}        ${CYAN}SyncStock - Actualización${NC}                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}              ${YELLOW}Preserva tu configuración${NC}                       ${PURPLE}║${NC}"
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

#-------------------------------------------------------------------------------
# Detectar instalación existente
#-------------------------------------------------------------------------------
detect_installation() {
    print_step "Detectando instalación existente"
    
    # Si se proporciona un dominio como argumento, usarlo
    if [ -n "$1" ]; then
        DOMAIN="$1"
    fi

    # Si no hay dominio, preguntar (solo en modo interactivo)
    if [ -z "$DOMAIN" ]; then
        if [ "$AUTO_MODE" == "yes" ]; then
            print_error "En modo automático debes proporcionar el dominio como argumento"
            echo "  Uso: sudo bash update.sh --auto app.sync-stock.com"
            exit 1
        fi
        echo ""
        read -p "  Introduce el dominio a actualizar (ej: app.sync-stock.com): " DOMAIN
        echo ""
    fi
    
    if [ -z "$DOMAIN" ]; then
        print_error "El dominio es obligatorio"
        exit 1
    fi
    
    # Buscar directorio de la aplicación
    if [ -d "/var/www/vhosts" ]; then
        IS_PLESK="yes"
        
        # Detectar si es un subdominio
        SUBDOMAIN_PARTS=$(echo "$DOMAIN" | tr '.' '\n' | wc -l)
        
        if [ "$SUBDOMAIN_PARTS" -ge 3 ]; then
            # Es un subdominio - extraer dominio principal
            MAIN_DOMAIN=$(echo "$DOMAIN" | rev | cut -d'.' -f1-2 | rev)
            IS_SUBDOMAIN="yes"
            
            # Buscar en estructura de subdominio de Plesk
            if [ -d "/var/www/vhosts/$MAIN_DOMAIN/$DOMAIN/app" ]; then
                APP_DIR="/var/www/vhosts/$MAIN_DOMAIN/$DOMAIN/app"
                PLESK_VHOST_DIR="/var/www/vhosts/$MAIN_DOMAIN"
                print_info "Detectado como subdominio de $MAIN_DOMAIN"
            elif [ -d "/var/www/vhosts/$DOMAIN/app" ]; then
                # El subdominio tiene su propio vhost
                APP_DIR="/var/www/vhosts/$DOMAIN/app"
                PLESK_VHOST_DIR="/var/www/vhosts/$DOMAIN"
                IS_SUBDOMAIN="no"
            fi
        else
            # Dominio principal
            IS_SUBDOMAIN="no"
            if [ -d "/var/www/vhosts/$DOMAIN/app" ]; then
                APP_DIR="/var/www/vhosts/$DOMAIN/app"
                PLESK_VHOST_DIR="/var/www/vhosts/$DOMAIN"
            fi
        fi
        
        # Detectar usuario de Plesk
        if [ -n "$PLESK_VHOST_DIR" ] && [ -d "$PLESK_VHOST_DIR" ]; then
            PLESK_USER=$(stat -c '%U' "$PLESK_VHOST_DIR" 2>/dev/null)
        fi
    fi
    
    # Si no se encontró en Plesk, buscar en ubicación estándar
    if [ -z "$APP_DIR" ] && [ -f "/var/www/$APP_NAME/backend/server.py" ]; then
        APP_DIR="/var/www/$APP_NAME"
        IS_PLESK="no"
    fi
    
    # Verificar que existe el código
    if [ -z "$APP_DIR" ] || [ ! -f "$APP_DIR/backend/server.py" ]; then
        print_error "No se encontró una instalación en $DOMAIN"
        echo ""
        echo -e "  ${YELLOW}Rutas buscadas:${NC}"
        if [ "$IS_SUBDOMAIN" == "yes" ]; then
            echo -e "    - /var/www/vhosts/$MAIN_DOMAIN/$DOMAIN/app"
        fi
        echo -e "    - /var/www/vhosts/$DOMAIN/app"
        echo ""
        echo -e "  ${YELLOW}Si es una instalación nueva, usa:${NC}"
        echo -e "    ${CYAN}sudo bash install.sh${NC}"
        echo ""
        exit 1
    fi
    
    # Detectar nombre del servicio y puerto
    SERVICE_NAME=$(echo "$DOMAIN" | tr '.' '-' | tr '[:upper:]' '[:lower:]')
    SERVICE_NAME="${SERVICE_NAME}-backend"
    
    # Leer el puerto si existe el archivo
    if [ -f "$APP_DIR/.backend_port" ]; then
        BACKEND_PORT=$(cat "$APP_DIR/.backend_port")
    else
        # Intentar detectar el puerto del servicio systemd
        BACKEND_PORT=$(grep -oP 'port \K[0-9]+' /etc/systemd/system/${SERVICE_NAME}.service 2>/dev/null || echo "8001")
    fi
    
    # Configuración persistente por dominio
    PERSISTENT_CONFIG_DIR="/etc/syncstock/$DOMAIN"
    PERSISTENT_CONFIG="$PERSISTENT_CONFIG_DIR/config.json"
    BACKUP_DIR="$PERSISTENT_CONFIG_DIR/backups"
    
    # Fallback a configuración antigua si no existe la nueva
    if [ ! -f "$PERSISTENT_CONFIG" ] && [ -f "/etc/syncstock/config.json" ]; then
        PERSISTENT_CONFIG="/etc/syncstock/config.json"
        BACKUP_DIR="/etc/syncstock/backups"
    fi
    
    print_success "Instalación encontrada en: $APP_DIR"
    
    if [ "$IS_PLESK" == "yes" ]; then
        print_info "Tipo: Plesk ($DOMAIN)"
        print_info "Usuario: $PLESK_USER"
        if [ "$IS_SUBDOMAIN" == "yes" ]; then
            print_info "Subdominio de: $MAIN_DOMAIN"
        fi
    else
        print_info "Tipo: Instalación estándar"
    fi
    
    print_info "Servicio: $SERVICE_NAME"
    print_info "Puerto: $BACKEND_PORT"
}

#-------------------------------------------------------------------------------
# Crear backup completo (código + configuración)
#-------------------------------------------------------------------------------
backup_config() {
    print_step "Creando backup previo a la actualización"

    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    # --- Backup del código fuente (excluye carpetas pesadas) ---
    CODE_BACKUP="$BACKUP_DIR/code_backup_$TIMESTAMP.tar.gz"
    print_info "Creando backup del código fuente..."
    tar -czf "$CODE_BACKUP" \
        --exclude='*/node_modules' \
        --exclude='*/venv' \
        --exclude='*/__pycache__' \
        --exclude='*/build' \
        --exclude='*/.git' \
        -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")" 2>/dev/null || true

    if [ -f "$CODE_BACKUP" ]; then
        BACKUP_SIZE=$(du -sh "$CODE_BACKUP" 2>/dev/null | cut -f1)
        print_success "Backup del código: code_backup_$TIMESTAMP.tar.gz ($BACKUP_SIZE)"
    else
        print_warning "No se pudo crear el backup del código"
    fi

    # --- Backup de config.json si existe ---
    if [ -f "$PERSISTENT_CONFIG" ]; then
        cp "$PERSISTENT_CONFIG" "$BACKUP_DIR/config_backup_$TIMESTAMP.json"
        print_success "Backup de configuración: config_backup_$TIMESTAMP.json"
    else
        if [ -f "$APP_DIR/backend/config.json" ]; then
            mkdir -p "$PERSISTENT_CONFIG_DIR"
            cp "$APP_DIR/backend/config.json" "$PERSISTENT_CONFIG"
            cp "$APP_DIR/backend/config.json" "$BACKUP_DIR/config_backup_$TIMESTAMP.json"
            print_success "Configuración migrada a ubicación persistente"
            print_success "Backup de configuración: config_backup_$TIMESTAMP.json"
        else
            print_warning "No se encontró configuración persistente para respaldar"
        fi
    fi

    # --- Backup del .env del backend ---
    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$BACKUP_DIR/env_backend_$TIMESTAMP"
        print_success "Backup de .env backend creado"
    fi

    # --- Backup del .env del frontend ---
    if [ -f "$APP_DIR/frontend/.env" ]; then
        cp "$APP_DIR/frontend/.env" "$BACKUP_DIR/env_frontend_$TIMESTAMP"
        print_success "Backup de .env frontend creado"
    fi

    # Limpiar backups antiguos (mantener últimos 5)
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/code_backup_*.tar.gz 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 5 ]; then
        print_info "Limpiando backups antiguos (manteniendo últimos 5)..."
        ls -1t "$BACKUP_DIR"/code_backup_*.tar.gz | tail -n +6 | xargs rm -f 2>/dev/null || true
        ls -1t "$BACKUP_DIR"/config_backup_*.json | tail -n +6 | xargs rm -f 2>/dev/null || true
    fi

    print_info "Backups almacenados en: $BACKUP_DIR"
}

#-------------------------------------------------------------------------------
# Actualizar el código
#-------------------------------------------------------------------------------
update_code() {
    print_step "Actualizando código fuente"

    cd "$APP_DIR"

    # Modo automático o si existe .git → usar git pull directamente
    if [ "$AUTO_MODE" == "yes" ] || [ -d ".git" ]; then
        if [ -d ".git" ]; then
            print_info "Ejecutando git pull..."
            git fetch origin
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || git pull
            print_success "Código actualizado desde Git"
            return
        else
            if [ "$AUTO_MODE" == "yes" ]; then
                print_warning "No es un repositorio Git. Asumiendo que los archivos ya están actualizados."
                print_success "Continuando con la actualización..."
                return
            fi
        fi
    fi

    # Modo interactivo
    echo ""
    echo -e "${YELLOW}  ¿Cómo deseas actualizar el código?${NC}"
    echo ""
    echo "    1) Desde repositorio Git (git pull)"
    echo "    2) Subir archivos manualmente (ya subidos)"
    echo "    3) Clonar de nuevo desde un repositorio"
    echo ""
    read -p "  Selecciona una opción [1-3]: " update_choice

    case $update_choice in
        1)
            if [ -d ".git" ]; then
                print_info "Ejecutando git pull..."
                git fetch origin
                git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || git pull
                print_success "Código actualizado desde Git"
            else
                print_error "No es un repositorio Git"
                exit 1
            fi
            ;;
        2)
            print_info "Asumiendo que los archivos ya están actualizados"
            print_success "Continuando con la actualización..."
            ;;
        3)
            read -p "  URL del repositorio Git: " GIT_URL
            TEMP_DIR=$(mktemp -d)
            print_info "Clonando repositorio..."
            git clone "$GIT_URL" "$TEMP_DIR"

            # Preservar config.json y .env antes de copiar
            if [ -f "$APP_DIR/backend/config.json" ]; then
                cp "$APP_DIR/backend/config.json" "$TEMP_DIR/backend/" 2>/dev/null || true
            fi
            if [ -f "$APP_DIR/backend/.env" ]; then
                cp "$APP_DIR/backend/.env" "$TEMP_DIR/backend/" 2>/dev/null || true
            fi

            # Copiar nuevos archivos
            rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='build' "$TEMP_DIR/" "$APP_DIR/"
            rm -rf "$TEMP_DIR"
            print_success "Código actualizado desde repositorio"
            ;;
        *)
            print_warning "Opción no válida. Continuando sin actualizar código fuente."
            ;;
    esac
}

#-------------------------------------------------------------------------------
# Actualizar Backend
#-------------------------------------------------------------------------------
update_backend() {
    print_step "Actualizando Backend"
    
    cd "$APP_DIR/backend"
    
    # Activar entorno virtual
    if [ ! -d "venv" ]; then
        print_info "Creando entorno virtual..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    
    # Actualizar dependencias
    print_info "Actualizando dependencias de Python..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    
    # Leer valores existentes del .env actual como fallback
    EXISTING_MONGO_URL=""
    EXISTING_DB_NAME=""
    EXISTING_CORS=""
    EXISTING_JWT_SECRET=""
    EXISTING_FERNET_KEY=""
    EXISTING_CONFIG_PATH=""
    if [ -f ".env" ]; then
        EXISTING_MONGO_URL=$(grep -oP '^MONGO_URL=\K.*' .env 2>/dev/null || echo "")
        EXISTING_DB_NAME=$(grep -oP '^DB_NAME=\K.*' .env 2>/dev/null || echo "")
        EXISTING_CORS=$(grep -oP '^CORS_ORIGINS=\K.*' .env 2>/dev/null || echo "")
        EXISTING_JWT_SECRET=$(grep -oP '^JWT_SECRET=\K.*' .env 2>/dev/null || echo "")
        EXISTING_FERNET_KEY=$(grep -oP '^FERNET_KEY=\K.*' .env 2>/dev/null || echo "")
        EXISTING_CONFIG_PATH=$(grep -oP '^CONFIG_PATH=\K.*' .env 2>/dev/null || echo "")
        print_info "Valores existentes del .env leídos como fallback"
    fi

    # Restaurar configuración persistente si existe
    if [ -f "$PERSISTENT_CONFIG" ]; then
        print_success "Configuración persistente detectada: $PERSISTENT_CONFIG"

        # Extraer valores para actualizar .env
        if command -v python3 &> /dev/null; then
            MONGO_URL=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('mongo_url',''))" 2>/dev/null || echo "")
            DB_NAME=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('db_name',''))" 2>/dev/null || echo "")
            CORS=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('cors_origins',''))" 2>/dev/null || echo "")
            JWT_SECRET_VAL=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('jwt_secret',''))" 2>/dev/null || echo "")
            FERNET_KEY_VAL=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('fernet_key',''))" 2>/dev/null || echo "")

            # Usar valores del config persistente, con fallback al .env existente
            MONGO_URL="${MONGO_URL:-$EXISTING_MONGO_URL}"
            DB_NAME="${DB_NAME:-$EXISTING_DB_NAME}"
            DB_NAME="${DB_NAME:-syncstock_db}"
            CORS="${CORS:-$EXISTING_CORS}"
            CORS="${CORS:-*}"
            JWT_SECRET_VAL="${JWT_SECRET_VAL:-$EXISTING_JWT_SECRET}"
            FERNET_KEY_VAL="${FERNET_KEY_VAL:-$EXISTING_FERNET_KEY}"

            # CRÍTICO: Si no hay JWT_SECRET en ninguna fuente, generar uno nuevo
            # Esto evita que el backend falle al arrancar por falta de JWT_SECRET
            if [ -z "$JWT_SECRET_VAL" ]; then
                print_warning "JWT_SECRET no encontrado en config persistente ni en .env"
                JWT_SECRET_VAL=$(python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null)
                if [ -n "$JWT_SECRET_VAL" ]; then
                    print_success "JWT_SECRET generado automáticamente"
                else
                    print_error "No se pudo generar JWT_SECRET"
                fi
            fi

            # Si no hay FERNET_KEY, generar una nueva
            if [ -z "$FERNET_KEY_VAL" ]; then
                FERNET_KEY_VAL=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
                if [ -n "$FERNET_KEY_VAL" ]; then
                    print_info "FERNET_KEY generada automáticamente"
                fi
            fi

            if [ -n "$MONGO_URL" ]; then
                # Actualizar .env con los valores fusionados
                cat > .env << EOF
MONGO_URL=$MONGO_URL
DB_NAME=$DB_NAME
CORS_ORIGINS=$CORS
CONFIG_PATH=$PERSISTENT_CONFIG
EOF
                # Añadir JWT_SECRET (siempre debe existir en este punto)
                if [ -n "$JWT_SECRET_VAL" ]; then
                    echo "JWT_SECRET=$JWT_SECRET_VAL" >> .env
                fi
                # Añadir FERNET_KEY si existe
                if [ -n "$FERNET_KEY_VAL" ]; then
                    echo "FERNET_KEY=$FERNET_KEY_VAL" >> .env
                fi
                print_success "Archivo .env actualizado (config persistente + valores existentes)"

                # Sincronizar valores faltantes de vuelta al config.json persistente
                # IMPORTANTE: Siempre asegurar que jwt_secret y fernet_key estén guardados
                python3 -c "
import json, sys
try:
    with open('$PERSISTENT_CONFIG', 'r') as f:
        cfg = json.load(f)
    updated = False
    if not cfg.get('db_name') and '$DB_NAME':
        cfg['db_name'] = '$DB_NAME'
        updated = True
    # Siempre sincronizar jwt_secret si falta en config persistente
    if not cfg.get('jwt_secret') and '$JWT_SECRET_VAL':
        cfg['jwt_secret'] = '$JWT_SECRET_VAL'
        updated = True
    # Siempre sincronizar fernet_key si falta en config persistente
    if not cfg.get('fernet_key') and '$FERNET_KEY_VAL':
        cfg['fernet_key'] = '$FERNET_KEY_VAL'
        updated = True
    # Asegurar que mongo_url esté en config persistente
    if not cfg.get('mongo_url') and '$MONGO_URL':
        cfg['mongo_url'] = '$MONGO_URL'
        updated = True
    # Asegurar que cors_origins esté en config persistente
    if not cfg.get('cors_origins') and '$CORS':
        cfg['cors_origins'] = '$CORS'
        updated = True
    if updated:
        with open('$PERSISTENT_CONFIG', 'w') as f:
            json.dump(cfg, f, indent=2)
        print('Config persistente actualizado con valores faltantes')
    else:
        print('Config persistente ya tiene todos los valores')
except Exception as e:
    print(f'Aviso: no se pudo sincronizar config persistente: {e}', file=sys.stderr)
" 2>/dev/null && print_info "Config persistente sincronizado" || true
            fi
        fi
    elif [ -f ".env" ]; then
        # No hay config persistente, pero sí hay .env — preservarlo
        print_info "No hay configuración persistente, preservando .env existente"

        # Verificar que el .env existente tiene JWT_SECRET
        if ! grep -q '^JWT_SECRET=' .env 2>/dev/null; then
            print_warning "JWT_SECRET no encontrado en .env existente, generando uno..."
            JWT_SECRET_VAL=$(python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null)
            if [ -n "$JWT_SECRET_VAL" ]; then
                echo "JWT_SECRET=$JWT_SECRET_VAL" >> .env
                print_success "JWT_SECRET añadido al .env"
            fi
        fi
    else
        # No hay ni config persistente ni .env — crear .env mínimo
        print_warning "No se encontró ni configuración persistente ni .env"
        JWT_SECRET_VAL=$(python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null)
        cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=syncstock_db
CORS_ORIGINS=*
EOF
        if [ -n "$JWT_SECRET_VAL" ]; then
            echo "JWT_SECRET=$JWT_SECRET_VAL" >> .env
            print_success "Archivo .env creado con JWT_SECRET generado"
        else
            print_error "No se pudo generar .env con JWT_SECRET"
        fi
    fi
    
    # Reiniciar servicio usando el nombre correcto
    print_info "Reiniciando servicio: $SERVICE_NAME"
    
    if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
        systemctl restart ${SERVICE_NAME}
        sleep 5

        if systemctl is-active --quiet ${SERVICE_NAME}; then
            print_success "Backend reiniciado correctamente"
        else
            print_error "Error al reiniciar el backend"
            journalctl -u ${SERVICE_NAME} --no-pager -n 20
        fi
    else
        # Intentar con nombre antiguo (syncstock-backend)
        if systemctl is-enabled --quiet ${APP_NAME}-backend 2>/dev/null; then
            print_warning "Usando nombre de servicio antiguo: ${APP_NAME}-backend"
            systemctl restart ${APP_NAME}-backend
            sleep 5
            
            if systemctl is-active --quiet ${APP_NAME}-backend; then
                print_success "Backend reiniciado correctamente"
            else
                print_warning "Error al reiniciar. Intentando supervisorctl..."
                supervisorctl restart backend 2>/dev/null || true
            fi
        else
            print_warning "No se encontró servicio systemd. Intentando supervisorctl..."
            supervisorctl restart backend 2>/dev/null || true
        fi
    fi
}

#-------------------------------------------------------------------------------
# Actualizar Frontend
#-------------------------------------------------------------------------------
update_frontend() {
    print_step "Actualizando Frontend"
    
    cd "$APP_DIR/frontend"
    
    # Preservar .env si existe
    if [ -f ".env" ]; then
        FRONTEND_ENV=$(cat .env)
    else
        # Crear .env básico
        if [ -n "$DOMAIN" ]; then
            FRONTEND_ENV="REACT_APP_BACKEND_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false"
        fi
    fi
    
    # Instalar dependencias
    print_info "Actualizando dependencias de Node.js..."
    yarn install --silent 2>/dev/null || yarn install

    # Asegurar que react-scripts real está instalado (el stub 0.0.0 no tiene config/env.js)
    RS_VERSION=$(node -e "try{require('react-scripts/package.json');console.log(require('react-scripts/package.json').version)}catch(e){console.log('0.0.0')}" 2>/dev/null || echo "0.0.0")
    if [ "$RS_VERSION" = "0.0.0" ] || [ -z "$RS_VERSION" ]; then
        print_info "Instalando react-scripts 5.0.1 (versión real necesaria para craco)..."
        yarn add react-scripts@5.0.1 --exact --silent 2>/dev/null || yarn add react-scripts@5.0.1 --exact
    fi

    # Asegurar que dotenv está instalado (requerido por craco.config.js)
    if ! node -e "require('dotenv')" 2>/dev/null; then
        print_info "Instalando dotenv (requerido por craco)..."
        yarn add dotenv --silent 2>/dev/null || yarn add dotenv
    fi

    # Restaurar .env
    if [ -n "$FRONTEND_ENV" ]; then
        echo "$FRONTEND_ENV" > .env
    fi

    # Compilar
    print_info "Compilando frontend (esto puede tardar unos minutos)..."
    GENERATE_SOURCEMAP=false yarn build
    
    if [ -d "build" ]; then
        print_success "Frontend compilado correctamente"
    else
        print_error "Error al compilar el frontend"
        exit 1
    fi
    
    # Establecer permisos
    if [ "$IS_PLESK" == "yes" ] && [ -n "$PLESK_USER" ]; then
        chown -R "$PLESK_USER:psacln" "$APP_DIR"
        chmod -R 755 "$APP_DIR"
        print_success "Permisos actualizados"
    fi
}

#-------------------------------------------------------------------------------
# Actualizar Landing
#-------------------------------------------------------------------------------
update_landing() {
    print_step "Actualizando Landing"

    if [ ! -d "$APP_DIR/landing" ]; then
        print_info "Directorio landing no encontrado, omitiendo..."
        return
    fi

    cd "$APP_DIR/landing"

    # Preservar .env si existe, si no, crearlo con el dominio
    if [ -f ".env" ]; then
        LANDING_ENV=$(cat .env)
    else
        if [ -n "$DOMAIN" ]; then
            LANDING_ENV="REACT_APP_API_URL=https://$DOMAIN
REACT_APP_APP_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false"
        fi
    fi

    # Instalar dependencias
    print_info "Actualizando dependencias del landing..."
    yarn install --silent 2>/dev/null || yarn install

    # Asegurar que react-scripts real está instalado
    RS_VERSION=$(node -e "try{require('react-scripts/package.json');console.log(require('react-scripts/package.json').version)}catch(e){console.log('0.0.0')}" 2>/dev/null || echo "0.0.0")
    if [ "$RS_VERSION" = "0.0.0" ] || [ -z "$RS_VERSION" ]; then
        print_info "Instalando react-scripts 5.0.1..."
        yarn add react-scripts@5.0.1 --exact --silent 2>/dev/null || yarn add react-scripts@5.0.1 --exact
    fi

    # Asegurar que dotenv está instalado
    if ! node -e "require('dotenv')" 2>/dev/null; then
        print_info "Instalando dotenv (requerido por craco)..."
        yarn add dotenv --silent 2>/dev/null || yarn add dotenv
    fi

    # Restaurar .env
    if [ -n "$LANDING_ENV" ]; then
        echo "$LANDING_ENV" > .env
    fi

    # Compilar
    print_info "Compilando landing (esto puede tardar unos minutos)..."
    GENERATE_SOURCEMAP=false yarn build

    if [ -d "build" ]; then
        print_success "Landing compilado correctamente"
    else
        print_error "Error al compilar el landing"
        exit 1
    fi

    # Establecer permisos
    if [ "$IS_PLESK" == "yes" ] && [ -n "$PLESK_USER" ]; then
        chown -R "$PLESK_USER:psacln" "$APP_DIR"
        chmod -R 755 "$APP_DIR"
    fi
}

#-------------------------------------------------------------------------------
# Verificar configuración de Nginx en Plesk
#-------------------------------------------------------------------------------
verify_nginx_plesk() {
    if [ "$IS_PLESK" != "yes" ]; then
        return
    fi
    
    print_step "Verificando configuración de Nginx para Plesk"
    
    PLESK_NGINX_DIR="/var/www/vhosts/system/$DOMAIN/conf"
    
    # Actualizar archivo de referencia con el puerto correcto
    mkdir -p "$PLESK_NGINX_DIR"
    
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << EOF
# Configuración Nginx para $DOMAIN
# IMPORTANTE: Este archivo es solo de REFERENCIA.
# Debes copiar su contenido en Plesk → Apache & nginx Settings → Additional nginx directives
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

    print_success "Archivo de referencia nginx actualizado (puerto $BACKEND_PORT)"
    
    # Verificar si la API responde
    print_info "Verificando si el proxy de la API está configurado..."
    
    API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/health" 2>/dev/null || echo "000")
    
    if [ "$API_RESPONSE" == "200" ]; then
        print_success "Backend responde correctamente en puerto $BACKEND_PORT"
        
        # Intentar verificar desde el dominio
        if [ -n "$DOMAIN" ]; then
            EXTERNAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/setup/status" 2>/dev/null || echo "000")
            
            if [ "$EXTERNAL_RESPONSE" == "200" ]; then
                print_success "Proxy de API funcionando correctamente"
            else
                echo ""
                echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${YELLOW}  ⚠ ATENCIÓN: El proxy de API puede no estar configurado${NC}"
                echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                echo -e "  ${CYAN}El backend funciona en puerto $BACKEND_PORT, pero las peticiones a /api/ no llegan.${NC}"
                echo -e "  ${CYAN}Verifica en Plesk → $DOMAIN → Apache & nginx Settings:${NC}"
                echo ""
                echo -e "  ${CYAN}1. Busca 'Additional nginx directives'${NC}"
                echo -e "  ${CYAN}2. Verifica que el puerto sea ${GREEN}$BACKEND_PORT${NC}"
                echo -e "  ${CYAN}3. Si está incorrecto, actualiza con el contenido de:${NC}"
                echo -e "     ${GREEN}$PLESK_NGINX_DIR/nginx_custom.conf${NC}"
                echo ""
            fi
        fi
    else
        print_warning "Backend no responde - verificar servicio"
    fi
}

#-------------------------------------------------------------------------------
# Verificar estado
#-------------------------------------------------------------------------------
verify_update() {
    print_step "Verificando actualización"
    
    # Verificar backend
    if systemctl is-active --quiet ${SERVICE_NAME} 2>/dev/null; then
        print_success "Backend: Corriendo (${SERVICE_NAME})"
    else
        print_warning "Backend: Verificar manualmente (${SERVICE_NAME})"
    fi
    
    # Verificar configuración
    if [ -f "$PERSISTENT_CONFIG" ]; then
        print_success "Configuración: Persistente (/etc/syncstock/)"
        
        # Verificar que la configuración es válida
        if python3 -c "import json; json.load(open('$PERSISTENT_CONFIG'))" 2>/dev/null; then
            print_success "Configuración: Válida"
        else
            print_warning "Configuración: Verificar formato"
        fi
    else
        print_warning "Configuración: No persistente (configurar desde /setup)"
    fi
    
    # Verificar frontend
    if [ -d "$APP_DIR/frontend/build" ] && [ -f "$APP_DIR/frontend/build/index.html" ]; then
        print_success "Frontend: Compilado"
    else
        print_warning "Frontend: Verificar compilación"
    fi
}

#-------------------------------------------------------------------------------
# Resumen final
#-------------------------------------------------------------------------------
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}            ${CYAN}¡Actualización Completada!${NC}                          ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ -f "$PERSISTENT_CONFIG" ]; then
        echo -e "  ${GREEN}✓ Tu configuración se ha preservado${NC}"
        echo -e "    ${CYAN}Ubicación: $PERSISTENT_CONFIG${NC}"
    fi
    
    echo ""
    echo -e "  ${PURPLE}Información del servicio:${NC}"
    echo -e "    Nombre: ${CYAN}$SERVICE_NAME${NC}"
    echo -e "    Puerto: ${CYAN}$BACKEND_PORT${NC}"
    echo ""
    echo -e "  ${PURPLE}Backups disponibles en:${NC}"
    echo -e "    ${CYAN}$BACKUP_DIR${NC}"
    echo ""
    
    if [ -n "$DOMAIN" ]; then
        echo -e "  ${PURPLE}Accede a tu aplicación:${NC}"
        echo -e "    ${CYAN}https://$DOMAIN${NC}"
    fi
    
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
    echo -e "    Ver backups:"
    echo -e "    ${CYAN}ls -la $BACKUP_DIR${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# Función principal
#-------------------------------------------------------------------------------
main() {
    print_header
    check_root
    detect_installation "$1"
    backup_config
    update_code
    update_backend
    update_frontend
    update_landing
    verify_nginx_plesk
    verify_update
    print_summary
}

#-------------------------------------------------------------------------------
# Punto de entrada
#-------------------------------------------------------------------------------
case "${1:-}" in
    --help|-h)
        echo ""
        echo "SyncStock Pro - Script de Actualización"
        echo ""
        echo "Uso:"
        echo "  sudo bash update.sh [dominio]              Modo interactivo"
        echo "  sudo bash update.sh --auto [dominio]       Modo automático (sin prompts)"
        echo "  sudo bash update.sh -y [dominio]           Modo automático (alias)"
        echo "  sudo bash update.sh -h                     Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  sudo bash update.sh app.sync-stock.com            Actualizar con confirmaciones"
        echo "  sudo bash update.sh --auto app.sync-stock.com     Actualizar sin intervención"
        echo "  sudo bash update.sh menuboard.es                  Actualizar un dominio principal"
        echo "  sudo bash update.sh                               Preguntará el dominio"
        echo ""
        echo "Este script:"
        echo "  - Crea backup completo del código antes de actualizar"
        echo "  - Detecta automáticamente subdominios en Plesk"
        echo "  - Preserva la conexión a MongoDB y el usuario SuperAdmin"
        echo "  - Usa el puerto correcto para cada instalación"
        echo "  - Actualiza dependencias Python y Node.js"
        echo "  - Recompila frontend y landing automáticamente"
        echo "  - Mantiene los últimos 5 backups (elimina los anteriores)"
        echo ""
        ;;
    --auto|-y)
        AUTO_MODE="yes"
        main "${2:-}"
        ;;
    *)
        main "$1"
        ;;
esac
