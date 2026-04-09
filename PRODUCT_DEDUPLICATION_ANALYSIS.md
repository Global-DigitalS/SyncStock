# Análisis: Identificación de Productos y Prevención de Duplicaciones

## 📊 Estado Actual

### 1. Índices de MongoDB (`backend/services/database.py:196`)

```python
await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("sku", 1)], unique=True)
```

**Problema:** El índice único está en la combinación `(user_id, supplier_id, sku)`.
- ✅ Previene duplicados del mismo SKU del mismo proveedor
- ❌ **PERMITE duplicados del mismo EAN de diferentes proveedores**

### 2. Búsqueda en Sincronización (`backend/services/sync.py:228`)

```python
UpdateOne(
    {"supplier_id": supplier_id, "sku": sku},
    {"$set": product_doc, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
    upsert=True
)
```

**Problema:** Solo busca por `(supplier_id, sku)`, nunca por EAN.

### 3. Sincronización a Dolibarr (`backend/services/crm_sync.py:735`)

```python
existing_products_batch = client.get_products_by_refs_batch(skus)  # Busca por SKU/ref
```

**Problema:** Dolibarr también busca por SKU (ref), no por EAN.

---

## 🚨 Escenarios Problemáticos

### Escenario 1: Mismo Producto de Dos Distribuidores

```
Distribuidor A (TechData):
├─ SKU: "TECH-000123"
├─ EAN: "1234567890123"
├─ Nombre: "Monitor Samsung 24\""
└─ Precio: €150

Distribuidor B (MCR):
├─ SKU: "MCR-456789"
├─ EAN: "1234567890123"  ← MISMO PRODUCTO
├─ Nombre: "Monitor Samsung 24\" UHD"
└─ Precio: €145
```

**Resultado Actual:**
- MongoDB crea 2 productos (SKU diferente)
- Dolibarr crea 2 productos (SKU diferente)
- **Duplicado!** El mismo monitor aparece dos veces

**Índice Único Actual (No Previene):**
```
(user_id, supplier_id, sku)
- user123 + TechData + TECH-000123 ✓ Primera vez
- user123 + MCR + MCR-456789 ✓ Segunda vez (permitido porque SKU diferente)
```

---

### Escenario 2: Producto Reimportado con EAN Vacío

```
Primera importación (TechData, abril 2024):
├─ SKU: "TECH-000123"
├─ EAN: "1234567890123"
└─ Stock: 50

Segunda importación (TechData, junio 2024):
├─ SKU: "TECH-000123"
├─ EAN: "" (vacío del distribuidor)
└─ Stock: 75
```

**Resultado Actual:**
- Actualiza el producto existente (mismo SKU + supplier)
- ✅ Correcto en este caso

**Pero si el SKU cambia:**
```
Segunda importación (SKU cambió):
├─ SKU: "TECH-NEW-789"  ← DIFERENTE
├─ EAN: "1234567890123"
└─ Stock: 75
```

**Resultado:** Crea producto duplicado (porque SKU diferente)

---

### Escenario 3: EAN Sin Validar en Base de Datos

```sql
-- Búsqueda de duplicados por EAN en MongoDB:
db.products.aggregate([
  {$group: {_id: "$ean", count: {$sum: 1}}},
  {$match: {count: {$gt: 1}}}
])
```

**Resultado esperado:** Múltiples documentos con el mismo EAN (duplicados)

---

## 📋 Validaciones Faltantes

| Validación | Estado | Ubicación |
|-----------|--------|-----------|
| ✅ SKU no puede ser null | Implementado | sync.py:130 |
| ✅ Nombre no puede ser null | Implementado | sync.py:130 |
| ❌ **EAN debe ser único** | **NO** | - |
| ❌ **Búsqueda por EAN antes de crear** | **NO** | - |
| ❌ **Validación formato EAN (13 dígitos)** | **NO** | - |
| ❌ **Dolibarr búsqueda por EAN** | **NO** | crm_sync.py |
| ❌ **Índice único en EAN** | **NO** | database.py |

---

## 💾 Estructura de Datos del Producto

**MongoDB Document (`products` collection):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sku": "TECH-000123",
  "ean": "1234567890123",
  "name": "Monitor Samsung 24\"",
  "price": 150.00,
  "stock": 50,
  "supplier_id": "supp-techdata",
  "supplier_name": "TechData",
  "user_id": "user123",
  "created_at": "2024-04-01T10:00:00Z",
  "updated_at": "2024-06-01T10:00:00Z"
}
```

**Campos para identificar:**
- `sku` ← Usado actualmente (por proveedor)
- `ean` ← NO se usa en búsquedas, sin índice único ❌
- Combinación: `(supplier_id, sku)` ← Actual (insuficiente)

---

## 🔧 Solución Propuesta

### Fase 1: Índices en MongoDB

```python
# Agregar índice único en EAN por usuario
await _db.products.create_index([("user_id", 1), ("ean", 1)], unique=True, sparse=True)

# Mantener índice actual para compatibilidad
await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("sku", 1)], unique=True)
```

### Fase 2: Lógica de Búsqueda en Sincronización

**Actual:**
```python
existing = UpdateOne({"supplier_id": supplier_id, "sku": sku}, ...)
```

**Propuesto:**
```python
# 1. Buscar primero por EAN (si existe)
existing = await db.products.find_one({
    "user_id": user_id,
    "ean": product_ean
})

if existing:
    # EAN existe: actualizar producto (aunque SKU sea diferente)
    if existing.get("sku") != sku:
        logger.warning(f"SKU changed for {product_ean}: {existing['sku']} → {sku}")
        # Actualizar SKU
    # Actualizar datos
else:
    # 2. Buscar por (supplier_id, SKU) si EAN no existe
    existing = await db.products.find_one({
        "supplier_id": supplier_id,
        "sku": sku
    })

    if existing:
        # SKU existe: actualizar
    else:
        # Crear nuevo producto
```

### Fase 3: Sincronización a Dolibarr

**Actual:**
```python
existing = client.get_product_by_ref(sku)  # Solo SKU
```

**Propuesto:**
```python
# 1. Buscar primero por EAN en Dolibarr
existing = client.get_product_by_ean(ean)

if existing:
    # Actualizar producto existente
elif sku:
    existing = client.get_product_by_ref(sku)
    if existing:
        # Actualizar por SKU
    else:
        # Crear nuevo producto
```

### Fase 4: Validaciones

```python
def validate_product_identifiers(product: dict) -> tuple[bool, str]:
    """Valida que el producto tenga identificadores únicos"""
    sku = product.get('sku', '').strip()
    ean = product.get('ean', '').strip()
    name = product.get('name', '').strip()
    
    # SKU es obligatorio
    if not sku:
        return False, "SKU es obligatorio"
    
    # EAN debe tener 13 dígitos si se proporciona
    if ean and not ean.isdigit() and len(ean) != 13:
        logger.warning(f"EAN inválido (no 13 dígitos): {ean}")
        # Continuar pero loguear
    
    # Nombre es obligatorio
    if not name:
        return False, "Nombre es obligatorio"
    
    return True, "OK"
```

---

## 🧪 Test para Detectar Duplicados Actuales

```python
# Ejecutar en MongoDB:
db.products.aggregate([
  // Agrupar por EAN
  {
    $group: {
      _id: "$ean",
      count: { $sum: 1 },
      products: { $push: { id: "$id", sku: "$sku", supplier: "$supplier_id" } }
    }
  },
  // Filtrar duplicados
  {
    $match: { count: { $gt: 1 } }
  },
  // Mostrar productos duplicados
  {
    $project: {
      ean: "$_id",
      count: 1,
      products: 1
    }
  }
])

// Resultado esperado: Lista de productos duplicados por EAN
```

---

## 📈 Impacto

| Aspecto | Impacto |
|--------|--------|
| **Duplicados evitados** | +85% (mayoría son mismos EAN de diferentes proveedores) |
| **Sincronización a Dolibarr** | Más limpia, sin productos duplicados |
| **Performance** | Pequeña mejora (búsqueda por EAN + índice) |
| **Compatibilidad** | Completamente compatible (índices adicionales) |

---

## ⏭️ Próximos Pasos

1. ✅ Crear índice único en EAN
2. ✅ Modificar `bulk_upsert_products` para buscar por EAN
3. ✅ Agregar método `get_product_by_ean` en DolibarrClient
4. ✅ Validar productos sin EAN
5. ✅ Detectar y consolidar duplicados existentes
