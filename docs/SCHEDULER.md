# Scheduler Service - BullMQ-style Job Queue para Scraping

Este documento describe el sistema de programación de trabajos de scraping de competidores en SyncStock.

## Arquitectura

El sistema está compuesto por varios componentes:

### 1. **scraper_scheduler.py** - Gestor de trabajos
- `CrawlJob`: Dataclass que representa un trabajo de scraping
- `JobStatus`: Enum con estados (pending, running, completed, failed, retrying, cancelled)
- Funciones para crear, actualizar, consultar y gestionar trabajos
- Lógica de reintentos con backoff exponencial

### 2. **job_executor.py** - Ejecutor de trabajos
- `execute_job()`: Ejecuta un único trabajo de scraping
- `process_pending_jobs()`: Procesa un lote de trabajos pendientes
- `start_scheduler_worker()`: Worker de ejecución continua (background)
- Respeta límites de concurrencia por usuario

### 3. **http_client.py** - Cliente HTTP mejorado
- Timeouts configurables por tipo de fuente (FTP: 120s, URL: 30s, general: 45s)
- Método `get_timeout_for_source()` para determinar timeout recomendado
- Reintentos automáticos con rotación de proxies

### 4. **routes/competitors.py** - API endpoints
- `POST /competitors/jobs/schedule` - Programar un trabajo
- `GET /competitors/jobs` - Listar trabajos
- `GET /competitors/jobs/{job_id}` - Detalles de un trabajo
- `POST /competitors/jobs/{job_id}/cancel` - Cancelar un trabajo
- `GET /competitors/jobs/stats/summary` - Estadísticas de ejecución

## Características

### Reintentos con Backoff Exponencial
Los trabajos fallidos se retentan automáticamente con estos delays:
- 1er intento fallido: Esperar 3 minutos
- 2do intento fallido: Esperar 5 minutos
- 3er intento fallido: Esperar 10 minutos
- Después: Marcar como definitivamente fallido

```python
# Configurar en scraper_scheduler.py
RETRY_DELAYS = [3, 5, 10]  # minutos
MAX_RETRIES = 3
```

### Límites de Concurrencia
- **Por usuario**: Máximo 3 scrapings simultáneos
- **Sistema-wide**: Máximo 10 scrapings simultáneos

```python
# Configurar en scraper_scheduler.py
MAX_CONCURRENT_CRAWLS_PER_USER = 3
MAX_CONCURRENT_CRAWLS_SYSTEM_WIDE = 10
```

### Timeouts Configurables
Different sources tienen diferentes timeouts:
```python
_REQUEST_TIMEOUT = 45      # General HTTP requests
_FTP_TIMEOUT = 120         # FTP/SFTP downloads
_URL_TIMEOUT = 30          # Normal web URLs
```

### Monitoreo y Estadísticas
Cada trabajo registra:
- `started_at`: Timestamp de inicio
- `completed_at`: Timestamp de finalización
- `duration_seconds`: Duración total
- `products_found`: Productos encontrados
- `products_matched`: Productos emparejados
- `products_alerts`: Alertas generadas
- `error_message`: Error si falló
- `next_retry_at`: Próximo reintento programado

## Uso - API REST

### Programar un scraping manual

```bash
curl -X POST http://localhost:8001/api/competitors/jobs/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "competitor_id": "comp-123",
    "immediate": true
  }' \
  -b "cookies.txt"
```

Respuesta:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "competitor_id": "comp-123",
  "scheduled_at": null,
  "message": "Trabajo encolado para ejecución inmediata"
}
```

### Listar trabajos de un usuario

```bash
curl http://localhost:8001/api/competitors/jobs?status=running&limit=20 \
  -b "cookies.txt"
```

Respuesta:
```json
{
  "jobs": [
    {
      "id": "job-123",
      "user_id": "user-456",
      "competitor_id": "comp-789",
      "status": "running",
      "attempts": 0,
      "started_at": "2025-03-30T10:30:00Z",
      "products_found": 250,
      ...
    }
  ],
  "total": 5,
  "offset": 0,
  "limit": 20
}
```

### Obtener detalles de un trabajo

```bash
curl http://localhost:8001/api/competitors/jobs/job-123 \
  -b "cookies.txt"
```

### Cancelar un trabajo

```bash
curl -X POST http://localhost:8001/api/competitors/jobs/job-123/cancel \
  -b "cookies.txt"
```

### Ver estadísticas de trabajos

```bash
curl http://localhost:8001/api/competitors/jobs/stats/summary?days=7 \
  -b "cookies.txt"
```

Respuesta:
```json
{
  "period_days": 7,
  "total_jobs": 42,
  "completed": 38,
  "failed": 2,
  "retrying": 2,
  "avg_duration_seconds": 45.3,
  "total_products_found": 2450,
  "total_products_matched": 1890,
  "total_alerts": 156,
  "success_rate": 90.48
}
```

## Configuración - Sincronización Automática

Para programar scrapings automáticos a intervalo regular (ej: cada 6 horas):

1. En la configuración del usuario (`sync_config`):
   ```python
   {
     "sync_competitors": True,
     "competitor_sync_interval": 6  # horas
   }
   ```

2. El scheduler verificará automáticamente:
   ```python
   # En job_executor.py
   await schedule_user_crawls(user_id)  # Se llama periódicamente
   ```

3. Los trabajos se crean y se encolan para ejecución.

## Despliegue - Worker Background

Para ejecutar el scheduler worker en producción:

### Opción 1: systemd service (recomendado)

Crear `/etc/systemd/system/syncstock-scheduler.service`:

```ini
[Unit]
Description=SyncStock Scheduler Worker
After=network.target
Requires=syncstock-backend.service

[Service]
Type=simple
User=syncstock
WorkingDirectory=/opt/syncstock
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 -m services.scheduler_worker
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl enable syncstock-scheduler
sudo systemctl start syncstock-scheduler
sudo systemctl status syncstock-scheduler

# Ver logs
sudo journalctl -u syncstock-scheduler -f
```

### Opción 2: Integración en aplicación principal

Iniciar el worker como tarea background en server.py:

```python
import asyncio
from services.scrapers.job_executor import start_scheduler_worker

async def start_scheduler():
    """Inicia el worker del scheduler en background"""
    asyncio.create_task(
        start_scheduler_worker(
            poll_interval_seconds=60,  # Chequear cada minuto
            batch_size=10,             # Procesar 10 jobs por lote
            max_runtime_hours=23       # Reiniciar worker cada 23 horas
        )
    )

# En server.py startup event:
@app.on_event("startup")
async def startup_event():
    await ensure_indexes()
    await start_scheduler()  # <-- Añadir esta línea
```

### Opción 3: Celery / RQ (para deployments más grandes)

Para sistemas con muchos usuarios, usar Celery con Redis:

```python
# celery_worker.py
from celery import Celery
from services.scrapers.job_executor import process_pending_jobs

app = Celery('syncstock')

@app.task
def process_crawl_jobs():
    return asyncio.run(process_pending_jobs(batch_size=10))

# crontab: ejecutar cada minuto
from celery.schedules import crontab
app.conf.beat_schedule = {
    'process-crawl-jobs': {
        'task': 'celery_worker.process_crawl_jobs',
        'schedule': crontab(),  # Cada minuto
    },
}
```

## Monitoreo

### Logs
- Los trabajos registran eventos en el logger `services.scrapers.job_executor`
- Verificar logs con: `grep "Crawl job" /var/log/syncstock.log`

### Métricas
- `GET /api/competitors/jobs/stats/summary` devuelve tasa de éxito y métricas
- Dashboards en `GET /api/competitors/dashboard/table` muestran estados recientes

### Alertas Recomendadas
- Tasa de éxito < 80% en los últimos 7 días
- Número de trabajos fallidos acumulándose sin reintentar
- Duración de trabajos > timeout configurado (posible cuelgue)

## Troubleshooting

### Trabajos atascados en "running"
Si un trabajo está en estado "running" pero debería haber completado:
1. Verificar logs: `grep "job-id" /var/log/syncstock.log`
2. Cancelar manualmente: `POST /api/competitors/jobs/job-id/cancel`
3. Reintentar: Se reintentará automáticamente

### Trabajos que no se retentan
1. Verificar `MAX_RETRIES` (default 3 reintentos)
2. Verificar delays en `RETRY_DELAYS`
3. Revisar `error_message` en detalles del trabajo

### Límites de concurrencia alcanzados
Esperar a que se completen trabajos actuales, o:
1. Aumentar `MAX_CONCURRENT_CRAWLS_PER_USER`
2. Usar workers separados para usuarios diferentes

### Timeouts en descargas
Si FTP/SFTP falla por timeout:
1. Aumentar `_FTP_TIMEOUT` (default 120s)
2. Verificar velocidad de conexión del servidor
3. Considerar usar conexión más rápida o proxy
