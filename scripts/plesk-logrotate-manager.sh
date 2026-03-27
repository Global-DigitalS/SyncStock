#!/bin/bash

#===============================================================================
#
#          FILE: plesk-logrotate-manager.sh
#
#         USAGE: sudo bash plesk-logrotate-manager.sh [option]
#
#   DESCRIPTION: Manager de Log Rotation para Plesk Obsidian
#                Permite ejecutar limpieza de logs desde el panel de Plesk
#
#       VERSION: 1.0.0
#        AUTHOR: SyncStock
#
#===============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_FILE="/var/log/plesk-logrotate.log"
CLEANUP_SCRIPT="/usr/local/bin/cleanup-logs.sh"

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}         ${YELLOW}SyncStock - Log Rotation Manager for Plesk${NC}         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Este script debe ejecutarse como root"
        exit 1
    fi
}

# Función: ejecutar limpieza de logs
cleanup() {
    print_header
    echo "Ejecutando limpieza de logs..."
    echo ""

    if [ ! -f "$CLEANUP_SCRIPT" ]; then
        print_error "Script de limpieza no encontrado: $CLEANUP_SCRIPT"
        exit 1
    fi

    # Ejecutar limpieza
    $CLEANUP_SCRIPT

    print_success "Limpieza completada"
    echo ""
    echo "📋 Resultado:"
    du -sh /var/log
    echo ""
}

# Función: mostrar estado actual
status() {
    print_header
    echo "Estado actual de logs:"
    echo ""

    echo "1️⃣  Tamaño total de /var/log:"
    du -sh /var/log
    echo ""

    echo "2️⃣  Journal (systemd):"
    journalctl --disk-usage
    echo ""

    echo "3️⃣  Configuración de logrotate:"
    if [ -f /etc/logrotate.d/syncstock ]; then
        echo "   ✅ /etc/logrotate.d/syncstock existe"
    else
        echo "   ❌ /etc/logrotate.d/syncstock NO existe"
    fi
    echo ""

    echo "4️⃣  Script de limpieza:"
    if [ -f "$CLEANUP_SCRIPT" ]; then
        echo "   ✅ $CLEANUP_SCRIPT existe"
    else
        echo "   ❌ $CLEANUP_SCRIPT NO existe"
    fi
    echo ""

    echo "5️⃣  Cron job:"
    if crontab -l 2>/dev/null | grep -q "cleanup-logs.sh"; then
        echo "   ✅ Cron job agendado"
        crontab -l | grep cleanup-logs.sh
    else
        echo "   ❌ Cron job NO agendado"
    fi
    echo ""

    echo "6️⃣  Últimas limpiezas:"
    if [ -f "$LOG_FILE" ]; then
        tail -10 "$LOG_FILE"
    else
        echo "   Sin registros aún"
    fi
    echo ""
}

# Función: ver logs de limpieza
logs() {
    print_header
    echo "Logs de limpieza (/var/log/cleanup.log):"
    echo ""

    if [ ! -f /var/log/cleanup.log ]; then
        echo "   Sin registros aún"
        return
    fi

    tail -50 /var/log/cleanup.log
    echo ""
}

# Función: validar configuración
validate() {
    print_header
    echo "Validando configuración..."
    echo ""

    ERRORS=0

    # Validar logrotate
    if command -v logrotate &> /dev/null; then
        print_success "logrotate instalado"
    else
        print_error "logrotate NO instalado"
        ERRORS=$((ERRORS + 1))
    fi

    # Validar archivo de configuración
    if [ -f /etc/logrotate.d/syncstock ]; then
        if logrotate -d /etc/logrotate.d/syncstock > /dev/null 2>&1; then
            print_success "Configuración de logrotate válida"
        else
            print_error "Errores en configuración de logrotate"
            ERRORS=$((ERRORS + 1))
        fi
    else
        print_error "/etc/logrotate.d/syncstock NO existe"
        ERRORS=$((ERRORS + 1))
    fi

    # Validar journald
    if [ -f /etc/systemd/journald.conf.d/99-syncstock.conf ]; then
        print_success "systemd-journald configurado"
    else
        print_error "systemd-journald NO configurado"
        ERRORS=$((ERRORS + 1))
    fi

    # Validar script de limpieza
    if [ -f "$CLEANUP_SCRIPT" ] && [ -x "$CLEANUP_SCRIPT" ]; then
        print_success "Script de limpieza existe y es ejecutable"
    else
        print_error "Script de limpieza NO existe o no es ejecutable"
        ERRORS=$((ERRORS + 1))
    fi

    echo ""
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ Todo está configurado correctamente${NC}"
    else
        echo -e "${RED}❌ Se encontraron $ERRORS errores${NC}"
        exit 1
    fi
    echo ""
}

# Función: mostrar ayuda
show_help() {
    echo "SyncStock - Log Rotation Manager for Plesk"
    echo ""
    echo "Uso:"
    echo "  sudo bash plesk-logrotate-manager.sh cleanup   Ejecutar limpieza de logs"
    echo "  sudo bash plesk-logrotate-manager.sh status    Mostrar estado actual"
    echo "  sudo bash plesk-logrotate-manager.sh logs      Ver logs de limpieza"
    echo "  sudo bash plesk-logrotate-manager.sh validate  Validar configuración"
    echo "  sudo bash plesk-logrotate-manager.sh help      Mostrar esta ayuda"
    echo ""
}

# Main
check_root

case "${1:-status}" in
    cleanup)
        cleanup
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    validate)
        validate
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "Opción desconocida: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
