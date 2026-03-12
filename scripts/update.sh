#!/bin/bash
# =============================================================================
# SCRIPT DE ACTUALIZACIÓN - SyncStock
# Ejecuta este script en tu servidor de producción para actualizar la app
# =============================================================================

set -e  # Salir si hay error

echo "=========================================="
echo "  ACTUALIZACIÓN DE SYNCSTOCK"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración - AJUSTA ESTOS VALORES
APP_DIR="${APP_DIR:-/var/www/vhosts/app.sync-stock.com/app}"
BACKUP_DIR="/var/backups/syncstock"
SERVICE_NAME="syncstock-backend"
DOMAIN="app.sync-stock.com"

# Verificar que existe el directorio
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Error: No se encontró el directorio $APP_DIR${NC}"
    echo "Por favor, ejecuta con: APP_DIR=/ruta/correcta ./update.sh"
    exit 1
fi

cd "$APP_DIR"
echo -e "${GREEN}📁 Directorio: $APP_DIR${NC}"

# 1. Crear backup
echo ""
echo -e "${YELLOW}1️⃣  Creando backup...${NC}"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" --exclude='node_modules' --exclude='venv' --exclude='__pycache__' . 2>/dev/null || true
echo -e "${GREEN}✅ Backup creado: $BACKUP_FILE${NC}"

# 2. Detener servicio
echo ""
echo -e "${YELLOW}2️⃣  Deteniendo servicio backend...${NC}"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
echo -e "${GREEN}✅ Servicio detenido${NC}"

# 3. Actualizar código (si es git)
echo ""
echo -e "${YELLOW}3️⃣  Actualizando código...${NC}"
if [ -d ".git" ]; then
    git fetch origin
    git pull origin main 2>/dev/null || git pull origin master
    echo -e "${GREEN}✅ Código actualizado desde git${NC}"
else
    echo -e "${YELLOW}⚠️  No es repositorio git. Actualiza manualmente los archivos.${NC}"
fi

# 4. Actualizar dependencias del backend
echo ""
echo -e "${YELLOW}4️⃣  Actualizando dependencias del backend...${NC}"
cd backend

# Crear venv si no existe
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo -e "${GREEN}✅ Dependencias del backend actualizadas${NC}"

# 5. Actualizar dependencias del frontend
echo ""
echo -e "${YELLOW}5️⃣  Actualizando dependencias del frontend...${NC}"
cd frontend
if command -v yarn &> /dev/null; then
    yarn install --frozen-lockfile 2>/dev/null || yarn install
else
    npm install
fi
echo -e "${GREEN}✅ Dependencias del frontend actualizadas${NC}"

# 6. Construir frontend
echo ""
echo -e "${YELLOW}6️⃣  Construyendo frontend...${NC}"
if command -v yarn &> /dev/null; then
    REACT_APP_BACKEND_URL="https://$DOMAIN" yarn build
else
    REACT_APP_BACKEND_URL="https://$DOMAIN" npm run build
fi
cd ..
echo -e "${GREEN}✅ Frontend construido${NC}"

# 7. Reiniciar servicio
echo ""
echo -e "${YELLOW}7️⃣  Reiniciando servicio backend...${NC}"
systemctl start "$SERVICE_NAME"
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
else
    echo -e "${RED}❌ Error al iniciar el servicio${NC}"
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

# 8. Verificar que funciona
echo ""
echo -e "${YELLOW}8️⃣  Verificando funcionamiento...${NC}"
sleep 2
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend respondiendo correctamente (HTTP 200)${NC}"
else
    echo -e "${RED}❌ Backend no responde correctamente (HTTP $HTTP_STATUS)${NC}"
    echo "Revisa los logs con: journalctl -u $SERVICE_NAME -f"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  ACTUALIZACIÓN COMPLETADA${NC}"
echo "=========================================="
echo ""
echo "📋 Próximos pasos:"
echo "   1. Verifica la aplicación en https://$DOMAIN"
echo "   2. Si hay problemas, restaura el backup:"
echo "      tar -xzf $BACKUP_FILE -C $APP_DIR"
echo ""
