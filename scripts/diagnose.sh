#!/bin/bash
# =============================================================================
# SCRIPT DE DIAGNÓSTICO - SyncStock
# Ejecuta este script en tu servidor de producción para diagnosticar problemas
# =============================================================================

echo "=========================================="
echo "  DIAGNÓSTICO DE SYNCSTOCK"
echo "=========================================="
echo ""

# Detectar directorio de la aplicación
APP_DIR="/var/www/vhosts/app.sync-stock.com/app"
if [ ! -d "$APP_DIR" ]; then
    APP_DIR="/var/www/vhosts/$(hostname)/app"
fi
if [ ! -d "$APP_DIR" ]; then
    echo "⚠️  No se encontró el directorio de la aplicación"
    echo "Por favor, indica el directorio manualmente:"
    read -p "Directorio: " APP_DIR
fi

echo "📁 Directorio de la aplicación: $APP_DIR"
echo ""

# 1. Verificar servicios
echo "1️⃣  ESTADO DE SERVICIOS"
echo "------------------------"
if systemctl is-active --quiet syncstock-backend 2>/dev/null; then
    echo "✅ Backend: ACTIVO"
else
    echo "❌ Backend: INACTIVO"
    echo "   Intentando con nombre alternativo..."
    systemctl status syncstock* 2>/dev/null | head -5
fi
echo ""

# 2. Verificar logs del backend
echo "2️⃣  ÚLTIMOS ERRORES DEL BACKEND"
echo "--------------------------------"
BACKEND_LOG="/var/log/syncstock-backend.log"
if [ -f "$BACKEND_LOG" ]; then
    echo "Últimas 20 líneas con errores:"
    grep -i "error\|exception\|traceback" "$BACKEND_LOG" | tail -20
else
    echo "⚠️  Log no encontrado en $BACKEND_LOG"
    echo "Buscando logs alternativos..."
    find /var/log -name "*syncstock*" -o -name "*syncstock*" 2>/dev/null | head -5
fi
echo ""

# 3. Verificar journalctl
echo "3️⃣  LOGS DE SYSTEMD"
echo "-------------------"
journalctl -u syncstock-backend --no-pager -n 30 2>/dev/null || echo "No se encontraron logs de systemd"
echo ""

# 4. Verificar conexión a MongoDB
echo "4️⃣  CONEXIÓN A MONGODB"
echo "----------------------"
if [ -f "$APP_DIR/backend/.env" ]; then
    source "$APP_DIR/backend/.env"
    echo "MONGO_URL configurada: ${MONGO_URL:0:30}..."
    
    # Intentar conectar
    if command -v mongosh &> /dev/null; then
        mongosh "$MONGO_URL" --eval "db.stats()" 2>&1 | head -10
    elif command -v mongo &> /dev/null; then
        mongo "$MONGO_URL" --eval "db.stats()" 2>&1 | head -10
    else
        echo "⚠️  Cliente de MongoDB no instalado, no se puede verificar conexión"
    fi
else
    echo "❌ No se encontró archivo .env en $APP_DIR/backend/"
fi
echo ""

# 5. Verificar puertos
echo "5️⃣  PUERTOS EN USO"
echo "------------------"
echo "Puerto 8001 (Backend):"
netstat -tlnp 2>/dev/null | grep 8001 || ss -tlnp | grep 8001
echo ""

# 6. Verificar Nginx
echo "6️⃣  CONFIGURACIÓN DE NGINX"
echo "--------------------------"
if [ -f "/etc/nginx/conf.d/app.sync-stock.com.conf" ]; then
    echo "Configuración encontrada:"
    cat "/etc/nginx/conf.d/app.sync-stock.com.conf" | head -50
elif [ -d "/etc/nginx/vhosts" ]; then
    echo "Buscando en vhosts de Plesk..."
    find /etc/nginx/vhosts -name "*sync-stock*" -exec cat {} \; 2>/dev/null | head -50
else
    echo "⚠️  Configuración de Nginx no encontrada"
fi
echo ""

# 7. Probar endpoint de suppliers
echo "7️⃣  PROBANDO ENDPOINT /api/suppliers"
echo "-------------------------------------"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8001/api/suppliers 2>/dev/null || echo "❌ No se pudo conectar al backend"
echo ""

# 8. Verificar versión del código
echo "8️⃣  VERSIÓN DEL CÓDIGO"
echo "----------------------"
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    echo "Último commit: $(git log -1 --format='%H %s' 2>/dev/null)"
    echo "Rama actual: $(git branch --show-current 2>/dev/null)"
else
    echo "⚠️  No es un repositorio git"
fi
echo ""

# 9. Verificar dependencias Python
echo "9️⃣  DEPENDENCIAS PYTHON"
echo "-----------------------"
if [ -f "$APP_DIR/backend/venv/bin/python" ]; then
    echo "Versión de Python:"
    "$APP_DIR/backend/venv/bin/python" --version
    echo ""
    echo "Paquetes instalados (primeros 20):"
    "$APP_DIR/backend/venv/bin/pip" list 2>/dev/null | head -20
else
    echo "⚠️  Virtual environment no encontrado"
fi
echo ""

echo "=========================================="
echo "  DIAGNÓSTICO COMPLETADO"
echo "=========================================="
echo ""
echo "📋 Copia la salida de este script y compártela para analizar los problemas."
