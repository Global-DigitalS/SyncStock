# Revisión de Seguridad - Nuevas Áreas
## Frontend React | Nginx | Plesk | SSL/TLS | Logging

**Fecha:** 27 de marzo de 2026
**Rama:** `claude/code-review-security-JitQz`
**Alcance:** Frontend Security, Nginx Configuration, Plesk Hardening, SSL/TLS, Logging

---

## RESUMEN EJECUTIVO

| Severidad | Categoría | Cantidad | Estado |
|-----------|-----------|----------|--------|
| 🔴 CRÍTICA | Frontend XSS | 1 | ❌ FALTANTE |
| 🔴 CRÍTICA | Validación Inputs | 6 formularios | ❌ FALTANTE |
| 🟠 ALTA | localStorage Token | 1 | ❌ FALTANTE |
| 🟡 MEDIA | Infrastructure | 5 | ⚠️ INCOMPLETO |

**Total de problemas encontrados:** 13
**Esfuerzo estimado:** 26-45 horas

---

## AREA 1: SEGURIDAD DEL FRONTEND REACT (20-32 horas)

### 1.1 VALIDACIÓN DE INPUTS - ❌ CRÍTICO

**Problema:** Librerías Zod y react-hook-form instaladas pero NO utilizadas

**Formularios afectados:**
- `Login.jsx` - Validación manual solo `trim()`
- `Register.jsx` - Validación manual incompleta
- `Suppliers.jsx` - Validación mínima
- `Catalogs.jsx` - SIN validación
- `Marketplaces.jsx` - SIN validación
- `AdminEmailTemplates.jsx` - SIN validación

**Esfuerzo:** 16-24 horas
**Prioridad:** URGENTE

---

### 1.2 PROTECCIÓN XSS - ❌ CRÍTICO

**Ubicación:** `/frontend/src/hooks/useGoogleScripts.js` línea 48

**Vulnerabilidad:**
```javascript
gtmNoscript.innerHTML = `<iframe src="...?id=${gtmId}">`;
// gtmId viene del servidor sin validar
```

**Riesgo:** Si `config.tag_manager_container_id` está contaminado, se ejecuta código malicioso

**Esfuerzo:** 2-4 horas
**Prioridad:** URGENTE

---

### 1.3 localStorage Token - ⚠️ ALTA

**Ubicación:** `/frontend/src/pages/Register.jsx` línea 220

**Vulnerabilidad:**
```javascript
localStorage.setItem("pending_token", token);  // ❌ Inseguro
```

**Riesgo:** localStorage es vulnerable a XSS

**Esfuerzo:** < 1 hora
**Prioridad:** URGENTE

---

### 1.4 PROTECCIÓN CSRF - ✅ CORRECTO

Implementado correctamente en `/frontend/src/App.js`
- ✓ withCredentials: true
- ✓ X-CSRF-Token enviado en todas las mutaciones
- ✓ Double-submit cookie pattern

---

## AREA 2: NGINX CONFIGURATION (3-5 horas)

### 2.1 SECURITY HEADERS - ✅ EXCELENTE

**Implementados:**
- ✓ HSTS (2 años + preload)
- ✓ CSP completa y restrictiva
- ✓ X-Frame-Options: DENY
- ✓ X-Content-Type-Options: nosniff
- ✓ Permissions-Policy (hardware deshabilitado)

---

### 2.2 WebSocket TIMEOUTS - ⚠️ PROBLEMA

**Ubicación:** `/scripts/nginx_config_plesk.conf` líneas 62-68

**Problema:** Timeouts muy largos (7 días)
```nginx
proxy_connect_timeout 7d;
proxy_send_timeout 7d;
proxy_read_timeout 7d;
```

**Riesgo:** Conexiones fantasma no se detectan

**Solución:** Implementar heartbeat en FastAPI + reducir a 300s

**Esfuerzo:** 1-2 horas
**Prioridad:** IMPORTANTE

---

### 2.3 RATE LIMITING - ❌ FALTANTE

**Problema:** NO hay rate limiting en Nginx (solo en FastAPI)

**Solución:** Agregar `limit_req_zone` en Nginx

**Esfuerzo:** < 1 hora
**Prioridad:** IMPORTANTE

---

### 2.4 Static Files Cache - ✅ CORRECTO

- ✓ Expires 1 año
- ✓ Cache-Control: immutable
- ✓ CRA content-hash permite cache agresivo

---

## AREA 3: SSL/TLS CERTIFICATES (< 1 hora)

### 3.1 CERTIFICADOS - ✅ CORRECTO

- ✓ Let's Encrypt via certbot
- ✓ Validez 90 días (requiere renovación)

**Acción:** Verificar que `systemctl list-timers` muestre certbot.timer activo

---

### 3.2 CIPHER SUITES - ⚠️ NO CONFIGURADOS

**Problema:** Nginx usa ciphers por defecto

**Solución:** Configurar ciphers seguros (TLS 1.2+)

**Esfuerzo:** < 1 hora
**Prioridad:** IMPORTANTE

---

## AREA 4: PLESK HARDENING (1-2 horas)

### 4.1 PERMISOS DE ARCHIVO - ⚠️ NO DOCUMENTADO

**Problema:** Sin especificación de permisos correctos

**Solución necesaria:**
```bash
chmod 600 /etc/syncstock/config.json
chmod 700 /etc/syncstock/
find $APP_DIR -type d -exec chmod 755 {} \;
find $APP_DIR -type f -exec chmod 644 {} \;
```

**Esfuerzo:** 1-2 horas
**Prioridad:** IMPORTANTE

---

## AREA 5: LOGGING & MONITORING (2-6 horas)

### 5.1 STRUCTURED LOGGING - ✅ CORRECTO

- ✓ JSON format
- ✓ Incluye method, path, status, duration, IP
- ✓ Diferencia errores 4xx vs 5xx
- ✓ Skip health checks

---

### 5.2 SIN DATOS SENSIBLES - ✅ CORRECTO

- ✓ No se loguea request body
- ✓ No se loguea headers sensibles
- ✓ No se loguea response body

---

### 5.3 LOG ROTATION - ❌ FALTANTE

**Problema:** No documentada la rotación de logs

**Solución:** `/etc/logrotate.d/syncstock`

**Esfuerzo:** < 1 hora
**Prioridad:** IMPORTANTE

---

### 5.4 MONITOREO CENTRALIZADO - ❌ FALTANTE

**Opción recomendada:** Sentry o DataDog

**Esfuerzo:** 2-4 horas
**Prioridad:** A MEDIANO PLAZO

---

## TOP 10 VULNERABILIDADES

1. 🔴 **innerHTML en useGoogleScripts.js** - XSS CRÍTICO
2. 🔴 **NO usar Zod para validación** - 6 formularios
3. 🟠 **Token en localStorage** - Register.jsx
4. 🟡 **WebSocket timeout 7 días** - Nginx
5. 🟡 **NO hay rate limiting Nginx** - DDoS
6. 🟡 **Ciphers no optimizados** - SSL/TLS
7. 🟡 **Permisos archivos** - Plesk
8. 🟡 **Log rotation no configurada** - Logging
9. 🟡 **SIN monitoreo centralizado** - Observabilidad
10. 🟢 **URLs imagen no validadas** - Frontend

---

## PLAN DE ACCIÓN RECOMENDADO

### URGENTE (Esta semana)
- [ ] Sanitizar innerHTML en useGoogleScripts.js (2-4h)
- [ ] Remover localStorage token Register.jsx (<1h)
- [ ] Comenzar migración Zod (formularios críticos: Login, Register) (4-6h)

### IMPORTANTE (Este sprint)
- [ ] WebSocket heartbeat timeout (1-2h)
- [ ] Rate limiting Nginx (<1h)
- [ ] SSL/TLS cipher configuration (<1h)
- [ ] Permisos archivo Plesk (1-2h)

### A MEDIANO PLAZO (Próximas 2 semanas)
- [ ] Migración completa a Zod (16-24h)
- [ ] Log rotation (<1h)
- [ ] Integración Sentry (2-4h)
- [ ] Validar URLs imagen (<1h)

---

## ESTIMACIÓN TOTAL POR CATEGORÍA

| Categoría | Horas |
|-----------|-------|
| Frontend Security | 20-32h |
| Nginx/Infrastructure | 3-5h |
| Plesk Hardening | 1-2h |
| Logging & Monitoring | 2-6h |
| **TOTAL** | **26-45h** |

---

## CÓDIGO RECOMENDADO - MUESTRAS RÁPIDAS

### Fix 1: Sanitizar XSS en useGoogleScripts.js
```javascript
import DOMPurify from "dompurify";

const validateGTMId = (id) => {
  const gtmRegex = /^GTM-[A-Z0-9]{6,}$/;
  return gtmRegex.test(id) ? id : null;
};

const validGtmId = validateGTMId(config.tag_manager_container_id);
if (!validGtmId) return;

const iframeHtml = `<iframe src="https://www.googletagmanager...?id=${validGtmId}">`;
gtmNoscript.innerHTML = DOMPurify.sanitize(iframeHtml, {
  ALLOWED_TAGS: ["iframe"],
  ALLOWED_ATTR: ["src", "height", "width"]
});
```

### Fix 2: Validación con Zod (ejemplo)
```javascript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const supplierSchema = z.object({
  name: z.string().min(2).max(100),
  ftp_host: z.string().ip().or(z.string().hostname()),
  ftp_port: z.number().min(1).max(65535),
  ftp_user: z.string().min(1),
});

const form = useForm({ resolver: zodResolver(supplierSchema) });
```

### Fix 3: Remover localStorage
```javascript
// ANTES: localStorage.setItem("pending_token", token);
// DESPUÉS: sessionStorage (temporal)
sessionStorage.setItem("pending_token", token);
```

### Fix 4: Nginx Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/auth/login {
    limit_req zone=login burst=2 nodelay;
    proxy_pass http://syncstock_backend;
}
```

---

**Generado:** 27 de marzo de 2026
**Rama:** `claude/code-review-security-JitQz`
