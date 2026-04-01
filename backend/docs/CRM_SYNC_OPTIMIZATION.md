# Optimización de Sincronización CRM - Análisis y Propuestas

## 🔴 Problemas Actuales (Rendimiento)

### 1. **Sincronización Secuencial (Producto por Producto)**
**Problema:**
- Procesa 1 producto a la vez
- 100 productos = 100 llamadas API secuenciales
- Tiempo total = Suma de todos los timeouts

```python
# ❌ ACTUAL - Secuencial
for product in products:  # 100 productos
    existing = client.get_product_by_ref(sku)  # 1 API call
    if existing:
        client.update_product(...)  # 1 API call
    else:
        client.create_product(...)  # 1 API call
    # Total: 200-300 API calls secuenciales
```

**Impacto:**
- Sincronizar 1000 productos = 30-60 minutos (con rate limit)
- Cualquier timeout retrasa TODOS los productos posteriores

---

### 2. **Queries de BD Ineficientes**
**Problema:**
```python
# ❌ Para CADA producto:
suppliers = await db.suppliers.find(...)  # Query repetida 100 veces
margin_rules = await db.catalog_margin_rules.find(...)  # Query repetida 100 veces
catalog_items_map = {}  # Se construye manualmente, sin índices
```

**Impacto:**
- 100 productos × 2 queries = 200 queries extras
- Sin aprovechar índices de MongoDB

---

### 3. **Sin Batch de Detección**
**Problema:**
```python
# ❌ ACTUAL
for sku in skus:  # 100 iteraciones
    product = client.get_product_by_ref(sku)  # 1 API call
```

**Métodos batch existentes NO se usan:**
```python
# Dolibarr client tiene esto pero no lo usamos:
def get_products_by_refs_batch(self, refs: List[str])
```

**Impacto:**
- 100 productos = 100 calls
- Con batch = 1-2 calls

---

### 4. **Sin Caché de Datos CRM**
**Problema:**
- No se cachean productos obtenidos de Dolibarr
- Si el usuario synca 2 catálogos el mismo día:
  - Catálogo 1: obtiene producto X de Dolibarr
  - Catálogo 2: vuelve a obtener producto X de Dolibarr

**Impacto:**
- Datos CRM más lentos para sincronizaciones repetidas

---

### 5. **Sin Compresión de Cambios**
**Problema:**
```python
# Si un producto solo cambió stock, actualizamos TODO:
client.update_product(...)  # Envía: nombre, precio, descripción, etc.
client.update_stock(...)    # Envía: solo stock
```

**Impacto:**
- Bandwidth desperdiciado
- Más datos en logs
- Más lento en conexiones lentas

---

### 6. **Sin Control de Rate Limiting Global**
**Problema:**
- Cada cliente CRM (Dolibarr, Odoo) tiene su propio rate limit local
- No hay coordinación global entre syncs paralelos

```python
# Dolibarr:
self.min_delay = 0.1  # 100ms entre requests

# Odoo:
self.min_delay = 0.1  # 100ms entre requests

# Si sincronizas Dolibarr + Odoo en paralelo = 200 requests/segundo
```

**Impacto:**
- Puede exceder límites reales del CRM
- Rate limit errors no capturados

---

## 💡 Optimizaciones Propuestas

### ✅ **NIVEL 1: Batch Processing (Máximo Impacto)**

#### 1.1 Usar `get_products_by_refs_batch()` en Dolibarr
```python
# ✓ OPTIMIZADO - Batch
skus = [p.get("sku") for p in products]
existing_products_map = client.get_products_by_refs_batch(skus)
# 1 pass por 100 productos

# Ahora solo 1 loop:
for product in products:
    existing = existing_products_map.get(product.get("sku"))
```

**Ganancia:**
- 100 products: 100 → 1 API call
- Speedup: **50-100x más rápido**

#### 1.2 Batch Create/Update
```python
# Crear en chunks
chunk_size = 10
for i in range(0, len(products), chunk_size):
    chunk = products[i:i+chunk_size]
    tasks = [
        client.create_product_async(p)  # Llamadas paralelas
        for p in chunk if not existing_products_map.get(p.get("sku"))
    ]
    results = await asyncio.gather(*tasks)
```

**Ganancia:**
- Parallelismo: 10 productos simultáneamente
- Speedup: **10x más rápido**

---

### ✅ **NIVEL 2: Caché en Memoria**

```python
# SyncCache con TTL
class SyncCache:
    def __init__(self, ttl_minutes=30):
        self.cache = {}
        self.ttl = ttl_minutes * 60
        self.timestamps = {}
    
    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = time.time()

# Uso:
cache = SyncCache(ttl_minutes=30)
existing = cache.get(sku) or client.get_product_by_ref(sku)
cache.set(sku, existing)
```

**Ganancia:**
- Si synca 2 catálogos el mismo día con productos comunes: **80% menos API calls**

---

### ✅ **NIVEL 3: Cambios Diferenciales**

```python
# Solo enviar campos que cambiaron
def build_update_payload(product_local, product_crm):
    """Build update payload with only changed fields"""
    payload = {}
    
    fields = ["name", "price", "cost_price", "description"]
    for field in fields:
        local_val = product_local.get(field)
        crm_val = product_crm.get(field)
        if local_val != crm_val:
            payload[field] = local_val  # Only add if different
    
    return payload if payload else None  # None = no changes needed

# Uso:
update_payload = build_update_payload(local_product, crm_product)
if update_payload:
    client.update_product(product_id, update_payload)
else:
    logger.info(f"Product {sku} unchanged, skipping update")
```

**Ganancia:**
- Menos datos transmitidos: **30-50% menos bandwidth**
- Más rapido: **2-3x en conexiones lentas**

---

### ✅ **NIVEL 4: Carga Lazy de Datos BD**

```python
# ❌ ANTES - Carga todo upfront
suppliers = await db.suppliers.find({...}).to_list(1000)  # Antes del loop
suppliers_map = {s["id"]: s for s in suppliers}

margin_rules = await db.catalog_margin_rules.find({...}).to_list(100)

for product in products:
    supplier = suppliers_map.get(product["supplier_id"])  # Lookup rápido
```

```python
# ✓ OPTIMIZADO - Carga lazy con caché
supplier_cache = {}
async def get_supplier(supplier_id):
    if supplier_id not in supplier_cache:
        supplier_cache[supplier_id] = await db.suppliers.find_one({"id": supplier_id})
    return supplier_cache[supplier_id]

for product in products:
    supplier = await get_supplier(product["supplier_id"])
```

**Ganancia:**
- Si no todos los productos usan todos los suppliers: **50-80% menos queries**

---

### ✅ **NIVEL 5: Procesamiento Paralelo por Tipo**

```python
# Separar en grupos
to_create = [p for p in products if not existing_map.get(p.get("sku"))]
to_update = [p for p in products if existing_map.get(p.get("sku"))]

# Procesar en paralelo
create_tasks = [create_product_async(p) for p in to_create]
update_tasks = [update_product_async(p) for p in to_update]

results_create = await asyncio.gather(*create_tasks)
results_update = await asyncio.gather(*update_tasks)
```

**Ganancia:**
- Creates y updates sin competencia de resources: **2-3x más rápido**

---

### ✅ **NIVEL 6: Rate Limiting Global**

```python
from asyncio import Semaphore

class GlobalRateLimiter:
    def __init__(self, max_concurrent=5, min_delay=0.1):
        self.semaphore = Semaphore(max_concurrent)  # Max 5 calls simultáneas
        self.min_delay = min_delay
        self.last_call = 0
    
    async def acquire(self):
        async with self.semaphore:
            elapsed = time.time() - self.last_call
            if elapsed < self.min_delay:
                await asyncio.sleep(self.min_delay - elapsed)
            self.last_call = time.time()

# Uso:
limiter = GlobalRateLimiter(max_concurrent=5, min_delay=0.05)
await limiter.acquire()
result = await client.update_product(...)
```

**Ganancia:**
- Control global de rate limits: **Evita excepciones 429 (Too Many Requests)**

---

## 📊 Ganancia de Rendimiento Teórico

Sincronizar **1000 productos** desde SyncStock a Dolibarr:

| Método | Tiempo | Mejora | API Calls |
|--------|--------|--------|-----------|
| **ACTUAL (Secuencial)** | **60 min** | Base | 1,500-2,000 |
| + Batch detection | 45 min | **1.3x** | 500-1,000 |
| + Parallelismo (10x) | 5 min | **12x** | 500-1,000 |
| + Cambios diferenciales | 3 min | **20x** | 300-500 |
| + Caché | 2 min | **30x** | 100-200 |
| **OPTIMIZADO TOTAL** | **2 min** | **30x** | ~150 |

---

## 🚀 Plan de Implementación Recomendado

### **Fase 1 (Rápido) - 2 horas**
- [ ] Implementar batch detection (1.1)
- [ ] Usar `get_products_by_refs_batch()` existente
- **Resultado:** 50x en detección

### **Fase 2 (Medio) - 4 horas**
- [ ] Parallelismo por chunks (1.2)
- [ ] AsyncIO para crear/actualizar en paralelo
- **Resultado:** 10x más en procesamiento

### **Fase 3 (Completo) - 6 horas**
- [ ] Caché en memoria (2)
- [ ] Cambios diferenciales (3)
- [ ] Rate limiting global (6)
- **Resultado:** 30x total

---

## Código Prototipo: Sync Optimizado

```python
async def sync_products_to_dolibarr_optimized(
    client: DolibarrClient,
    user_id: str,
    sync_settings: dict = None,
    sync_job_id: str = None
) -> Dict:
    """Optimized product sync using batch operations and parallelism"""
    
    products = await db.products.find({"user_id": user_id}).to_list(10000)
    
    # Phase 1: Batch detection
    skus = [p.get("sku") for p in products if p.get("sku")]
    existing_map = client.get_products_by_refs_batch(skus)  # 1 API call!
    
    # Phase 2: Separate into groups
    to_create = [p for p in products if p.get("sku") and p.get("sku") not in existing_map]
    to_update = [p for p in products if p.get("sku") and p.get("sku") in existing_map]
    
    # Phase 3: Process in parallel chunks
    limiter = GlobalRateLimiter(max_concurrent=5)
    
    async def create_with_limiter(product):
        await limiter.acquire()
        return await client.create_product_async(product)
    
    async def update_with_limiter(product):
        await limiter.acquire()
        payload = build_update_payload(product, existing_map[product.get("sku")])
        if payload:
            return await client.update_product_async(product.get("id"), payload)
    
    create_tasks = [create_with_limiter(p) for p in to_create]
    update_tasks = [update_with_limiter(p) for p in to_update]
    
    results = await asyncio.gather(*create_tasks, *update_tasks, return_exceptions=True)
    
    # Phase 4: Collect results
    created = sum(1 for r in results[:len(create_tasks)] if r.get("status") == "success")
    updated = sum(1 for r in results[len(create_tasks):] if r.get("status") == "success")
    
    return {
        "status": "success",
        "created": created,
        "updated": updated,
        "api_calls": len(skus) + len(to_create) + len(to_update)  # Mucho menos
    }
```

---

## 🔍 Métricas a Monitorear

Después de optimizar, registra:

```python
logger.info(f"Sync completed in {time.time() - start}s")
logger.info(f"Products: {created} created, {updated} updated, {errors} errors")
logger.info(f"API calls: {api_call_count} (optimized from est. {products_count * 3})")
logger.info(f"Rate: {products_count / (time.time() - start):.1f} products/sec")
```

Target después de optimización: **50+ products/segundo**

