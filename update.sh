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
    
    # Buscar directorio de la aplicación
    if [ -d "/var/www/vhosts" ]; then
        # Buscar en Plesk
        for vhost_dir in /var/www/vhosts/*/app; do
            if [ -f "$vhost_dir/backend/server.py" ]; then
                APP_DIR="$vhost_dir"
                DOMAIN=$(basename $(dirname "$vhost_dir"))
                IS_PLESK="yes"
                PLESK_USER=$(stat -c '%U' "$(dirname $vhost_dir)" 2>/dev/null)
                break
            fi
        done
    fi
    
    # Si no se encontró en Plesk, buscar en ubicación estándar
    if [ -z "$APP_DIR" ] && [ -f "/var/www/$APP_NAME/backend/server.py" ]; then
        APP_DIR="/var/www/$APP_NAME"
        IS_PLESK="no"
    fi
    
    if [ -z "$APP_DIR" ]; then
        print_error "No se encontró una instalación de SupplierSync Pro"
        echo ""
        echo -e "  ${YELLOW}Si es una instalación nueva, usa:${NC}"
        echo -e "    ${CYAN}sudo bash install.sh${NC}"
        echo ""
        exit 1
    fi
    
    print_success "Instalación encontrada en: $APP_DIR"
    
    if [ "$IS_PLESK" == "yes" ]; then
        print_info "Tipo: Plesk ($DOMAIN)"
        print_info "Usuario: $PLESK_USER"
    else
        print_info "Tipo: Instalación estándar"
    fi
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
            mkdir -p /etc/suppliersync
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
        print_success "Configuración persistente detectada"
        
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
EOF
                print_success "Archivo .env actualizado desde configuración persistente"
            fi
        fi
    fi
    
    # Reiniciar servicio
    print_info "Reiniciando servicio backend..."
    systemctl restart ${APP_NAME}-backend 2>/dev/null || true
    
    sleep 3
    
    if systemctl is-active --quiet ${APP_NAME}-backend 2>/dev/null; then
        print_success "Backend reiniciado correctamente"
    else
        print_warning "Verificando estado del backend..."
        # Intentar con supervisorctl si systemctl falla
        supervisorctl restart backend 2>/dev/null || true
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
    
    # Actualizar archivo de referencia
    mkdir -p "$PLESK_NGINX_DIR"
    
    cat > "$PLESK_NGINX_DIR/nginx_custom.conf" << 'NGINX_EOF'
# SupplierSync Pro - Configuración Nginx para Plesk
# IMPORTANTE: Este archivo es solo de REFERENCIA.
# Debes copiar su contenido en Plesk → Apache & nginx Settings → Additional nginx directives

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

    print_success "Archivo de referencia nginx actualizado"
    
    # Verificar si la API responde
    print_info "Verificando si el proxy de la API está configurado..."
    
    API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8001/health" 2>/dev/null || echo "000")
    
    if [ "$API_RESPONSE" == "200" ]; then
        print_success "Backend responde correctamente en puerto 8001"
        
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
                echo -e "  ${CYAN}El backend funciona, pero las peticiones a /api/ no llegan.${NC}"
                echo -e "  ${CYAN}Verifica en Plesk → $DOMAIN → Apache & nginx Settings:${NC}"
                echo ""
                echo -e "  ${CYAN}1. Busca 'Additional nginx directives'${NC}"
                echo -e "  ${CYAN}2. Debe contener la configuración de proxy para /api/${NC}"
                echo -e "  ${CYAN}3. Si está vacío, copia el contenido de:${NC}"
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
    echo -e "    ${CYAN}journalctl -u ${APP_NAME}-backend -f${NC}"
    echo ""
    echo -e "    Reiniciar backend:"
    echo -e "    ${CYAN}systemctl restart ${APP_NAME}-backend${NC}"
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
    detect_installation
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
        echo "SupplierSync Pro - Script de Actualización"
        echo ""
        echo "Uso:"
        echo "  sudo bash update.sh     Actualizar la aplicación preservando configuración"
        echo "  sudo bash update.sh -h  Mostrar esta ayuda"
        echo ""
        echo "Este script:"
        echo "  - Detecta automáticamente la instalación existente"
        echo "  - Crea backups de la configuración antes de actualizar"
        echo "  - Preserva la conexión a MongoDB y el usuario SuperAdmin"
        echo "  - Actualiza dependencias y recompila el frontend"
        echo ""
        ;;
    *)
        main
        ;;
esac
