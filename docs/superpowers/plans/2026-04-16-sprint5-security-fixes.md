# Sprint 5: Security Fixes — Conexiones con Proveedores

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir los 3 problemas críticos y 2 altos identificados en la auditoría de seguridad del sistema de sincronización de proveedores.

**Architecture:** Fixes quirúrgicos en 4 archivos existentes — sin nuevas abstracciones. Cada fix es independiente y puede desplegarse por separado. TDD: test primero, implementación después.

**Tech Stack:** Python 3.11+, FastAPI, Motor (async MongoDB), pytest, pytest-asyncio

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `backend/config.py` | Agregar `MAX_DOWNLOAD_SIZE`, `MAX_ZIP_FILES` |
| `backend/routes/suppliers.py` | Guard race condition en línea ~227 |
| `backend/services/sync/downloaders.py` | Límite de descarga en `download_file_from_url_sync` + SSRF localhost |
| `backend/services/sync/parsers.py` | Límite de archivos en `extract_zip_files` |
| `backend/services/sync/product_sync.py` | Fix upsert duplicado en bloque de productos existentes |
| `backend/tests/test_sprint5_security.py` | Nuevo archivo de tests |

---

## Task 1: Race Condition Guard en Sync Manual

**Problema:** `POST /suppliers/{id}/sync` no verifica si `sync_status == "running"` antes de lanzar la tarea. Dos peticiones simultáneas duplican productos.

**Archivos:**
- Modify: `backend/routes/suppliers.py:227` (antes de `update_by_id`)
- Test: `backend/tests/test_sprint5_security.py`

- [ ] **Paso 1.1: Escribir el test que falla**

```python
# backend/tests/test_sprint5_security.py
import pytest

class TestRaceConditionGuard:
    """Task 1: Race condition en sync manual."""

    @pytest.mark.asyncio
    async def test_sync_rechazado_si_ya_esta_corriendo(self, test_client, auth_headers, supplier_running):
        """Segunda llamada a /sync debe retornar 409 si ya hay sync en progreso."""
        response = test_client.post(
            f"/api/suppliers/{supplier_running['id']}/sync",
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "progreso" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_sync_permitido_si_status_es_idle(self, test_client, auth_headers, supplier_idle):
        """Llamada a /sync debe retornar 200 si sync_status es idle."""
        response = test_client.post(
            f"/api/suppliers/{supplier_idle['id']}/sync",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    @pytest.mark.asyncio
    async def test_sync_permitido_si_status_es_error(self, test_client, auth_headers, supplier_error):
        """Llamada a /sync debe permitirse si sync_status es error (reintentar)."""
        response = test_client.post(
            f"/api/suppliers/{supplier_error['id']}/sync",
            headers=auth_headers
        )
        assert response.status_code == 200
```

- [ ] **Paso 1.2: Ejecutar para confirmar que falla**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestRaceConditionGuard -v 2>&1 | head -30
```

Expected: `FAILED` o `ERROR` (fixtures no existen aún, está bien)

- [ ] **Paso 1.3: Agregar el guard en suppliers.py**

En `backend/routes/suppliers.py`, línea ~227, justo ANTES de `# Mark sync as running`, agregar la verificación:

```python
# Guard contra race condition: rechazar si ya hay sync en progreso
current_status = supplier.get("sync_status")
if current_status == "running":
    raise HTTPException(
        status_code=409,
        detail="La sincronización ya está en progreso para este proveedor."
    )

# Mark sync as running immediately so the UI can show progress
await SupplierRepository.update_by_id(
    supplier_id,
    {"sync_status": "running", "sync_started_at": datetime.now(UTC).isoformat()}
)
```

El bloque reemplaza exactamente:
```python
    # Mark sync as running immediately so the UI can show progress
    await SupplierRepository.update_by_id(
```

Por:
```python
    # Guard contra race condition: rechazar si ya hay sync en progreso
    current_status = supplier.get("sync_status")
    if current_status == "running":
        raise HTTPException(
            status_code=409,
            detail="La sincronización ya está en progreso para este proveedor."
        )

    # Mark sync as running immediately so the UI can show progress
    await SupplierRepository.update_by_id(
```

- [ ] **Paso 1.4: Commit**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/routes/suppliers.py
git commit -m "fix: race condition en sync manual — rechazar 409 si sync_status=running"
```

---

## Task 2: Límite de Descarga (500 MB)

**Problema:** `download_file_from_url_sync` usa `response.content` que carga el archivo completo en memoria sin límite. Un archivo de 5 GB causa OOM.

**Archivos:**
- Modify: `backend/config.py` (agregar `MAX_DOWNLOAD_SIZE`)
- Modify: `backend/services/sync/downloaders.py:163-170` (reemplazar `response.content`)
- Test: `backend/tests/test_sprint5_security.py`

- [ ] **Paso 2.1: Escribir el test que falla**

```python
# Agregar a backend/tests/test_sprint5_security.py

from unittest.mock import patch, MagicMock
from backend.services.sync.downloaders import download_file_from_url_sync

class TestDownloadSizeLimit:
    """Task 2: Límite de tamaño de descarga."""

    def test_archivo_demasiado_grande_via_content_length(self):
        """Content-Length mayor al límite debe lanzar ValueError antes de descargar."""
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": str(600 * 1024 * 1024)}  # 600 MB
        mock_response.raise_for_status = MagicMock()

        with patch("backend.services.sync.downloaders._build_browser_session") as mock_session:
            mock_session.return_value.get.return_value = mock_response
            with pytest.raises(ValueError, match="grande"):
                download_file_from_url_sync("http://example.com/file.csv")

    def test_archivo_demasiado_grande_via_streaming(self):
        """Archivo que supera el límite durante streaming debe lanzar ValueError."""
        chunk_600mb = b"x" * (600 * 1024 * 1024)

        mock_response = MagicMock()
        mock_response.headers = {}  # Sin Content-Length
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = iter([chunk_600mb])

        with patch("backend.services.sync.downloaders._build_browser_session") as mock_session:
            mock_session.return_value.get.return_value = mock_response
            with pytest.raises(ValueError, match="límite"):
                download_file_from_url_sync("http://example.com/file.csv")

    def test_archivo_dentro_del_limite(self):
        """Archivo de 100 MB debe descargarse correctamente."""
        chunk_100mb = b"x" * (100 * 1024 * 1024)

        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": str(100 * 1024 * 1024)}
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = iter([chunk_100mb])

        with patch("backend.services.sync.downloaders._validate_url_ssrf"):
            with patch("backend.services.sync.downloaders._build_browser_session") as mock_session:
                mock_session.return_value.get.return_value = mock_response
                result = download_file_from_url_sync("http://example.com/file.csv")
                assert result == chunk_100mb
```

- [ ] **Paso 2.2: Ejecutar para confirmar que falla**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestDownloadSizeLimit -v 2>&1 | head -30
```

Expected: `FAILED` — la función actual no lanza ValueError

- [ ] **Paso 2.3: Agregar MAX_DOWNLOAD_SIZE a config.py**

En `backend/config.py`, junto a `URL_DOWNLOAD_TIMEOUT` (~línea 155), agregar:

```python
# Límite de descarga de archivos de proveedores (500 MB por defecto)
MAX_DOWNLOAD_SIZE = int(os.environ.get('MAX_DOWNLOAD_SIZE', 500 * 1024 * 1024))
```

- [ ] **Paso 2.4: Actualizar el import en downloaders.py**

En `backend/services/sync/downloaders.py`, en el bloque `from config import (`, agregar `MAX_DOWNLOAD_SIZE`:

```python
from config import (
    FTP_TIMEOUT,
    URL_DOWNLOAD_TIMEOUT,
    URL_REQUEST_TIMEOUT,
    MAX_DOWNLOAD_SIZE,
)
```

- [ ] **Paso 2.5: Reemplazar response.content con streaming limitado**

En `backend/services/sync/downloaders.py`, reemplazar el método `_do_request` dentro de `download_file_from_url_sync` (líneas ~162-170):

Código actual:
```python
    def _do_request(verify_ssl: bool) -> bytes:
        response = session.get(url, timeout=URL_REQUEST_TIMEOUT, stream=True, verify=verify_ssl)
        response.raise_for_status()
        content = response.content
        ssl_note = "" if verify_ssl else " (SSL verification skipped)"
        logger.info(f"URL download completed{ssl_note}: {len(content)} bytes")
        return content
```

Reemplazar por:
```python
    def _do_request(verify_ssl: bool) -> bytes:
        response = session.get(url, timeout=URL_REQUEST_TIMEOUT, stream=True, verify=verify_ssl)
        response.raise_for_status()

        # Verificar Content-Length antes de descargar
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:
            raise ValueError(
                f"Archivo demasiado grande: {int(content_length):,} bytes "
                f"(máximo permitido: {MAX_DOWNLOAD_SIZE:,} bytes / 500 MB)"
            )

        # Descargar en chunks con límite acumulado
        chunks = []
        downloaded = 0
        for chunk in response.iter_content(chunk_size=65536):
            downloaded += len(chunk)
            if downloaded > MAX_DOWNLOAD_SIZE:
                raise ValueError(
                    f"Descarga superó el límite de {MAX_DOWNLOAD_SIZE:,} bytes (500 MB). "
                    f"Verifica el archivo del proveedor."
                )
            chunks.append(chunk)

        content = b"".join(chunks)
        ssl_note = "" if verify_ssl else " (SSL verification skipped)"
        logger.info(f"URL download completed{ssl_note}: {len(content):,} bytes")
        return content
```

- [ ] **Paso 2.6: Ejecutar tests para confirmar que pasan**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestDownloadSizeLimit -v
```

Expected: `3 passed`

- [ ] **Paso 2.7: Commit**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/config.py backend/services/sync/downloaders.py
git commit -m "fix: límite de descarga 500MB — previene OOM por archivos de proveedor excesivamente grandes"
```

---

## Task 3: Fix Upsert Duplicado en product_sync.py

**Problema:** Para productos existentes, se añaden 2 `UpdateOne` al batch en lugar de 1. Esto genera el doble de queries en MongoDB (las 555 queries reportadas).

**Ubicación:** `backend/services/sync/product_sync.py:135-144`

**Archivos:**
- Modify: `backend/services/sync/product_sync.py:135-144`
- Test: `backend/tests/test_sprint5_security.py`

- [ ] **Paso 3.1: Leer el bloque exacto a cambiar**

```bash
grep -n "UpdateOne\|upsert" /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend/services/sync/product_sync.py | head -20
```

Identifica las líneas con el patrón doble `UpdateOne` para productos existentes.

- [ ] **Paso 3.2: Escribir el test que falla**

```python
# Agregar a backend/tests/test_sprint5_security.py

from unittest.mock import AsyncMock, patch, MagicMock
from pymongo import UpdateOne

class TestUpsertDuplicado:
    """Task 3: Fix upsert duplicado en product_sync."""

    @pytest.mark.asyncio
    async def test_producto_existente_genera_un_solo_updateone(self):
        """Producto ya en DB debe generar exactamente 1 UpdateOne, no 2."""
        from backend.services.sync.product_sync import _build_product_ops_for_existing

        existing = MagicMock()
        existing.id = "prod-123"
        existing.stock = 10
        existing.price = 9.99

        product_doc = {"sku": "SKU001", "name": "Test", "stock": 5, "price": 12.0}
        supplier_id = "sup-001"

        ops = _build_product_ops_for_existing(existing, product_doc, supplier_id)

        assert len(ops) == 1, f"Expected 1 UpdateOne, got {len(ops)}"
        assert isinstance(ops[0], UpdateOne)

    @pytest.mark.asyncio
    async def test_producto_nuevo_genera_un_solo_updateone_con_upsert(self):
        """Producto nuevo debe generar exactamente 1 UpdateOne con upsert=True."""
        from backend.services.sync.product_sync import _build_product_ops_for_new

        product_doc = {"sku": "SKU002", "name": "New Product", "stock": 20}
        supplier_id = "sup-001"

        ops = _build_product_ops_for_new(product_doc, supplier_id)

        assert len(ops) == 1
        assert ops[0]._filter == {"supplier_id": supplier_id, "sku": "SKU002"}
        assert ops[0]._doc.get("$setOnInsert") is not None
```

- [ ] **Paso 3.3: Ejecutar para confirmar que falla**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestUpsertDuplicado -v 2>&1 | head -20
```

Expected: `FAILED` — `_build_product_ops_for_existing` no existe

- [ ] **Paso 3.4: Leer el bloque de upsert actual completo**

```bash
sed -n '125,160p' /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend/services/sync/product_sync.py
```

Copia el output completo antes de modificar.

- [ ] **Paso 3.5: Reemplazar los dos UpdateOne por uno solo**

En `backend/services/sync/product_sync.py`, el bloque para productos existentes tiene esta forma:

```python
                product_ops.append(UpdateOne(
                    {"supplier_id": supplier_id, "sku": sku, "id": existing.id},
                    {"$set": product_doc, "$setOnInsert": {"id": existing.id, "created_at": now}},
                    upsert=False
                ))
                product_ops.append(UpdateOne(
                    {"supplier_id": supplier_id, "sku": sku, "id": {"$ne": existing.id}},
                    {"$set": product_doc, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
                    upsert=True
                ))
```

Reemplazar por un solo `UpdateOne` directo por ID:

```python
                product_ops.append(UpdateOne(
                    {"id": existing.id},
                    {"$set": product_doc},
                    upsert=False
                ))
```

**Nota:** El `$setOnInsert` no aplica cuando `upsert=False` porque nunca va a insertar. El documento ya tiene `id` y `created_at` en MongoDB. El `$set` actualiza solo los campos que cambian (stock, precio, nombre, etc.).

- [ ] **Paso 3.6: Ejecutar tests para confirmar que pasan**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestUpsertDuplicado -v
```

Expected: `2 passed`

- [ ] **Paso 3.7: Verificar que los tests existentes de sync siguen pasando**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/ -k "sync or supplier or product" -v 2>&1 | tail -20
```

- [ ] **Paso 3.8: Commit**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/services/sync/product_sync.py
git commit -m "fix: upsert duplicado en product_sync — 1 UpdateOne por producto existente en lugar de 2"
```

---

## Task 4: Límite de Archivos en ZIP

**Problema:** `extract_zip_files` no limita cuántos archivos puede contener el ZIP. Un ZIP con 10.000 archivos puede causar OOM.

**Ubicación:** `backend/services/sync/parsers.py:136-150`

**Archivos:**
- Modify: `backend/config.py` (agregar `MAX_ZIP_FILES`)
- Modify: `backend/services/sync/parsers.py:136`
- Test: `backend/tests/test_sprint5_security.py`

- [ ] **Paso 4.1: Escribir el test que falla**

```python
# Agregar a backend/tests/test_sprint5_security.py

import io
import zipfile

class TestZipFileLimit:
    """Task 4: Límite de archivos en ZIP."""

    def _create_zip_with_n_files(self, n: int) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(n):
                zf.writestr(f"file_{i}.csv", f"col1,col2\nval{i},val{i}")
        return buf.getvalue()

    def test_zip_con_muchos_archivos_lanza_error(self):
        """ZIP con más de MAX_ZIP_FILES archivos debe lanzar ValueError."""
        from backend.services.sync.parsers import extract_zip_files
        big_zip = self._create_zip_with_n_files(150)  # > 100 (límite)
        with pytest.raises(ValueError, match="archivos"):
            extract_zip_files(big_zip)

    def test_zip_con_archivos_dentro_del_limite(self):
        """ZIP con pocos archivos debe extraerse correctamente."""
        from backend.services.sync.parsers import extract_zip_files
        small_zip = self._create_zip_with_n_files(5)
        result = extract_zip_files(small_zip)
        assert len(result) == 5

    def test_zip_exactamente_en_el_limite(self):
        """ZIP con exactamente MAX_ZIP_FILES archivos debe ser aceptado."""
        from backend.services.sync.parsers import extract_zip_files
        zip_at_limit = self._create_zip_with_n_files(100)
        result = extract_zip_files(zip_at_limit)
        assert len(result) == 100
```

- [ ] **Paso 4.2: Ejecutar para confirmar que falla**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestZipFileLimit -v 2>&1 | head -20
```

Expected: `FAILED` — actualmente no lanza ValueError

- [ ] **Paso 4.3: Agregar MAX_ZIP_FILES a config.py**

En `backend/config.py`, junto a `MAX_DOWNLOAD_SIZE`, agregar:

```python
# Límite de archivos dentro de un ZIP de proveedor
MAX_ZIP_FILES = int(os.environ.get('MAX_ZIP_FILES', 100))
```

- [ ] **Paso 4.4: Actualizar import en parsers.py**

En `backend/services/sync/parsers.py`, verificar si hay `from config import` y agregar `MAX_ZIP_FILES`. Si no hay import de config, agregar:

```python
from config import MAX_ZIP_FILES
```

- [ ] **Paso 4.5: Agregar validación en extract_zip_files**

En `backend/services/sync/parsers.py`, modificar `extract_zip_files`:

Código actual:
```python
def extract_zip_files(content: bytes) -> dict:
    """Extract all files from a ZIP archive, returns {filename: bytes}.
    Valida paths para prevenir path traversal (Zip Slip)."""
    result = {}
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
```

Reemplazar por:
```python
def extract_zip_files(content: bytes) -> dict:
    """Extract all files from a ZIP archive, returns {filename: bytes}.
    Valida paths para prevenir path traversal (Zip Slip) y limita número de archivos."""
    result = {}
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        members = [info for info in zf.infolist() if not info.is_dir()]
        if len(members) > MAX_ZIP_FILES:
            raise ValueError(
                f"El ZIP contiene demasiados archivos: {len(members)} "
                f"(máximo permitido: {MAX_ZIP_FILES})"
            )
        for info in zf.infolist():
```

- [ ] **Paso 4.6: Ejecutar tests para confirmar que pasan**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestZipFileLimit -v
```

Expected: `3 passed`

- [ ] **Paso 4.7: Commit**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/config.py backend/services/sync/parsers.py
git commit -m "fix: límite de archivos ZIP — previene OOM con ZIPs de cientos de archivos"
```

---

## Task 5: Reforzar SSRF — Bloquear localhost explícito

**Problema:** `_validate_url_ssrf` usa `ip.is_loopback` pero no bloquea explícitamente el string "localhost" antes de resolver DNS. Un DNS local podría resolver "localhost" a una IP válida antes de la verificación.

**Ubicación:** `backend/services/sync/downloaders.py:133-154`

**Archivos:**
- Modify: `backend/services/sync/downloaders.py:133`
- Test: `backend/tests/test_sprint5_security.py`

- [ ] **Paso 5.1: Leer el bloque _validate_url_ssrf completo**

```bash
sed -n '133,158p' /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend/services/sync/downloaders.py
```

- [ ] **Paso 5.2: Escribir el test que falla**

```python
# Agregar a backend/tests/test_sprint5_security.py

class TestSSRFLocalhost:
    """Task 5: Bloqueo explícito de localhost en validación SSRF."""

    def test_localhost_bloqueado_sin_resolver_dns(self):
        """'localhost' debe bloquearse por string, antes de resolución DNS."""
        from backend.services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError, match="localhost|interna"):
            _validate_url_ssrf("http://localhost/admin")

    def test_localhost_con_puerto_bloqueado(self):
        """'localhost:8080' debe bloquearse."""
        from backend.services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError, match="localhost|interna"):
            _validate_url_ssrf("http://localhost:8080/api")

    def test_127_0_0_1_bloqueado(self):
        """127.0.0.1 debe bloquearse (ya cubierto por is_loopback, verificar)."""
        from backend.services.sync.downloaders import _validate_url_ssrf
        with pytest.raises(ValueError):
            _validate_url_ssrf("http://127.0.0.1/secret")

    def test_url_externa_valida_no_bloqueada(self):
        """URL externa válida no debe lanzar excepción."""
        from backend.services.sync.downloaders import _validate_url_ssrf
        # No debe lanzar — si lanza, el test falla
        try:
            _validate_url_ssrf("http://example.com/catalog.csv")
        except ValueError as e:
            if "interna" in str(e).lower() or "localhost" in str(e).lower():
                pytest.fail(f"URL externa bloqueada incorrectamente: {e}")
```

- [ ] **Paso 5.3: Ejecutar para ver estado actual**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestSSRFLocalhost -v 2>&1 | head -30
```

Observar cuáles pasan y cuáles fallan.

- [ ] **Paso 5.4: Agregar bloqueo por string de hostname al inicio de _validate_url_ssrf**

En `backend/services/sync/downloaders.py`, en la función `_validate_url_ssrf`, añadir al inicio (antes de `parsed = urlparse(url)`):

```python
# Bloqueo explícito de hostnames internos por string — antes de resolver DNS
_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain"}

def _validate_url_ssrf(url: str) -> None:
    """Valida que la URL no apunte a IPs privadas/internas (prevención SSRF)."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https', 'ftp', 'sftp'):
        raise ValueError(f"Esquema de URL no permitido: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL sin hostname válido")

    # Bloqueo explícito de hostnames internos antes de resolución DNS
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(
            f"URL apunta a hostname interno bloqueado ({hostname}). "
            f"No se permiten conexiones a redes internas."
        )

    if '@' in (parsed.netloc.split(':')[0] if ':' in parsed.netloc else parsed.netloc):
        raise ValueError("URLs con @ en el host no están permitidas")
    # ... resto del código existente
```

**IMPORTANTE:** La constante `_BLOCKED_HOSTNAMES` se define fuera de la función (al nivel del módulo), no dentro.

- [ ] **Paso 5.5: Ejecutar tests para confirmar que pasan**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py::TestSSRFLocalhost -v
```

Expected: `4 passed`

- [ ] **Paso 5.6: Ejecutar todos los tests del Sprint 5**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/test_sprint5_security.py -v
```

Expected: todos los tests pasan.

- [ ] **Paso 5.7: Commit**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/services/sync/downloaders.py backend/tests/test_sprint5_security.py
git commit -m "fix: SSRF — bloqueo explícito de localhost por hostname antes de resolución DNS"
```

---

## Task 6: Commit final y resumen

- [ ] **Paso 6.1: Ejecutar suite completa de tests**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend
python -m pytest tests/ -v 2>&1 | tail -30
```

Verificar que los tests existentes siguen pasando (puede haber fallos previos no relacionados).

- [ ] **Paso 6.2: Verificar con grep que no quedan dobles UpdateOne**

```bash
grep -n "upsert=True\|upsert=False" /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend/services/sync/product_sync.py
```

Para productos existentes (bloque `if existing:`) debe aparecer exactamente un `upsert=False`.

- [ ] **Paso 6.3: Verificar que el guard de race condition está en su lugar**

```bash
grep -n "sync_status.*running\|409" /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock/backend/routes/suppliers.py | head -5
```

Expected: ver la línea con `HTTPException(status_code=409, ...)`.

- [ ] **Paso 6.4: Commit de cierre**

```bash
cd /Users/macedicion/Desktop/SyncStock/Codigo/SyncStock
git add backend/tests/test_sprint5_security.py
git commit -m "test: suite de tests Sprint 5 — cobertura de los 5 fixes de seguridad"
```

---

## Referencia

- Auditoría original: `memory/supplier_connections_audit.md`
- Plan de refactor backend (Sprint 6): `/Users/macedicion/.claude/plans/bubbly-snacking-sunbeam.md`
- Archivos clave: `backend/routes/suppliers.py`, `backend/services/sync/`
