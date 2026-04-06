# Log Rotation - FIX 8

Documentación completa para gestionar y monitorear logs en SyncStock.

## 📋 Contenido

1. [Descripción](#descripción)
2. [Componentes](#componentes)
3. [Uso Manual](#uso-manual)
4. [Automatización](#automatización)
5. [Monitoreo](#monitoreo)
6. [Troubleshooting](#troubleshooting)

---

## Descripción

FIX 8 implementa un sistema completo de **rotación y limpieza automática de logs** para:

- ✅ Prevenir que `/var/log` llene el disco (antes: 90GB+, ahora: 300MB-500MB)
- ✅ Comprimir logs antiguos automáticamente (80-90% reducción)
- ✅ Mantener 7 días de histórico de logs
- ✅ Limpiar journal de systemd (antes: 450MB, ahora: <100MB)
- ✅ Alertar si los logs exceden límite configurado
- ✅ Se ejecuta automáticamente a las 3 AM

---

## Componentes

### 1. Logrotate (`/etc/logrotate.d/syncstock`)

Configuración estándar para rotar logs diariamente:

```
/var/log/syncstock.log        → Rota diariamente, mantiene 7 días
/var/log/nginx/*.log          → Rota diariamente, mantiene 5 días
```

**Acciones automáticas:**
- Comprime archivos con gzip (`.gz`)
- Ejecuta reload de backend después de rotación
- Reinicia nginx si es necesario

### 2. Systemd-Journald (`/etc/systemd/journald.conf.d/99-syncstock.conf`)

Limita automáticamente el tamaño del journal:

```
SystemMaxUse=300M            → Máximo 300MB total
SystemMaxFileSize=50M        → Máximo 50MB por archivo
MaxRetentionSec=7day         → Mantener 7 días
```

### 3. Script de Limpieza (`/usr/local/bin/cleanup-logs.sh`)

Ejecutado diariamente a las 3 AM:

```bash
# Se ejecuta cada día:
journalctl --vacuum-size=300M      # Limpiar journal
truncate -s 0 /var/log/btmp*       # Limpiar intentos fallidos
logrotate -f /etc/logrotate.d/*    # Forzar rotación
```

### 4. Manager para Plesk (`scripts/plesk-logrotate-manager.sh`)

Interfaz para ejecutar acciones desde el CLI o Plesk:

```bash
sudo bash plesk-logrotate-manager.sh cleanup   # Limpiar logs ahora
sudo bash plesk-logrotate-manager.sh status    # Ver estado actual
sudo bash plesk-logrotate-manager.sh logs      # Ver registros
sudo bash plesk-logrotate-manager.sh validate  # Validar config
```

### 5. Monitor de Logs (`scripts/monitor-logs.sh`)

Alerta si los logs exceden límite configurado:

```bash
sudo bash monitor-logs.sh          # Check con límite default (500MB)
sudo bash monitor-logs.sh 1000     # Check con límite 1GB
```

---

## Uso Manual

### Ver Estado Actual

```bash
# Tamaño de /var/log
du -sh /var/log

# Desglose por directorio
du -sh /var/log/* | sort -rh

# Journal
journalctl --disk-usage

# Logs de limpieza
tail -50 /var/log/cleanup.log
```

### Ejecutar Limpieza Manualmente

```bash
# Método 1: Ejecutar script directamente
sudo /usr/local/bin/cleanup-logs.sh

# Método 2: Usar manager de Plesk
sudo bash scripts/plesk-logrotate-manager.sh cleanup

# Método 3: Forzar rotación con logrotate
sudo logrotate -f /etc/logrotate.d/syncstock
```

### Ver Configuración

```bash
# Logrotate
cat /etc/logrotate.d/syncstock

# Systemd-journald
cat /etc/systemd/journald.conf.d/99-syncstock.conf

# Cron job
crontab -l | grep cleanup-logs
```

### Validar Configuración

```bash
# Syntax check de logrotate (dry run)
sudo logrotate -d /etc/logrotate.d/syncstock

# Validar con manager
sudo bash scripts/plesk-logrotate-manager.sh validate
```

---

## Automatización

### Cron Job

Se ejecuta automáticamente a las **3 AM** cada día:

```bash
0 3 * * * /usr/local/bin/cleanup-logs.sh
```

Ver y editar:

```bash
# Ver cron jobs actuales
crontab -l

# Editar cron jobs
crontab -e

# Agregar manualmente
echo "0 3 * * * /usr/local/bin/cleanup-logs.sh" | crontab -
```

### Cambiar Hora de Ejecución

```bash
# Ejecutar a las 2 AM en lugar de 3 AM
crontab -e
# Cambiar "0 3 * * *" a "0 2 * * *"
```

### Ejecutar Múltiples Veces al Día

```bash
# Ejecutar cada 4 horas
0 0,4,8,12,16,20 * * * /usr/local/bin/cleanup-logs.sh

# Ejecutar cada hora
0 * * * * /usr/local/bin/cleanup-logs.sh
```

---

## Monitoreo

### Alertar si Logs Crecen Demasiado

Agendar monitor en cron:

```bash
# Verificar cada hora (default 500MB)
0 * * * * sudo bash /home/user/SyncStock/scripts/monitor-logs.sh

# Verificar cada 6 horas (límite 1GB)
0 0,6,12,18 * * * sudo bash /home/user/SyncStock/scripts/monitor-logs.sh 1000
```

### Configurar Email de Alertas

Editar `/home/user/SyncStock/scripts/monitor-logs.sh`:

```bash
# Cambiar:
EMAIL_RECIPIENT=""

# A:
EMAIL_RECIPIENT="admin@miempresa.com"
```

Luego:
```bash
# Instalar utilidad de email (si no existe)
sudo apt-get install mailutils
```

### Ver Logs de Monitoreo

```bash
# Logs del monitor
tail -50 /var/log/log-monitor.log

# Logs de limpieza
tail -50 /var/log/cleanup.log
```

---

## Resultados Esperados

### Antes de FIX 8

```
/var/log:        90GB
├── journal:     ~450MB
├── nginx:       ~200MB
├── plesk:       ~150MB
├── mongodb:     ~100MB
└── otros:       89GB+
```

### Después de FIX 8

```
/var/log:        ~500MB (MÁXIMO)
├── journal:     ~100MB (limpiado automáticamente)
├── nginx:       ~100MB (rotado y comprimido)
├── plesk:       ~50MB (limpieza de antiguos)
├── mongodb:     ~100MB
└── otros:       ~50MB
```

**Reducción: ~90GB → 500MB (ahorro de ~180x)**

---

## Troubleshooting

### Problema: Los logs no se rotan

**Síntoma:** Los archivos `.log.1.gz` no aparecen

**Solución:**

```bash
# 1. Validar sintaxis
sudo logrotate -d /etc/logrotate.d/syncstock

# 2. Forzar rotación manualmente
sudo logrotate -f /etc/logrotate.d/syncstock

# 3. Verificar permisos
ls -la /var/log/syncstock.log
ls -la /etc/logrotate.d/syncstock

# 4. Ver logs de logrotate
sudo journalctl -u logrotate -n 20
```

### Problema: Journal no se limpia

**Síntoma:** `journalctl --disk-usage` muestra > 300MB

**Solución:**

```bash
# 1. Forzar limpieza inmediata
sudo journalctl --vacuum-size=300M
sudo journalctl --rotate

# 2. Reiniciar journald
sudo systemctl restart systemd-journald

# 3. Verificar configuración
cat /etc/systemd/journald.conf.d/99-syncstock.conf

# 4. Si no funciona, editar directamente
sudo systemctl stop systemd-journald
sudo rm -rf /var/log/journal/*/
sudo systemctl start systemd-journald
```

### Problema: Espacio de disco sigue siendo alto

**Solución:**

```bash
# 1. Identificar culprables
du -sh /var/log/* | sort -rh

# 2. Ver archivos grandes
find /var/log -type f -size +100M

# 3. Limpiar específicamente
# Journal
sudo journalctl --vacuum-size=100M

# Plesk
sudo truncate -s 0 /var/log/plesk/*

# MongoDB
sudo truncate -s 0 /var/log/mongodb/*

# 4. Ejecutar limpieza completa
sudo /usr/local/bin/cleanup-logs.sh
```

### Problema: Cron job no se ejecuta

**Solución:**

```bash
# 1. Verificar cron está habilitado
sudo systemctl status cron

# 2. Ver si cron job existe
crontab -l | grep cleanup-logs.sh

# 3. Ver logs de cron
sudo tail -50 /var/log/syslog | grep CRON

# 4. Re-agregar si es necesario
echo "0 3 * * * /usr/local/bin/cleanup-logs.sh" | crontab -

# 5. Probar ejecución manual
sudo /usr/local/bin/cleanup-logs.sh
```

---

## Integración con Plesk

### Opción 1: Manual desde CLI

```bash
sudo bash /home/user/SyncStock/scripts/plesk-logrotate-manager.sh status
sudo bash /home/user/SyncStock/scripts/plesk-logrotate-manager.sh cleanup
```

### Opción 2: Crear botón en Plesk (Advanced)

```bash
# Crear archivo en Plesk
sudo tee /usr/local/psa/admin/conf/custom.xml > /dev/null << 'EOF'
<extension name="SyncStock Log Manager">
  <action id="syncstock.cleanup.logs" when="after">
    <type>script</type>
    <script>/home/user/SyncStock/scripts/plesk-logrotate-manager.sh cleanup</script>
  </action>
</extension>
EOF

# Reiniciar Plesk
sudo plesk repair
```

### Opción 3: Script Plesk Extension

```bash
# Para Plesk 18+, crear extensión:
sudo mkdir -p /usr/local/psa/admin/plib/modules/syncstock
sudo tee /usr/local/psa/admin/plib/modules/syncstock/index.php > /dev/null << 'EOF'
<?php
// SyncStock Log Manager for Plesk
if ($_POST['action'] == 'cleanup_logs') {
    shell_exec('sudo /usr/local/bin/cleanup-logs.sh');
    echo json_encode(['status' => 'success']);
}
?>
EOF
```

---

## Referencias

- [Logrotate Manual](https://linux.die.net/man/8/logrotate)
- [Systemd Journal](https://www.freedesktop.org/software/systemd/man/journald.conf.html)
- [Cron Syntax](https://crontab.guru/)

---

**Última actualización:** 2026-03-27
**Versión:** 1.0.0
**Status:** ✅ Completo
