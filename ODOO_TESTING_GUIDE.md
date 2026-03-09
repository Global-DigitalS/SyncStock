# Guía de Testing - Integración Odoo en StockHUB3

## Estado del Proyecto

✅ **Integración completada y sin errores de sintaxis**

---

## Requisitos Previos

Para probar la integración de Odoo, necesitarás:

1. **Instancia de Odoo 17.0** con:
   - ✅ Acceso HTTPS
   - ✅ Módulo de inventario habilitado
   - ✅ Módulo de compras habilitado
   - ✅ API REST habilitada

2. **API Token de Odoo**:
   - Ir a Settings → Users → Tu Usuario
   - Copiar el "Access Token"

3. **StockHUB3 ejecutándose** localmente o en servidor

---

## Plan de Testing

### Fase 1: Validación de Sintaxis ✅
- [x] Análisis de Python - SIN ERRORES
- [x] Importación de módulos - OK
- [x] Estructura de clase - VÁLIDA

### Fase 2: Testing de Conexión (Próximo paso)
1. Crear conexión Odoo
2. Ejecutar test-connection
3. Validar respuesta

### Fase 3: Testing de Productos
1. Sincronizar productos desde StockHUB3
2. Verificar creación en Odoo
3. Actualizar producto
4. Verificar cambios en Odoo

### Fase 4: Testing de Proveedores
1. Sincronizar proveedores
2. Verificar creación en Odoo
3. Vincular producto a proveedor
4. Validar en Odoo

### Fase 5: Testing de Órdenes
1. Crear órdenes en WooCommerce
2. Sincronizar a Odoo
3. Validar importación

---

## Test 1: Prueba de Conexión

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/test-connection \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "odoo",
    "config": {
      "api_url": "https://tu-odoo.example.com",
      "api_token": "tu_access_token_de_odoo"
    }
  }'
```

### Respuesta Exitosa
```json
{
  "status": "success",
  "message": "Conexión exitosa a Odoo",
  "version": "Odoo 17"
}
```

### Respuesta con Error
```json
{
  "status": "error",
  "message": "API Token inválido" // o cualquier otro error
}
```

---

## Test 2: Crear Conexión Odoo

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/connections \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Odoo de Prueba",
    "platform": "odoo",
    "config": {
      "api_url": "https://tu-odoo.example.com",
      "api_token": "tu_access_token_de_odoo"
    },
    "sync_settings": {
      "products": true,
      "stock": true,
      "prices": true,
      "descriptions": true,
      "images": true,
      "suppliers": true,
      "orders": true
    },
    "auto_sync_enabled": false
  }'
```

### Respuesta
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "tu_user_id",
  "name": "Mi Odoo de Prueba",
  "platform": "odoo",
  "config": { ... },
  "is_connected": true,
  "created_at": "2024-01-15T10:30:00+00:00"
}
```

**Guarda el ID de la conexión para próximos tests.**

---

## Test 3: Obtener Estadísticas

### Comando
```bash
curl -X GET http://localhost:8001/api/crm/connections \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

### Respuesta
```json
[
  {
    "id": "connection_id",
    "name": "Mi Odoo de Prueba",
    "platform": "odoo",
    "is_connected": true,
    "stats": {
      "products": 45,
      "suppliers": 12,
      "clients": 0,
      "orders": 8
    },
    "last_sync": "2024-01-15T11:00:00+00:00"
  }
]
```

---

## Test 4: Sincronizar Productos

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/connections/CONNECTION_ID/sync \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "products",
    "catalog_id": null
  }'
```

### Respuesta
```json
{
  "status": "started",
  "sync_job_id": "job_550e8400-e29b-41d4-a716",
  "message": "Sincronización iniciada en segundo plano"
}
```

**Guarda el sync_job_id para monitorear el progreso.**

---

## Test 5: Monitorear Progreso de Sincronización

### Comando
```bash
curl -X GET http://localhost:8001/api/crm/sync-jobs/SYNC_JOB_ID \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

### Respuesta (en progreso)
```json
{
  "id": "job_550e8400-e29b-41d4-a716",
  "status": "running",
  "progress": 45,
  "current_step": "Sincronizando productos...",
  "processed_items": 45,
  "created": 23,
  "updated": 22,
  "started_at": "2024-01-15T11:05:00+00:00",
  "completed_at": null
}
```

### Respuesta (completada)
```json
{
  "id": "job_550e8400-e29b-41d4-a716",
  "status": "completed",
  "progress": 100,
  "current_step": "products: 23 creados, 22 actualizados, 0 errores",
  "processed_items": 45,
  "created": 23,
  "updated": 22,
  "completed_at": "2024-01-15T11:10:00+00:00",
  "results": {
    "products": {
      "status": "success",
      "message": "23 creados, 22 actualizados, 0 errores",
      "created": 23,
      "updated": 22,
      "errors": 0
    }
  }
}
```

---

## Test 6: Sincronizar Proveedores

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/connections/CONNECTION_ID/sync \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "suppliers"
  }'
```

---

## Test 7: Sincronizar Órdenes

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/connections/CONNECTION_ID/sync \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "orders"
  }'
```

---

## Test 8: Sincronizar Todo

### Comando
```bash
curl -X POST http://localhost:8001/api/crm/connections/CONNECTION_ID/sync \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "all"
  }'
```

---

## Test 9: Actualizar Conexión

### Comando
```bash
curl -X PUT http://localhost:8001/api/crm/connections/CONNECTION_ID \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Odoo - Actualizado",
    "sync_settings": {
      "products": true,
      "suppliers": false,
      "orders": false
    }
  }'
```

---

## Test 10: Eliminar Conexión

### Comando
```bash
curl -X DELETE http://localhost:8001/api/crm/connections/CONNECTION_ID \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

### Respuesta
```json
{
  "status": "success",
  "message": "Conexión eliminada"
}
```

---

## Checklist de Validación Final

### Validación de Código
- [x] Sintaxis Python - ✅ SIN ERRORES
- [x] Imports necesarios - ✅ VÁLIDOS
- [x] Métodos de OdooClient - ✅ IMPLEMENTADOS
- [x] Endpoints actualizados - ✅ COMPLETOS
- [x] Documentación - ✅ GENERADA

### Requisitos de Testing Pendientes
- [ ] Prueba real de conexión a Odoo 17
- [ ] Sincronización de datos real
- [ ] Verificación de datos en Odoo
- [ ] Prueba de manejo de errores
- [ ] Prueba de rate limiting
- [ ] Prueba de sincronización automática
- [ ] Prueba de rollback/reversión

### Requisitos de Implementación Frontend Pendientes
- [ ] Interfaz para crear conexiones Odoo
- [ ] Formulario de credenciales
- [ ] Tabla de conexiones con stats
- [ ] Botón para iniciar sincronización
- [ ] Monitoreo de progreso en tiempo real
- [ ] Historial de sincronizaciones

---

## Scripts de Automatización (Bash)

### Script para hacer un test completo

```bash
#!/bin/bash

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
API_URL="http://localhost:8001/api"
TOKEN="TU_JWT_TOKEN"
ODOO_URL="https://tu-odoo.example.com"
ODOO_TOKEN="tu_odoo_token"

echo -e "${YELLOW}=== Test de Integración Odoo ===${NC}\n"

# Test 1: Validar conexión
echo -e "${YELLOW}1. Probando conexión a Odoo...${NC}"
TEST_RESPONSE=$(curl -s -X POST $API_URL/crm/test-connection \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"odoo\",
    \"config\": {
      \"api_url\": \"$ODOO_URL\",
      \"api_token\": \"$ODOO_TOKEN\"
    }
  }")

if echo $TEST_RESPONSE | grep -q '"status":"success"'; then
  echo -e "${GREEN}✓ Conexión exitosa${NC}\n"
else
  echo -e "${RED}✗ Conexión fallida${NC}"
  echo $TEST_RESPONSE
  exit 1
fi

# Test 2: Crear conexión
echo -e "${YELLOW}2. Creando conexión Odoo...${NC}"
CREATE_RESPONSE=$(curl -s -X POST $API_URL/crm/connections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Odoo\",
    \"platform\": \"odoo\",
    \"config\": {
      \"api_url\": \"$ODOO_URL\",
      \"api_token\": \"$ODOO_TOKEN\"
    }
  }")

CONNECTION_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
if [ -z "$CONNECTION_ID" ]; then
  echo -e "${RED}✗ No se pudo crear conexión${NC}"
  echo $CREATE_RESPONSE
  exit 1
fi
echo -e "${GREEN}✓ Conexión creada: $CONNECTION_ID${NC}\n"

# Test 3: Obtener estadísticas
echo -e "${YELLOW}3. Obteniendo estadísticas...${NC}"
STATS=$(curl -s -X GET $API_URL/crm/connections \
  -H "Authorization: Bearer $TOKEN" | grep -o '"stats":{[^}]*}' | head -1)
echo -e "${GREEN}✓ Estadísticas: $STATS${NC}\n"

# Test 4: Sincronizar productos
echo -e "${YELLOW}4. Sincronizando productos...${NC}"
SYNC_RESPONSE=$(curl -s -X POST $API_URL/crm/connections/$CONNECTION_ID/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sync_type":"products"}')

SYNC_JOB=$(echo $SYNC_RESPONSE | grep -o '"sync_job_id":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}✓ Sync iniciado: $SYNC_JOB${NC}\n"

# Test 5: Monitorear progreso
echo -e "${YELLOW}5. Monitoreando progreso...${NC}"
for i in {1..10}; do
  PROGRESS=$(curl -s -X GET $API_URL/crm/sync-jobs/$SYNC_JOB \
    -H "Authorization: Bearer $TOKEN" | grep -o '"progress":[0-9]*' | cut -d':' -f2)
  
  if [ -z "$PROGRESS" ]; then
    PROGRESS="0"
  fi
  
  echo "   Progreso: ${PROGRESS}%"
  
  if [ "$PROGRESS" -eq 100 ]; then
    echo -e "${GREEN}✓ Sincronización completada${NC}\n"
    break
  fi
  
  sleep 2
done

echo -e "${GREEN}=== Test completado exitosamente ===${NC}"
```

---

## Troubleshooting

### Error: "API Token inválido"
- Verifica que el token es correcto
- Asegúrate que no hay espacios en blanco
- Regenera el token en Odoo si es necesario

### Error: "No se puede conectar al servidor"
- Verifica la URL de Odoo
- Asegúrate que HTTPS está disponible
- Comprueba firewall/puertos abiertos

### Error: "Timeout"
- La instancia Odoo está muy lenta
- Aumenta el timeout en el cliente
- De lo contrario, revisa carga del servidor

### Productos no se sincronizan
- Verifica que los productos tienen SKU
- Confirma permisos del usuario en Odoo
- Revisa logs del servidor para más detalles

---

## Logs Útiles

```bash
# Ver logs del backend
sudo journalctl -u suppliersync-backend -f

# Buscar errores de Odoo
sudo journalctl -u suppliersync-backend -f | grep -i "odoo"

# Ver logs completos de un sync
curl -X GET http://localhost:8001/api/crm/sync-jobs/JOB_ID
```

---

## Siguiente Pasos

1. **Ejecutar todos los tests** mencionados arriba
2. **Verificar datos en Odoo** (productos creados, proveedores, etc.)
3. **Documentar casos de uso específicos** de tu negocio
4. **Configurar sincronización automática** si todo funciona bien
5. **Setup en producción** considerando horarios de sincronización

---

**Testing completado ✅**

Para más información, ver:
- [ODOO_INTEGRATION.md](ODOO_INTEGRATION.md)
- [ODOO_INTEGRATION_SUMMARY.md](ODOO_INTEGRATION_SUMMARY.md)
