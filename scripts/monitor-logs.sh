#!/bin/bash

#===============================================================================
#
#          FILE: monitor-logs.sh
#
#         USAGE: sudo bash monitor-logs.sh [threshold_mb]
#                sudo bash monitor-logs.sh          # Default: 500MB
#                sudo bash monitor-logs.sh 1000     # Alert si > 1GB
#
#   DESCRIPTION: Monitorear tamaño de logs y alertar si exceden límite
#                Se puede ejecutar desde cron cada hora
#
#       VERSION: 1.0.0
#        AUTHOR: SyncStock
#
#===============================================================================

set -e

# Configuración
THRESHOLD_MB=${1:-500}          # Default 500MB
THRESHOLD_BYTES=$((THRESHOLD_MB * 1024 * 1024))
LOG_DIR="/var/log"
ALERT_LOG="/var/log/log-monitor.log"
EMAIL_RECIPIENT=""             # Dejar vacío para desabilitar email

# Colores
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Obtener tamaño actual
get_log_size() {
    du -bs "$LOG_DIR" 2>/dev/null | cut -f1
}

# Formatear bytes a MB/GB
format_size() {
    local bytes=$1
    local mb=$((bytes / 1024 / 1024))
    local gb=$((mb / 1024))

    if [ $gb -gt 0 ]; then
        echo "${gb}GB"
    else
        echo "${mb}MB"
    fi
}

# Enviar alerta por email (opcional)
send_email_alert() {
    if [ -z "$EMAIL_RECIPIENT" ]; then
        return
    fi

    if ! command -v mail &> /dev/null; then
        return
    fi

    local current_size=$(format_size "$(get_log_size)")
    local threshold_formatted=$(format_size "$THRESHOLD_BYTES")
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    mail -s "⚠️  ALERTA: Logs de SyncStock exceden ${threshold_formatted}" "$EMAIL_RECIPIENT" << EOF
Timestamp: $timestamp
Servidor: $(hostname)

Tamaño actual de /var/log: $current_size
Límite configurado: $threshold_formatted

Los logs de SyncStock están ocupando más espacio del permitido.

Acciones recomendadas:
1. Ejecutar: sudo /usr/local/bin/cleanup-logs.sh
2. Ver logs por directorios: du -sh /var/log/*

Más información:
sudo bash /home/user/SyncStock/scripts/plesk-logrotate-manager.sh status
EOF
}

# Loguear evento
log_event() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" >> "$ALERT_LOG"
}

# Main
main() {
    current_size=$(get_log_size)
    current_formatted=$(format_size "$current_size")
    threshold_formatted=$(format_size "$THRESHOLD_BYTES")
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Escribir log
    echo "[$timestamp] Verificación: $current_formatted (límite: $threshold_formatted)" >> "$ALERT_LOG"

    # Verificar si excede límite
    if [ "$current_size" -gt "$THRESHOLD_BYTES" ]; then
        echo -e "${RED}❌ ALERTA: Logs exceden límite${NC}"
        echo "   Tamaño actual: $current_formatted"
        echo "   Límite: $threshold_formatted"
        echo ""

        # Loguear
        log_event "CRITICAL" "Logs exceeding threshold: $current_formatted > $threshold_formatted"

        # Enviar email si está configurado
        send_email_alert

        # Mostrar top 10 directorios
        echo "Top 10 directorios por tamaño:"
        du -sh "$LOG_DIR"/* 2>/dev/null | sort -rh | head -10

        echo ""
        echo "Ejecutar limpieza:"
        echo "  sudo /usr/local/bin/cleanup-logs.sh"
        echo ""

        return 1
    else
        echo -e "${GREEN}✅ OK: Logs dentro del límite${NC}"
        echo "   Tamaño actual: $current_formatted"
        echo "   Límite: $threshold_formatted"

        log_event "INFO" "Logs OK: $current_formatted < $threshold_formatted"

        return 0
    fi
}

main "$@"
