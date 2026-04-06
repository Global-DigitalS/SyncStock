# Plan de Acción - Vulnerabilidades de Seguridad
## SyncStock Security Fixes - Ordenadas por Criticidad

**Fecha:** 27 de marzo de 2026
**Total de Tareas:** 10
**Esfuerzo Total:** 26-45 horas
**Rama de Trabajo:** `claude/code-review-security-JitQz`

---

## 📊 RESUMEN DE PRIORIDADES

| Prioridad | Cantidad | Tareas | Esfuerzo |
|-----------|----------|--------|----------|
| 🔴 CRÍTICA | 2 | FIX 1, FIX 2 | 18-28h |
| 🟠 ALTA | 1 | FIX 3 | <1h |
| 🟡 MEDIA | 5 | FIX 4-8 | 4-11h |
| 🟢 BAJA | 2 | FIX 9-10 | 2-6h |

---

## 🔴 FIX 1: SANITIZAR XSS EN useGoogleScripts.js (CRÍTICO)

**Ubicación:** `/frontend/src/hooks/useGoogleScripts.js` línea 48
**Severidad:** 🔴 CRÍTICA - XSS RCE (Remote Code Execution)
**Esfuerzo:** 2-4 horas
**Bloqueador:** SÍ - Impide merge a master
**Impacto:** Todos los usuarios

### ¿Por qué es crítico?
Si `config.tag_manager_container_id` está contaminado (inyección en BD), se ejecutará código malicioso en el navegador de TODOS los usuarios.

### Código Actual (Vulnerable)
```javascript
// LÍNEA 48 - innerHTML vulnerable
gtmNoscript.innerHTML = `<iframe src="https://www.googletagmanager.com/ns.html?id=${gtmId}" ...`;

// LÍNEAS 45, 60, 73, 77 - Inyección de scripts
gtmScript.textContent = `(function(w,d,s,l,i){...gtm.js?id='+i+dl;...})(window,document,'script','dataLayer','${gtmId}');`;
```

### Pasos Detallados

#### PASO 1: Instalar DOMPurify (10 min)
```bash
cd /home/user/SyncStock/frontend
npm install dompurify
npm install --save-dev @types/dompurify  # Para TypeScript
```

#### PASO 2: Crear función de validación GTM (15 min)

**Archivo:** `/frontend/src/hooks/useGoogleScripts.js`

```javascript
/**
 * Valida que el ID de Google Tag Manager tenga el formato correcto
 * @param {string} id - ID a validar (debe ser GTM-XXXXXX)
 * @returns {string|null} - ID válido o null
 */
const validateGTMId = (id) => {
  // Google Tag Manager IDs tienen formato GTM-XXXXXXXX
  const gtmRegex = /^GTM-[A-Z0-9]{6,}$/;

  if (typeof id !== 'string') {
    console.error('GTM ID must be a string');
    return null;
  }

  if (!gtmRegex.test(id)) {
    console.error(`Invalid GTM ID format: ${id}`);
    return null;
  }

  return id;
};

/**
 * Escapa caracteres especiales para usar en atributos HTML
 * @param {string} str - String a escapar
 * @returns {string} - String escapado
 */
const escapeHtmlAttribute = (str) => {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};
```

#### PASO 3: Actualizar función que inserta GTM (30 min)

**Antes:**
```javascript
const insertGTM = (gtmId) => {
  // ... setup ...

  gtmNoscript.innerHTML = `<iframe src="https://www.googletagmanager.com/ns.html?id=${gtmId}" ...`;
  gtmScript.textContent = `...gtm.js?id='+i+dl;...})(window,document,'script','dataLayer','${gtmId}');`;

  // ... rest ...
};
```

**Después:**
```javascript
import DOMPurify from 'dompurify';

const insertGTM = (gtmId) => {
  // PASO 1: Validar GTM ID
  const validGtmId = validateGTMId(gtmId);

  if (!validGtmId) {
    console.error('GTM configuration is invalid. Skipping Google Tag Manager initialization.');
    return;  // Salir sin insertar nada
  }

  // PASO 2: Escapar ID para usarlo en HTML
  const escapedGtmId = escapeHtmlAttribute(validGtmId);

  // PASO 3: Crear HTML de iframe y sanitizarlo
  const iframeHtml = `<iframe src="https://www.googletagmanager.com/ns.html?id=${escapedGtmId}"
    height="0" width="0" style="display:none;visibility:hidden" id="tag-manager"></iframe>`;

  // PASO 4: Usar DOMPurify para sanitizar (doble protección)
  const sanitizedHtml = DOMPurify.sanitize(iframeHtml, {
    ALLOWED_TAGS: ['iframe'],
    ALLOWED_ATTR: ['src', 'height', 'width', 'style', 'id'],
    // Bloquear cualquier atributo que no esté en la lista
    FORCE_BODY: false,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false,
  });

  // PASO 5: Insertar de forma segura
  const noscriptDiv = document.querySelector('noscript');
  if (noscriptDiv) {
    // Usar innerHTML ahora es más seguro porque DOMPurify sanitizó
    noscriptDiv.innerHTML = sanitizedHtml;
  }

  // PASO 6: Para el script tag, usar un enfoque más seguro
  const scriptTag = document.querySelector('script[data-gtm-setup]');
  if (scriptTag) {
    // Usar template literal pero con validación de GTM ID
    // El ID fue validado arriba, así que es seguro usarlo aquí
    const scriptContent = `
      (function(w,d,s,l,i){
        w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
        var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';
        j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;
        f.parentNode.insertBefore(j,f);
      })(window,document,'script','dataLayer','${escapedGtmId}');
    `;

    // Reemplazar contenido del script (es más seguro que innerHTML)
    scriptTag.textContent = scriptContent;
  }
};
```

#### PASO 4: Configurar DOMPurify (10 min)

**Archivo:** `/frontend/src/config/dompurify.config.js` (crear nuevo)

```javascript
import DOMPurify from 'dompurify';

/**
 * Configuración global de DOMPurify para SyncStock
 */
DOMPurify.setConfig({
  // No permitir nada por defecto
  ALLOWED_TAGS: [],
  ALLOWED_ATTR: [],

  // Estas configuraciones se pueden sobrescribir por contexto
  RETURN_DOM: false,
  RETURN_DOM_FRAGMENT: false,
  RETURN_DOM_IMPORT: false,

  // Bloquear datos sensibles
  FORCE_BODY: false,
});

// Agregar handlers custom para casos especiales
DOMPurify.addHook('beforeSanitizeElements', (node) => {
  // Log si se encuentran intentos de XSS
  if (node.innerHTML && (node.innerHTML.includes('script') || node.innerHTML.includes('onerror'))) {
    console.warn('Potential XSS attempt blocked:', node);
  }
});

export default DOMPurify;
```

#### PASO 5: Testing (30 min)

**Archivo:** `/frontend/src/hooks/__tests__/useGoogleScripts.test.js` (crear nuevo)

```javascript
import { validateGTMId, escapeHtmlAttribute } from '../useGoogleScripts';
import DOMPurify from 'dompurify';

describe('Google Tag Manager Security', () => {

  describe('validateGTMId', () => {
    it('debe aceptar GTM ID válido', () => {
      expect(validateGTMId('GTM-XXXXXX')).toBe('GTM-XXXXXX');
      expect(validateGTMId('GTM-ABC123')).toBe('GTM-ABC123');
    });

    it('debe rechazar GTM ID inválido', () => {
      expect(validateGTMId('INVALID-ID')).toBeNull();
      expect(validateGTMId('gtm-lowercase')).toBeNull();  // Minúsculas no permitidas
      expect(validateGTMId('GTM-')).toBeNull();  // Sin sufijo
      expect(validateGTMId('')).toBeNull();  // Vacío
    });

    it('debe rechazar inyección XSS', () => {
      expect(validateGTMId('GTM-ABC<script>alert(1)</script>')).toBeNull();
      expect(validateGTMId('GTM-ABC" onload="alert(1)')).toBeNull();
    });

    it('debe rechazar tipos incorrectos', () => {
      expect(validateGTMId(123)).toBeNull();
      expect(validateGTMId(null)).toBeNull();
      expect(validateGTMId(undefined)).toBeNull();
    });
  });

  describe('escapeHtmlAttribute', () => {
    it('debe escapar caracteres especiales', () => {
      expect(escapeHtmlAttribute('<')).toBe('&lt;');
      expect(escapeHtmlAttribute('>')).toBe('&gt;');
      expect(escapeHtmlAttribute('"')).toBe('&quot;');
      expect(escapeHtmlAttribute('&')).toBe('&amp;');
    });

    it('debe prevenir inyección en atributos', () => {
      const input = 'value" onload="alert(1)';
      const output = escapeHtmlAttribute(input);
      expect(output).not.toContain('onload=');
      expect(output).toContain('&quot;');
    });
  });

  describe('DOMPurify sanitization', () => {
    it('debe sanitizar iframe malicioso', () => {
      const maliciousHtml = `<iframe src="javascript:alert(1)"></iframe>`;
      const sanitized = DOMPurify.sanitize(maliciousHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src']
      });

      expect(sanitized).not.toContain('javascript:');
    });

    it('debe permitir iframe legítimo', () => {
      const validHtml = `<iframe src="https://www.googletagmanager.com/ns.html?id=GTM-ABC123"></iframe>`;
      const sanitized = DOMPurify.sanitize(validHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src']
      });

      expect(sanitized).toContain('iframe');
      expect(sanitized).toContain('googletagmanager.com');
    });
  });
});
```

**Ejecutar tests:**
```bash
cd /frontend
npm test -- useGoogleScripts.test.js
```

#### PASO 6: Verificación en Desarrollo (15 min)

```bash
# 1. Iniciar dev server
npm start

# 2. Abrir DevTools (F12) y verificar:
# - No hay errores en Console
# - GTM se inicializa correctamente
# - En Network, ver que se carga gtm.js

# 3. Inspeccionar noscript tag
# - Debe contener iframe válido
# - Sin caracteres especiales sin escapar

# 4. Probar con ID malicioso (en DevTools Console)
# - Cambiar window.__GTM_ID__ = 'GTM-<script>alert(1)</script>'
# - Debe ser bloqueado y loguear error
```

#### PASO 7: Commit y Deploy

```bash
git add frontend/src/hooks/useGoogleScripts.js
git add frontend/src/config/dompurify.config.js
git add frontend/src/hooks/__tests__/useGoogleScripts.test.js

git commit -m "security: sanitizar XSS en Google Tag Manager

- Validar GTM ID contra formato permitido (GTM-XXXXXX)
- Usar DOMPurify para sanitizar iframe HTML
- Escapar atributos HTML para prevenir inyección
- Agregar tests para validación de XSS
- Loguear intentos de inyección
- Bloquear GTM si ID es inválido

Cierra vulnerabilidad crítica XSS en useGoogleScripts.js"
```

### Checklist de Validación

- [ ] DOMPurify instalado
- [ ] validateGTMId() implementado y testado
- [ ] escapeHtmlAttribute() implementado y testado
- [ ] insertGTM() refactorizado con sanitización
- [ ] Tests pasando (npm test)
- [ ] Dev server sin errores
- [ ] GTM se inicializa correctamente en prod
- [ ] Commit pusheado

### Tiempo Estimado: 2-4 horas

---

## 🔴 FIX 2: MIGRAR FORMULARIOS A ZOD + REACT-HOOK-FORM (CRÍTICO)

**Ubicación:** 6 formularios críticos
**Severidad:** 🔴 CRÍTICA - Input Validation
**Esfuerzo:** 16-24 horas
**Bloqueador:** Parcial - Comenzar con formularios más críticos
**Impacto:** Protección contra inyección NoSQL, validación de datos

### ¿Por qué es crítico?
Sin validación de inputs en el cliente, se pueden enviar datos malformados o maliciosos al servidor. El backend debe validar, pero el cliente debería rechazar primero.

### Formularios Críticos (por orden)

1. **Login.jsx** - Proteja contra ataques de fuerza bruta
2. **Register.jsx** - Validar email, contraseña, datos del usuario
3. **Suppliers.jsx** - Validar rutas FTP, puertos, credenciales
4. **Catalogs.jsx** - Validar nombres, reglas de margen
5. **Marketplaces.jsx** - Validar configuraciones de mercados
6. **AdminEmailTemplates.jsx** - Validar HTML de plantillas

### PASO 1: Crear esquemas Zod reutilizables (2 horas)

**Archivo:** `/frontend/src/schemas/index.js` (crear nuevo)

```javascript
import { z } from 'zod';

// ============================================================================
// ESQUEMAS COMPARTIDOS
// ============================================================================

export const emailSchema = z
  .string('Email requerido')
  .email('Email inválido')
  .trim()
  .toLowerCase();

export const passwordSchema = z
  .string('Contraseña requerida')
  .min(8, 'Mínimo 8 caracteres')
  .regex(/[A-Z]/, 'Debe contener mayúscula')
  .regex(/[a-z]/, 'Debe contener minúscula')
  .regex(/[0-9]/, 'Debe contener número')
  .regex(/[^A-Za-z0-9]/, 'Debe contener carácter especial');

export const nameSchema = z
  .string('Nombre requerido')
  .min(2, 'Mínimo 2 caracteres')
  .max(100, 'Máximo 100 caracteres')
  .trim()
  .regex(/^[a-zA-Z\s-'àáâãäåèéêëìíîïòóôõöùúûüýÿñ]+$/, 'Solo letras, espacios, guiones y apóstrofes');

export const urlSchema = z
  .string('URL requerida')
  .url('URL inválida')
  .startsWith('http', 'URL debe comenzar con http o https');

export const portSchema = z
  .number('Puerto requerido')
  .int('Puerto debe ser número entero')
  .min(1, 'Puerto mínimo: 1')
  .max(65535, 'Puerto máximo: 65535');

export const ipAddressSchema = z
  .string()
  .ip({ version: 'v4' })
  .or(z.string().hostname());

// ============================================================================
// ESQUEMAS POR FORMULARIO
// ============================================================================

// LOGIN
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string('Contraseña requerida').min(1, 'Contraseña requerida'),
  rememberMe: z.boolean().optional().default(false),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// REGISTER
export const registerSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  company: z
    .string()
    .max(100, 'Máximo 100 caracteres')
    .optional()
    .or(z.literal('')),
  password: passwordSchema,
  confirmPassword: z.string('Confirmación requerida'),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'Debe aceptar los términos de servicio',
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
});

export type RegisterFormData = z.infer<typeof registerSchema>;

// SUPPLIER (FTP/SFTP)
export const supplierSchema = z.object({
  name: z
    .string('Nombre requerido')
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres'),

  ftp_schema: z.enum(['ftp', 'ftps', 'sftp'], {
    errorMap: () => ({ message: 'Esquema debe ser FTP, FTPS o SFTP' }),
  }),

  ftp_host: z
    .string('Host requerido')
    .min(3, 'Host inválido'),

  ftp_port: portSchema.default(21),

  ftp_user: z
    .string('Usuario requerido')
    .min(1, 'Usuario requerido')
    .max(100, 'Máximo 100 caracteres'),

  ftp_password: z
    .string('Contraseña requerida')
    .min(1, 'Contraseña requerida')
    .max(200, 'Contraseña muy larga'),

  ftp_path: z
    .string('Ruta requerida')
    .startsWith('/', 'Ruta debe comenzar con /')
    .regex(/^[a-zA-Z0-9\/_\-\.]+$/, 'Ruta contiene caracteres inválidos'),

  sync_interval: z
    .number('Intervalo requerido')
    .int('Debe ser número entero')
    .min(1, 'Mínimo 1 hora')
    .max(168, 'Máximo 168 horas (1 semana)'),

  mode: z.enum(['active', 'passive']).optional().default('passive'),

  description: z
    .string()
    .max(500, 'Descripción muy larga')
    .optional()
    .or(z.literal('')),
});

export type SupplierFormData = z.infer<typeof supplierSchema>;

// CATALOG
export const catalogSchema = z.object({
  name: z
    .string('Nombre requerido')
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres'),

  description: z
    .string()
    .max(500, 'Descripción muy larga')
    .optional()
    .or(z.literal('')),

  basePrice: z
    .number('Precio base requerido')
    .positive('Precio debe ser positivo')
    .multipleOf(0.01, 'Máximo 2 decimales'),

  marginPercentage: z
    .number('Margen requerido')
    .min(0, 'Margen mínimo: 0%')
    .max(500, 'Margen máximo: 500%')
    .multipleOf(0.01, 'Máximo 2 decimales'),

  currency: z.enum(['USD', 'EUR', 'MXN', 'ARS']).default('USD'),
});

export type CatalogFormData = z.infer<typeof catalogSchema>;

// EMAIL TEMPLATE
export const emailTemplateSchema = z.object({
  name: z
    .string('Nombre requerido')
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres'),

  subject: z
    .string('Asunto requerido')
    .min(5, 'Mínimo 5 caracteres')
    .max(200, 'Máximo 200 caracteres'),

  // HTML será validado en el servidor (backend)
  htmlContent: z
    .string('Contenido requerido')
    .min(10, 'Contenido muy corto')
    .max(10000, 'Contenido muy largo'),

  isActive: z.boolean().default(true),
});

export type EmailTemplateFormData = z.infer<typeof emailTemplateSchema>;

// MARKETPLACE
export const marketplaceSchema = z.object({
  name: z
    .string('Nombre requerido')
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres'),

  type: z.enum(['woocommerce', 'shopify', 'prestashop']),

  url: urlSchema,

  apiKey: z
    .string('API Key requerida')
    .min(10, 'API Key inválida'),

  apiSecret: z
    .string('API Secret requerida')
    .min(10, 'API Secret inválida'),

  isActive: z.boolean().default(true),

  syncFrequency: z
    .number('Frecuencia requerida')
    .int()
    .min(1, 'Mínimo 1 hora')
    .max(168, 'Máximo 168 horas'),
});

export type MarketplaceFormData = z.infer<typeof marketplaceSchema>;
```

### PASO 2: Refactorizar Login.jsx (2-3 horas)

**Archivo:** `/frontend/src/pages/Login.jsx`

```javascript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, type LoginFormData } from '../schemas';
import { api } from '../App';
import { toast } from 'sonner';

export default function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur', // Validar cuando se pierde el focus
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      // data está validado y tipado
      const response = await api.post('/api/auth/login', data);

      localStorage.setItem('user', JSON.stringify(response.data.user));
      toast.success('Sesión iniciada');

      // Redirect...
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al iniciar sesión');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        type="email"
        placeholder="Email"
        {...register('email')}
        className={errors.email ? 'border-red-500' : ''}
      />
      {errors.email && <span className="text-red-500">{errors.email.message}</span>}

      <input
        type="password"
        placeholder="Contraseña"
        {...register('password')}
        className={errors.password ? 'border-red-500' : ''}
      />
      {errors.password && <span className="text-red-500">{errors.password.message}</span>}

      <label>
        <input type="checkbox" {...register('rememberMe')} />
        Recuérdame
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
      </button>
    </form>
  );
}
```

### PASO 3: Refactorizar Suppliers.jsx (3-4 horas)

```javascript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { supplierSchema, type SupplierFormData } from '../schemas';
import { api } from '../App';
import { toast } from 'sonner';

export default function SupplierForm() {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SupplierFormData>({
    resolver: zodResolver(supplierSchema),
    defaultValues: {
      ftp_schema: 'sftp',
      ftp_port: 22,
      sync_interval: 6,
      mode: 'passive',
    },
    mode: 'onChange', // Validación en tiempo real
  });

  const schema = watch('ftp_schema');
  const defaultPort = schema === 'sftp' ? 22 : schema === 'ftps' ? 990 : 21;

  const onSubmit = async (data: SupplierFormData) => {
    try {
      // data está completamente validado
      await api.post('/api/suppliers', data);
      toast.success('Proveedor creado exitosamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear proveedor');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Nombre */}
      <div>
        <label>Nombre *</label>
        <input {...register('name')} placeholder="Mi Proveedor FTP" />
        {errors.name && <span className="error">{errors.name.message}</span>}
      </div>

      {/* Esquema */}
      <div>
        <label>Tipo de Conexión *</label>
        <select {...register('ftp_schema')}>
          <option value="ftp">FTP</option>
          <option value="ftps">FTPS</option>
          <option value="sftp">SFTP</option>
        </select>
        {errors.ftp_schema && <span className="error">{errors.ftp_schema.message}</span>}
      </div>

      {/* Host */}
      <div>
        <label>Host *</label>
        <input {...register('ftp_host')} placeholder="ftp.ejemplo.com" />
        {errors.ftp_host && <span className="error">{errors.ftp_host.message}</span>}
      </div>

      {/* Puerto */}
      <div>
        <label>Puerto *</label>
        <input type="number" {...register('ftp_port', { valueAsNumber: true })} />
        {errors.ftp_port && <span className="error">{errors.ftp_port.message}</span>}
        <small>Defecto: {defaultPort}</small>
      </div>

      {/* Usuario */}
      <div>
        <label>Usuario *</label>
        <input {...register('ftp_user')} placeholder="usuario" />
        {errors.ftp_user && <span className="error">{errors.ftp_user.message}</span>}
      </div>

      {/* Contraseña */}
      <div>
        <label>Contraseña *</label>
        <input type="password" {...register('ftp_password')} />
        {errors.ftp_password && <span className="error">{errors.ftp_password.message}</span>}
      </div>

      {/* Ruta */}
      <div>
        <label>Ruta Remota *</label>
        <input {...register('ftp_path')} placeholder="/catalogs" />
        {errors.ftp_path && <span className="error">{errors.ftp_path.message}</span>}
      </div>

      {/* Intervalo de sincronización */}
      <div>
        <label>Sincronizar cada (horas) *</label>
        <input type="number" {...register('sync_interval', { valueAsNumber: true })} />
        {errors.sync_interval && <span className="error">{errors.sync_interval.message}</span>}
      </div>

      {/* Modo */}
      <div>
        <label>Modo FTP</label>
        <select {...register('mode')}>
          <option value="passive">Pasivo</option>
          <option value="active">Activo</option>
        </select>
      </div>

      {/* Descripción */}
      <div>
        <label>Descripción</label>
        <textarea {...register('description')} placeholder="Descripción opcional..." />
        {errors.description && <span className="error">{errors.description.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Guardando...' : 'Crear Proveedor'}
      </button>
    </form>
  );
}
```

### PASO 4: Tests para esquemas (2 horas)

**Archivo:** `/frontend/src/schemas/__tests__/index.test.js`

```javascript
import { loginSchema, registerSchema, supplierSchema } from '../index';

describe('Validation Schemas', () => {

  describe('loginSchema', () => {
    it('debe validar email y contraseña válidos', async () => {
      const validData = {
        email: 'user@example.com',
        password: 'password123',
        rememberMe: true,
      };

      const result = await loginSchema.parseAsync(validData);
      expect(result.email).toBe('user@example.com');
    });

    it('debe rechazar email inválido', async () => {
      const invalidData = {
        email: 'not-an-email',
        password: 'password123',
      };

      await expect(loginSchema.parseAsync(invalidData)).rejects.toThrow();
    });
  });

  describe('registerSchema', () => {
    it('debe validar registro completo válido', async () => {
      const validData = {
        name: 'John Doe',
        email: 'john@example.com',
        password: 'Password123!@',
        confirmPassword: 'Password123!@',
        acceptTerms: true,
      };

      const result = await registerSchema.parseAsync(validData);
      expect(result.name).toBe('John Doe');
    });

    it('debe rechazar contraseñas no coincidentes', async () => {
      const invalidData = {
        name: 'John Doe',
        email: 'john@example.com',
        password: 'Password123!@',
        confirmPassword: 'DifferentPassword123!@',
        acceptTerms: true,
      };

      await expect(registerSchema.parseAsync(invalidData)).rejects.toThrow();
    });

    it('debe rechazar si no acepta términos', async () => {
      const invalidData = {
        name: 'John Doe',
        email: 'john@example.com',
        password: 'Password123!@',
        confirmPassword: 'Password123!@',
        acceptTerms: false,
      };

      await expect(registerSchema.parseAsync(invalidData)).rejects.toThrow();
    });
  });

  describe('supplierSchema', () => {
    it('debe validar proveedor FTP válido', async () => {
      const validData = {
        name: 'Mi Proveedor',
        ftp_schema: 'sftp',
        ftp_host: 'ftp.example.com',
        ftp_port: 22,
        ftp_user: 'user123',
        ftp_password: 'pass12345',
        ftp_path: '/catalogs',
        sync_interval: 6,
      };

      const result = await supplierSchema.parseAsync(validData);
      expect(result.name).toBe('Mi Proveedor');
    });

    it('debe rechazar puerto fuera de rango', async () => {
      const invalidData = {
        name: 'Mi Proveedor',
        ftp_schema: 'sftp',
        ftp_host: 'ftp.example.com',
        ftp_port: 99999,  // Inválido
        ftp_user: 'user123',
        ftp_password: 'pass12345',
        ftp_path: '/catalogs',
        sync_interval: 6,
      };

      await expect(supplierSchema.parseAsync(invalidData)).rejects.toThrow();
    });

    it('debe rechazar ruta que no comienza con /', async () => {
      const invalidData = {
        name: 'Mi Proveedor',
        ftp_schema: 'sftp',
        ftp_host: 'ftp.example.com',
        ftp_port: 22,
        ftp_user: 'user123',
        ftp_password: 'pass12345',
        ftp_path: 'catalogs',  // Sin / al inicio
        sync_interval: 6,
      };

      await expect(supplierSchema.parseAsync(invalidData)).rejects.toThrow();
    });
  });
});
```

### PASO 5: Migración de formularios (6-8 horas)

Aplicar el mismo patrón a:
- [ ] `Catalogs.jsx` (usar catalogSchema)
- [ ] `Marketplaces.jsx` (usar marketplaceSchema)
- [ ] `Register.jsx` (usar registerSchema)
- [ ] `AdminEmailTemplates.jsx` (usar emailTemplateSchema)

### PASO 6: Verificación Final

```bash
# 1. Ejecutar todos los tests
npm test -- schemas

# 2. Probar cada formulario manualmente
npm start

# 3. Intentar enviar datos inválidos
# - Debe mostrar errores
# - No debe permitir enviar

# 4. Enviar datos válidos
# - Debe enviar correctamente
```

### Commit

```bash
git add frontend/src/schemas/
git add frontend/src/pages/Login.jsx
git add frontend/src/pages/Register.jsx
git add frontend/src/pages/Suppliers.jsx
git add frontend/src/pages/Catalogs.jsx
git add frontend/src/pages/Marketplaces.jsx
git add frontend/src/pages/AdminEmailTemplates.jsx

git commit -m "security: implementar validación de inputs con Zod

- Crear esquemas reutilizables en frontend/src/schemas/
- Migrar 6 formularios a react-hook-form + Zod
- Validación en tiempo real con mensajes de error
- Tests exhaustivos para cada esquema
- Prevenir inyección NoSQL y validación débil

Formularios refactorizados:
- Login
- Register
- Suppliers (FTP/SFTP)
- Catalogs
- Marketplaces
- Email Templates

Todos los formularios ahora validan:
- Tipos de dato
- Rango de valores
- Formatos (email, URL, IP, etc)
- Caracteres especiales permitidos
"
```

### Tiempo Estimado: 16-24 horas (dividir en 2-3 sesiones)

---

## 🟠 FIX 3: REMOVER TOKEN DE localStorage (ALTA)

**Ubicación:** `/frontend/src/pages/Register.jsx` línea 220
**Severidad:** 🟠 ALTA - Token inseguro en localStorage
**Esfuerzo:** < 1 hora
**Bloqueador:** SÍ - Token sensible expuesto a XSS
**Impacto:** Si hay XSS, el atacante puede robar token

### Código Actual (Vulnerable)

```javascript
// VULNERABLE: localStorage es accesible a JavaScript
localStorage.setItem("pending_token", token);
```

### FIX: Usar sessionStorage

```javascript
// SEGURO: sessionStorage se limpia cuando cierra la pestaña
sessionStorage.setItem("pending_token", token);

// O mejor aún: usar estado en memoria (más seguro)
const [pendingToken, setPendingToken] = useState(token);
// Si el usuario recarga, el token se pierde (comportamiento seguro)
```

### Pasos

1. Buscar todas las referencias a `pending_token`
```bash
grep -r "pending_token" frontend/src/
```

2. Reemplazar `localStorage` con `sessionStorage`
3. Considerar usar estado en memoria para máxima seguridad
4. Test: Verificar que el token se limpie al cerrar pestaña

### Commit

```bash
git commit -m "security: remover token de localStorage

- Cambiar localStorage a sessionStorage para pending_token
- sessionStorage se limpia automáticamente al cerrar pestaña
- Reduce riesgo de XSS token theft
"
```

---

## 🟡 FIX 4: WEBSOCKET HEARTBEAT + TIMEOUT (MEDIA)

**Ubicación:** Backend + Nginx
**Severidad:** 🟡 MEDIA - Conexiones fantasma
**Esfuerzo:** 1-2 horas

### El Problema

WebSocket con timeout 7 días permite conexiones muertas indefinidamente.

### Solución: Heartbeat + Timeout realista

**Backend (FastAPI):**

```python
# En backend/server.py

import asyncio
from datetime import datetime, timezone

async def heartbeat_task(manager, user_id, ws):
    """Enviar ping cada 30 segundos para mantener WebSocket vivo"""
    try:
        while True:
            await asyncio.sleep(30)
            await manager.send_to_user(user_id, {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except Exception:
        pass  # WebSocket desconectado

@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)

    # Iniciar heartbeat
    heartbeat = asyncio.create_task(heartbeat_task(manager, user_id, websocket))

    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=300)
            # Procesar mensaje
    except asyncio.TimeoutError:
        # Timeout: desconectar
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)
    finally:
        heartbeat.cancel()
```

**Nginx:**

```nginx
# En scripts/nginx_config_plesk.conf

location /ws/ {
    proxy_pass http://syncstock_backend/ws/;
    proxy_http_version 1.1;

    # Headers WebSocket
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    # Timeouts más realistas (con heartbeat cada 30s)
    proxy_connect_timeout 60s;    # Conectar
    proxy_send_timeout 310s;      # 5 minutos + 10s buffer
    proxy_read_timeout 310s;      # 5 minutos + 10s buffer

    # Sin buffering
    proxy_buffering off;
}
```

---

## 🟡 FIX 5: RATE LIMITING EN NGINX (MEDIA)

**Ubicación:** `/scripts/nginx_config_plesk.conf`
**Severidad:** 🟡 MEDIA - DDoS protection
**Esfuerzo:** < 1 hora

### Código a Agregar

```nginx
# En http {} block de nginx.conf

limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

# En server {} block

location /api/auth/login {
    limit_req zone=login burst=2 nodelay;
    proxy_pass http://syncstock_backend;
}

location /api/ {
    limit_req zone=api burst=10 nodelay;
    proxy_pass http://syncstock_backend;
}

location / {
    limit_req zone=general burst=20 nodelay;
    root /var/www/vhosts/app.sync-stock.com/app/frontend/build;
    try_files $uri $uri/ /index.html;
}
```

---

## 🟡 FIX 6: OPTIMIZAR CIPHERS SSL/TLS (MEDIA)

**Ubicación:** Plesk SSL/TLS Settings
**Severidad:** 🟡 MEDIA
**Esfuerzo:** < 1 hora

### Agregar en Plesk Nginx Directives

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers on;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

---

## 🟡 FIX 7: DOCUMENTAR PERMISOS ARCHIVO (MEDIA)

**Ubicación:** `/install.sh`
**Severidad:** 🟡 MEDIA
**Esfuerzo:** 1-2 horas

### Agregar en install.sh

```bash
# Después de descargar la aplicación, agregar:

print_step "Configurando permisos de archivos"

# Permisos para directorios
find $APP_DIR -type d -exec chmod 755 {} \;
print_success "Directorios: 755"

# Permisos para archivos
find $APP_DIR -type f -exec chmod 644 {} \;
print_success "Archivos: 644"

# Permisos para scripts ejecutables
find $APP_DIR -name "*.sh" -exec chmod 755 {} \;
print_success "Scripts ejecutables: 755"

# Configuración sensible (solo app puede leer)
chmod 600 $PERSISTENT_CONFIG_DIR/config.json
chmod 700 $PERSISTENT_CONFIG_DIR
print_success "Config persistente: 600/700 (solo aplicación puede leer)"

# Uploads (fuera de web root)
mkdir -p /var/data/syncstock-uploads
chown -R $PLESK_USER:$PLESK_USER /var/data/syncstock-uploads
chmod 750 /var/data/syncstock-uploads
print_success "Upload directory: 750"
```

---

## 🟡 FIX 8: CONFIGURAR LOG ROTATION (MEDIA)

**Ubicación:** `/etc/logrotate.d/syncstock`
**Severidad:** 🟡 MEDIA
**Esfuerzo:** < 1 hora

### Crear archivo

```bash
sudo nano /etc/logrotate.d/syncstock
```

### Contenido

```
/var/log/syncstock.log {
  daily
  rotate 7
  compress
  missingok
  notifempty
  create 0640 syncstock syncstock
  sharedscripts
  postrotate
    systemctl reload syncstock > /dev/null 2>&1 || true
  endscript
}
```

### Verificar

```bash
logrotate -f /etc/logrotate.d/syncstock
logrotate -v /etc/logrotate.d/syncstock
```

---

## 🟢 FIX 9: INTEGRAR SENTRY (BAJA)

**Ubicación:** Backend + Frontend
**Severidad:** 🟢 BAJA - Observabilidad
**Esfuerzo:** 2-4 horas

### Backend

```bash
pip install sentry-sdk
```

```python
# backend/server.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

### Frontend

```bash
npm install @sentry/react
```

```javascript
// frontend/src/index.js
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

---

## 🟢 FIX 10: VALIDAR URLS IMAGEN (BAJA)

**Ubicación:** Login.jsx, Register.jsx, etc.
**Severidad:** 🟢 BAJA
**Esfuerzo:** < 1 hora

### Crear validador

```javascript
// frontend/src/utils/imageValidator.js

export const validateImageUrl = (url) => {
  try {
    const urlObj = new URL(url);

    // Solo HTTPS
    if (urlObj.protocol !== 'https:') return false;

    // Solo dominios permitidos
    const allowedDomains = [
      'syncstock.app',
      'cdn.example.com',
    ];

    return allowedDomains.some(domain => urlObj.hostname.endsWith(domain));
  } catch {
    return false;
  }
};

// Uso
const logoUrl = 'https://syncstock.app/logo.png';
if (validateImageUrl(logoUrl)) {
  // Usar URL
}
```

---

## 📅 CRONOGRAMA RECOMENDADO

### SEMANA 1
- Lunes: FIX 1 (XSS) - 2-4 horas
- Martes: FIX 3 (localStorage) + FIX 5 (rate limiting) - 1 hora
- Miércoles-Viernes: Comenzar FIX 2 (Zod) - 8 horas

### SEMANA 2
- Continuar FIX 2 (Zod) - 12-16 horas

### SEMANA 3
- FIX 4 (WebSocket) - 1-2 horas
- FIX 6 (SSL/TLS) - <1 hora
- FIX 7 (Permisos) - 1-2 horas
- FIX 8 (Log rotation) - <1 hora

### SEMANA 4
- FIX 9 (Sentry) - 2-4 horas
- FIX 10 (Image validation) - <1 hora
- Testing final de todos los fixes

---

## ✅ CHECKLIST FINAL

### Por cada FIX completado:

- [ ] Código escrito
- [ ] Tests pasando
- [ ] Code review realizado
- [ ] Verificación en desarrollo
- [ ] Documentación actualizada
- [ ] Commit con mensaje descriptivo
- [ ] Pusheado a rama
- [ ] Verificación en staging (si aplica)

---

**Generado:** 27 de marzo de 2026
**Rama:** `claude/code-review-security-JitQz`
