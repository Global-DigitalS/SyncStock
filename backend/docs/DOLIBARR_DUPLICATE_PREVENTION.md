# Prevención de Duplicados en Sincronización Dolibarr

## Problema
Cuando sincronizas productos a Dolibarr, a veces se crean duplicados:
- Producto A se synca → se crea en Dolibarr
- Segunda sync del mismo producto → se crea OTRO producto igual

## Causa Raíz
La detección de existencia de productos puede fallar por:

1. **Fallo temporal de API**: `get_product_by_ref()` devuelve `None` (timeout/error) en vez de detectar que existe
2. **SKU vacío o null**: El producto en SyncStock tiene SKU null → no se puede buscar
3. **Diferencias en SKU**: SyncStock tiene SKU="ABC", Dolibarr lo guardó como "abc" (case sensitivity)
4. **Productos sin referencia**: El producto en Dolibarr nunca tuvo `ref` asignada

## Soluciones Implementadas

### 1. **Retry de detección**
```python
# En crm_sync.py línea ~232
# Intenta 2 veces buscar el producto antes de asumir que no existe
for attempt in range(2):
    existing = client.get_product_by_ref(sku)
```

**Ventaja**: Si hay un timeout temporal, se reintenta automáticamente

### 2. **Búsqueda por nombre como fallback**
```python
# Si SKU no existe pero el nombre sí:
products_by_name = client.search_products_by_name(product_name)
if products_by_name:
    existing = products_by_name[0]
```

**Ventaja**: Detecta productos incluso si el SKU está vacío o es diferente

### 3. **Validación de SKU antes de syncar**
```python
# Rechaza productos sin SKU
if not sku:
    errors += 1
    continue
```

**Ventaja**: Evita intentos fallidos de búsqueda

### 4. **Logging detallado**
```python
logger.info(f"Stock sync product {product_id}: "
    f"current_in_dolibarr={current_stock}, "
    f"desired={stock}, diff={diff}")
```

**Ventaja**: Fácil debugging en logs si algo sale mal

## Mejores Prácticas para Evitar Duplicados

### Para el usuario (en la UI):

1. **Asegúrate de que todos los productos tengan SKU**
   - Ir a Productos → verificar que todos tienen "SKU" poblado
   - Productos sin SKU no se sincronizarán

2. **Antes de sincronizar a Dolibarr:**
   - Limpia categorías/filtros en SyncStock para que veas TODOS los productos
   - Selecciona solo los productos que quieres syncar
   - Marcalos como "is_selected = true"

3. **Primera sincronización:**
   - Haz una sincronización de prueba con solo 2-3 productos
   - Verifica en Dolibarr que se crearon correctamente
   - Si todo bien, sincroniza el resto

4. **Para sincronizaciones posteriores:**
   - Usa "Actualizar" en vez de "Sincronizar" si quieres actualizar stock/precios
   - No hagas múltiples syncs del mismo catálogo sin esperar a que termine

### Para el equipo de desarrollo:

1. **En el código de detección de existencia:**
   ```python
   existing = client.get_product_by_ref(sku)
   
   # NUNCA hagas esto (asume que None = no existe):
   if existing is None:  # ❌ Peligroso
       create_product()
   
   # Siempre ten fallback:
   if not existing:  # ✓ Más seguro
       # Try alternative detection methods
       existing = search_by_name_or_id()
       if still_not_existing:
           create_product()
   ```

2. **Rate limiting y timeouts:**
   - Los timeouts son frecuentes en Dolibarr si hay muchas instancias/datos
   - Siempre implementa retry logic

3. **Testing:**
   ```bash
   # Test si la detección funciona
   python -c "
   from services.crm_clients import DolibarrClient
   client = DolibarrClient(url, key)
   
   # Test 1: Buscar por SKU que existe
   assert client.get_product_by_ref('SKU-001') is not None
   
   # Test 2: Buscar por SKU que no existe
   assert client.get_product_by_ref('INEXISTENT') is None
   "
   ```

## Métodos Disponibles de Detección

| Método | SKU Required | Confiable | Velocidad |
|--------|-------------|-----------|-----------|
| `get_product_by_ref()` | ✓ | ✓✓ | Rápido |
| `search_products_by_name()` | ✗ | ✓ | Lento (escanea todas) |
| `get_product_by_id()` | ✗ | ✓ | Rápido |

## Debugging: ¿Por qué se creó un duplicado?

1. **Revisar logs:**
   ```bash
   sudo journalctl -u syncstock-backend -f | grep "Product.*created"
   ```

2. **Verificar SKU en SyncStock:**
   ```bash
   # En la BD MongoDB:
   db.products.find({_id: ObjectId("...")}, {sku: 1})
   ```

3. **Verificar en Dolibarr:**
   - Admin → Configuración → Módulos/Aplicaciones → Productos
   - Buscar por SKU en la lista de productos
   - Ver si hay 1 o 2 productos con ese SKU

4. **Si hay duplicados:**
   - En Dolibarr: Eliminar el producto duplicado manualmente
   - En SyncStock: No hay que hacer nada (los duplicados en Dolibarr están separados)

## Monitoreo Continuo

Para evitar futuros duplicados:

```python
# Función de validación en cron job (cada 1 hora):
async def check_duplicates():
    """Check for potential duplicate products"""
    # Find products with same SKU in Dolibarr
    # If found, log warning to admin
    # Alert: "Posibles duplicados detectados en Dolibarr"
```

## Flujo de Sincronización Segura (Recomendado)

```
1. Usuario selecciona productos en SyncStock
2. Sistema verifica:
   - ✓ Todos tienen SKU
   - ✓ SKU no duplicados en SyncStock
   - ✓ Obtiene lista de SKUs de Dolibarr
3. Para cada producto:
   - Busca en Dolibarr por SKU
   - Si encontrado → UPDATE
   - Si NO encontrado → CREATE
4. Después de sync:
   - Verifica cantidad de productos en Dolibarr
   - Si diff inesperado → alerta al usuario
```
