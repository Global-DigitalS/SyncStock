#!/bin/bash
# =============================================================================
# SCRIPT DE ACTUALIZACIÓN - SyncStock
# Ejecuta este script en tu servidor de producción para actualizar la app
#
# Uso:
#   sudo bash scripts/update.sh                          # usa APP_DIR por defecto
#   APP_DIR=/ruta/custom sudo bash scripts/update.sh     # ruta personalizada
# =============================================================================

set -e  # Salir si hay error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuración - se puede sobreescribir con variables de entorno
APP_DIR="${APP_DIR:-/var/www/vhosts/sync-stock.com/app.sync-stock.com/app}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/syncstock}"
SERVICE_NAME="${SERVICE_NAME:-app-sync-stock-com-backend}"
DOMAIN="${DOMAIN:-app.sync-stock.com}"

echo ""
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${CYAN}       ACTUALIZACIÓN DE SYNCSTOCK         ${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo ""

# Verificar root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}✗ Este script debe ejecutarse como root (sudo)${NC}"
    exit 1
fi

# Verificar que existe el directorio
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}✗ No se encontró el directorio: $APP_DIR${NC}"
    echo -e "  Ejecuta con: APP_DIR=/ruta/correcta sudo bash scripts/update.sh"
    exit 1
fi

echo -e "${CYAN}  Directorio: $APP_DIR${NC}"
echo -e "${CYAN}  Dominio:    $DOMAIN${NC}"
echo -e "${CYAN}  Servicio:   $SERVICE_NAME${NC}"
echo ""

# ── 1. BACKUP COMPLETO ────────────────────────────────────────────────────────
echo -e "${YELLOW}1) Creando backup previo...${NC}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

tar -czf "$BACKUP_FILE" \
    --exclude='*/node_modules' \
    --exclude='*/venv' \
    --exclude='*/__pycache__' \
    --exclude='*/build' \
    --exclude='*/.git' \
    -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")" 2>/dev/null || true

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" 2>/dev/null | cut -f1)
    echo -e "${GREEN}  ✓ Backup creado: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    echo -e "${YELLOW}  ⚠ No se pudo crear el backup del código${NC}"
fi

# Backup del .env del backend
if [ -f "$APP_DIR/backend/.env" ]; then
    cp "$APP_DIR/backend/.env" "$BACKUP_DIR/env_backend_$TIMESTAMP"
    echo -e "${GREEN}  ✓ Backup de .env backend creado${NC}"
fi

# Backup del .env del frontend
if [ -f "$APP_DIR/frontend/.env" ]; then
    cp "$APP_DIR/frontend/.env" "$BACKUP_DIR/env_frontend_$TIMESTAMP"
    echo -e "${GREEN}  ✓ Backup de .env frontend creado${NC}"
fi

# Limpiar backups antiguos (mantener últimos 5)
ls -1t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

# ── 2. DETENER SERVICIO ───────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}2) Deteniendo servicio backend...${NC}"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
echo -e "${GREEN}  ✓ Servicio detenido${NC}"

# ── 3. ACTUALIZAR CÓDIGO ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}3) Actualizando código fuente...${NC}"
cd "$APP_DIR"
if [ -d ".git" ]; then
    git fetch origin
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || git pull
    echo -e "${GREEN}  ✓ Código actualizado desde git${NC}"
else
    echo -e "${YELLOW}  ⚠ No es repositorio git. Asumiendo archivos ya actualizados.${NC}"
fi

# ── 4. BACKEND: dependencias ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}4) Actualizando dependencias del backend...${NC}"
cd "$APP_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
cd "$APP_DIR"
echo -e "${GREEN}  ✓ Dependencias del backend actualizadas${NC}"

# ── 5. FRONTEND: dependencias + build ────────────────────────────────────────
echo ""
echo -e "${YELLOW}5) Actualizando frontend...${NC}"
cd "$APP_DIR/frontend"

# Preservar .env del frontend
FRONTEND_ENV_CONTENT=""
if [ -f ".env" ]; then
    FRONTEND_ENV_CONTENT=$(cat .env)
fi

# Instalar dependencias
if command -v yarn &> /dev/null; then
    yarn install 2>/dev/null || yarn install

    # Asegurar que react-scripts real está instalado (el stub 0.0.0 no tiene config/env.js)
    RS_VERSION=$(node -e "try{require('react-scripts/package.json');console.log(require('react-scripts/package.json').version)}catch(e){console.log('0.0.0')}" 2>/dev/null || echo "0.0.0")
    if [ "$RS_VERSION" = "0.0.0" ] || [ -z "$RS_VERSION" ]; then
        echo -e "${CYAN}    Instalando react-scripts 5.0.1...${NC}"
        yarn add react-scripts@5.0.1 --exact --silent 2>/dev/null || yarn add react-scripts@5.0.1 --exact
    fi

    # Asegurar que dotenv está instalado (requerido por craco.config.js)
    if ! node -e "require('dotenv')" 2>/dev/null; then
        echo -e "${CYAN}    Instalando dotenv (requerido por craco)...${NC}"
        yarn add dotenv --silent 2>/dev/null || yarn add dotenv
    fi
else
    npm install

    RS_VERSION=$(node -e "try{require('react-scripts/package.json');console.log(require('react-scripts/package.json').version)}catch(e){console.log('0.0.0')}" 2>/dev/null || echo "0.0.0")
    if [ "$RS_VERSION" = "0.0.0" ] || [ -z "$RS_VERSION" ]; then
        echo -e "${CYAN}    Instalando react-scripts 5.0.1...${NC}"
        npm install --save-exact react-scripts@5.0.1
    fi

    if ! node -e "require('dotenv')" 2>/dev/null; then
        echo -e "${CYAN}    Instalando dotenv (requerido por craco)...${NC}"
        npm install --save dotenv
    fi
fi

# Restaurar .env
if [ -n "$FRONTEND_ENV_CONTENT" ]; then
    echo "$FRONTEND_ENV_CONTENT" > .env
elif [ -n "$DOMAIN" ]; then
    cat > .env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false
EOF
fi

# Compilar
echo -e "${CYAN}    Compilando frontend (puede tardar unos minutos)...${NC}"
if command -v yarn &> /dev/null; then
    GENERATE_SOURCEMAP=false yarn build
else
    GENERATE_SOURCEMAP=false npm run build
fi

if [ -d "build" ] && [ -f "build/index.html" ]; then
    echo -e "${GREEN}  ✓ Frontend compilado correctamente${NC}"
else
    echo -e "${RED}  ✗ Error al compilar el frontend${NC}"
    exit 1
fi
cd "$APP_DIR"

# ── 6. LANDING: dependencias + build (si existe) ─────────────────────────────
if [ -d "$APP_DIR/landing" ]; then
    echo ""
    echo -e "${YELLOW}6) Actualizando landing...${NC}"
    cd "$APP_DIR/landing"

    LANDING_ENV_CONTENT=""
    if [ -f ".env" ]; then
        LANDING_ENV_CONTENT=$(cat .env)
    fi

    if command -v yarn &> /dev/null; then
        yarn install 2>/dev/null || yarn install
        if ! yarn list --pattern dotenv --depth=0 2>/dev/null | grep -q "dotenv@"; then
            yarn add dotenv --silent 2>/dev/null || yarn add dotenv
        fi
    else
        npm install
    fi

    if [ -n "$LANDING_ENV_CONTENT" ]; then
        echo "$LANDING_ENV_CONTENT" > .env
    fi

    if command -v yarn &> /dev/null; then
        GENERATE_SOURCEMAP=false yarn build
    else
        GENERATE_SOURCEMAP=false npm run build
    fi

    if [ -d "build" ]; then
        echo -e "${GREEN}  ✓ Landing compilado correctamente${NC}"
    else
        echo -e "${YELLOW}  ⚠ No se pudo compilar el landing${NC}"
    fi
    cd "$APP_DIR"
fi

# ── 7. REINICIAR BACKEND ──────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}7) Reiniciando servicio backend...${NC}"
systemctl start "$SERVICE_NAME"
sleep 4
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}  ✓ Servicio iniciado correctamente${NC}"
else
    echo -e "${RED}  ✗ Error al iniciar el servicio${NC}"
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

# ── 8. VERIFICAR ─────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}8) Verificando funcionamiento...${NC}"
sleep 2

# Detectar puerto del servicio
BACKEND_PORT=$(grep -oP 'port \K[0-9]+' /etc/systemd/system/${SERVICE_NAME}.service 2>/dev/null || echo "8001")
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${BACKEND_PORT}/api/health" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}  ✓ Backend respondiendo correctamente (HTTP 200)${NC}"
else
    echo -e "${YELLOW}  ⚠ Backend responde HTTP $HTTP_STATUS en puerto $BACKEND_PORT${NC}"
    echo -e "    Revisa los logs: journalctl -u $SERVICE_NAME -f"
fi

# ── RESUMEN ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}       ACTUALIZACIÓN COMPLETADA           ${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Backup en: ${CYAN}$BACKUP_FILE${NC}"
echo -e "  App en:    ${CYAN}https://$DOMAIN${NC}"
echo ""
echo -e "  Si hay problemas, restaura el backup:"
echo -e "  ${CYAN}tar -xzf $BACKUP_FILE -C $(dirname "$APP_DIR")${NC}"
echo ""
