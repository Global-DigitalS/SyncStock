#!/bin/bash

#===============================================================================
#
#          FILE: update.sh
#
#         USAGE: sudo bash update.sh
#
#   DESCRIPTION: Script de actualización de SupplierSync Pro
#                Preserva la configuración existente (MongoDB, SuperAdmin, etc.)
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
# Variables
#-------------------------------------------------------------------------------
APP_NAME="suppliersync"
PERSISTENT_CONFIG="/etc/suppliersync/config.json"
BACKUP_DIR="/etc/suppliersync/backups"

#-------------------------------------------------------------------------------
# Funciones de utilidad
#-------------------------------------------------------------------------------
print_header() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}        ${CYAN}SupplierSync Pro - Actualización${NC}                       ${PURPLE}║${NC}"
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
    
    # Si no hay dominio, preguntar
    if [ -z "$DOMAIN" ]; then
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
    PERSISTENT_CONFIG_DIR="/etc/suppliersync/$DOMAIN"
    PERSISTENT_CONFIG="$PERSISTENT_CONFIG_DIR/config.json"
    BACKUP_DIR="$PERSISTENT_CONFIG_DIR/backups"
    
    # Fallback a configuración antigua si no existe la nueva
    if [ ! -f "$PERSISTENT_CONFIG" ] && [ -f "/etc/suppliersync/config.json" ]; then
        PERSISTENT_CONFIG="/etc/suppliersync/config.json"
        BACKUP_DIR="/etc/suppliersync/backups"
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
# Crear backup de configuración
#-------------------------------------------------------------------------------
backup_config() {
    print_step "Creando backup de configuración"
    
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # Backup de config.json si existe
    if [ -f "$PERSISTENT_CONFIG" ]; then
        cp "$PERSISTENT_CONFIG" "$BACKUP_DIR/config_backup_$TIMESTAMP.json"
        print_success "Backup creado: config_backup_$TIMESTAMP.json"
    else
        # Buscar config.json en el directorio de la app
        if [ -f "$APP_DIR/backend/config.json" ]; then
            # Migrar a ubicación persistente
            mkdir -p "$PERSISTENT_CONFIG_DIR"
            cp "$APP_DIR/backend/config.json" "$PERSISTENT_CONFIG"
            cp "$APP_DIR/backend/config.json" "$BACKUP_DIR/config_backup_$TIMESTAMP.json"
            print_success "Configuración migrada a ubicación persistente"
            print_success "Backup creado: config_backup_$TIMESTAMP.json"
        else
            print_warning "No se encontró configuración para respaldar"
        fi
    fi
    
    # Backup del .env
    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$BACKUP_DIR/env_backup_$TIMESTAMP"
        print_success "Backup de .env creado"
    fi
}

#-------------------------------------------------------------------------------
# Actualizar el código
#-------------------------------------------------------------------------------
update_code() {
    print_step "Actualizando código fuente"
    
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
            cd "$APP_DIR"
            if [ -d ".git" ]; then
                print_info "Ejecutando git pull..."
                git pull
                print_success "Código actualizado desde Git"
            else
                print_error "No es un repositorio Git"
                print_info "Usa la opción 2 o 3"
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
    
    # Restaurar configuración persistente si existe
    if [ -f "$PERSISTENT_CONFIG" ]; then
        print_success "Configuración persistente detectada: $PERSISTENT_CONFIG"
        
        # Extraer valores para actualizar .env
        if command -v python3 &> /dev/null; then
            MONGO_URL=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('mongo_url',''))" 2>/dev/null || echo "")
            DB_NAME=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('db_name','supplier_sync_db'))" 2>/dev/null || echo "supplier_sync_db")
            CORS=$(python3 -c "import json; c=json.load(open('$PERSISTENT_CONFIG')); print(c.get('cors_origins','*'))" 2>/dev/null || echo "*")
            
            if [ -n "$MONGO_URL" ]; then
                # Actualizar .env con los valores de la configuración persistente
                cat > .env << EOF
MONGO_URL=$MONGO_URL
DB_NAME=$DB_NAME
CORS_ORIGINS=$CORS
CONFIG_PATH=$PERSISTENT_CONFIG
EOF
                print_success "Archivo .env actualizado desde configuración persistente"
            fi
        fi
    fi
    
    # Reiniciar servicio usando el nombre correcto
    print_info "Reiniciando servicio: $SERVICE_NAME"
    
    if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
        systemctl restart ${SERVICE_NAME}
        sleep 3
        
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            print_success "Backend reiniciado correctamente"
        else
            print_error "Error al reiniciar el backend"
            journalctl -u ${SERVICE_NAME} --no-pager -n 20
        fi
    else
        # Intentar con nombre antiguo (suppliersync-backend)
        if systemctl is-enabled --quiet ${APP_NAME}-backend 2>/dev/null; then
            print_warning "Usando nombre de servicio antiguo: ${APP_NAME}-backend"
            systemctl restart ${APP_NAME}-backend
            sleep 3
            
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
    if systemctl is-active --quiet ${APP_NAME}-backend 2>/dev/null; then
        print_success "Backend: Corriendo"
    else
        print_warning "Backend: Verificar manualmente"
    fi
    
    # Verificar configuración
    if [ -f "$PERSISTENT_CONFIG" ]; then
        print_success "Configuración: Persistente (/etc/suppliersync/)"
        
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
        echo "  sudo bash update.sh [dominio]     Actualizar la aplicación preservando configuración"
        echo "  sudo bash update.sh -h            Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  sudo bash update.sh app.sync-stock.com   Actualizar un subdominio específico"
        echo "  sudo bash update.sh menuboard.es         Actualizar un dominio principal"
        echo "  sudo bash update.sh                      Preguntará el dominio"
        echo ""
        echo "Este script:"
        echo "  - Detecta automáticamente subdominios en Plesk"
        echo "  - Crea backups de la configuración antes de actualizar"
        echo "  - Preserva la conexión a MongoDB y el usuario SuperAdmin"
        echo "  - Usa el puerto correcto para cada instalación"
        echo "  - Actualiza dependencias y recompila el frontend"
        echo ""
        ;;
    *)
        main "$1"
        ;;
esac
