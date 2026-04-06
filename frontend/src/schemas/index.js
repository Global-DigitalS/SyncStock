/**
 * Esquemas de validación Zod para todos los formularios de SyncStock
 * Reutilizables y composables para mantener consistencia en validaciones
 */

import { z } from 'zod';

// ========================================
// ESQUEMAS BASE REUTILIZABLES
// ========================================

/**
 * Email válido (RFC 5322 simplificado)
 */
export const emailSchema = z
  .string()
  .min(1, 'El correo es requerido')
  .email('Correo inválido')
  .toLowerCase()
  .trim();

/**
 * Contraseña con validaciones de seguridad
 * - Mínimo 8 caracteres
 * - Al menos una mayúscula
 * - Al menos una minúscula
 * - Al menos un número
 * - Al menos un carácter especial
 */
export const passwordSchema = z
  .string()
  .min(8, 'La contraseña debe tener al menos 8 caracteres')
  .regex(/[A-Z]/, 'La contraseña debe contener al menos una mayúscula')
  .regex(/[a-z]/, 'La contraseña debe contener al menos una minúscula')
  .regex(/\d/, 'La contraseña debe contener al menos un número')
  .regex(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/, 'La contraseña debe contener al menos un carácter especial');

/**
 * Nombre de usuario/persona
 */
export const nameSchema = z
  .string()
  .min(2, 'El nombre debe tener al menos 2 caracteres')
  .max(100, 'El nombre no puede exceder 100 caracteres')
  .trim();

/**
 * URL válida
 */
export const urlSchema = z
  .string()
  .url('URL inválida')
  .startsWith('http', 'La URL debe empezar con http o https');

/**
 * Puertos válidos (1-65535)
 */
export const portSchema = z
  .number()
  .min(1, 'El puerto debe ser mayor a 0')
  .max(65535, 'El puerto no puede exceder 65535')
  .int('El puerto debe ser un número entero');

/**
 * Dirección IP o hostname válido
 */
export const hostSchema = z
  .string()
  .min(3, 'El host debe tener al menos 3 caracteres')
  .refine(
    (val) => {
      // Verificar si es una IP válida (simplificado)
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
      // O si es un hostname válido
      const hostnameRegex = /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
      return ipRegex.test(val) || hostnameRegex.test(val) || val === 'localhost';
    },
    'Host inválido. Debe ser una IP, hostname o localhost'
  );

/**
 * Ruta de archivo (debe empezar con /)
 */
export const pathSchema = z
  .string()
  .min(1, 'La ruta es requerida')
  .startsWith('/', 'La ruta debe empezar con /');

/**
 * Intervalo de sincronización en horas (1-168)
 */
export const syncIntervalSchema = z
  .number()
  .min(1, 'El intervalo debe ser al menos 1 hora')
  .max(168, 'El intervalo no puede exceder 7 días (168 horas)')
  .int('El intervalo debe ser un número entero');

/**
 * Porcentaje válido (0-100)
 */
export const percentageSchema = z
  .number()
  .min(0, 'El porcentaje no puede ser menor a 0')
  .max(100, 'El porcentaje no puede exceder 100');

/**
 * Margen de beneficio
 */
export const marginSchema = z
  .number()
  .min(-100, 'El margen no puede ser menor a -100%')
  .max(1000, 'El margen no puede exceder 1000%');

/**
 * Slug válido (solo letras, números y guiones)
 */
export const slugSchema = z
  .string()
  .min(1, 'El slug es requerido')
  .regex(/^[a-z0-9-]+$/, 'El slug solo puede contener letras minúsculas, números y guiones')
  .toLowerCase();

// ========================================
// ESQUEMAS DE AUTENTICACIÓN
// ========================================

/**
 * Login: Email + Contraseña
 */
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'La contraseña es requerida'),
  rememberMe: z.boolean().optional().default(false),
});

export type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Registro: Nombre + Email + Contraseña + Confirmación
 */
export const registerSchema = z
  .object({
    name: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Debe confirmar la contraseña'),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: 'Debe aceptar los términos y condiciones',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

/**
 * Recuperación de contraseña: Email
 */
export const forgotPasswordSchema = z.object({
  email: emailSchema,
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

/**
 * Reset de contraseña: Nueva contraseña + Confirmación
 */
export const resetPasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Debe confirmar la contraseña'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  });

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

// ========================================
// ESQUEMAS DE PROVEEDORES (SUPPLIERS)
// ========================================

/**
 * Proveedor: FTP/SFTP/URL
 */
export const supplierSchema = z
  .object({
    name: z
      .string()
      .min(2, 'El nombre debe tener al menos 2 caracteres')
      .max(100, 'El nombre no puede exceder 100 caracteres')
      .trim(),
    description: z
      .string()
      .max(500, 'La descripción no puede exceder 500 caracteres')
      .optional()
      .default(''),
    supplier_type: z.enum(['ftp', 'ftps', 'sftp', 'url', 'csv_url', 'xlsx_url'], {
      errorMap: () => ({ message: 'Tipo de proveedor inválido' }),
    }),
    ftp_host: hostSchema.optional(),
    ftp_port: portSchema.optional(),
    ftp_user: z
      .string()
      .min(1, 'Usuario FTP requerido')
      .max(100, 'Usuario FTP inválido')
      .optional(),
    ftp_password: z.string().max(200, 'Contraseña FTP inválida').optional(),
    ftp_path: pathSchema.optional(),
    ftp_mode: z.enum(['active', 'passive']).optional().default('passive'),
    url: urlSchema.optional(),
    sync_interval: syncIntervalSchema.default(6),
    enabled: z.boolean().optional().default(true),
  })
  .refine(
    (data) => {
      // Si es FTP/SFTP, validar campos obligatorios
      if (['ftp', 'ftps', 'sftp'].includes(data.supplier_type)) {
        return data.ftp_host && data.ftp_user && data.ftp_password && data.ftp_path;
      }
      // Si es URL-based, validar URL
      if (['url', 'csv_url', 'xlsx_url'].includes(data.supplier_type)) {
        return data.url;
      }
      return true;
    },
    {
      message: 'Campos requeridos faltantes para este tipo de proveedor',
      path: ['supplier_type'],
    }
  );

export type SupplierFormData = z.infer<typeof supplierSchema>;

// ========================================
// ESQUEMAS DE CATÁLOGOS
// ========================================

/**
 * Catálogo
 */
export const catalogSchema = z.object({
  name: z
    .string()
    .min(2, 'El nombre debe tener al menos 2 caracteres')
    .max(100, 'El nombre no puede exceder 100 caracteres')
    .trim(),
  description: z
    .string()
    .max(500, 'La descripción no puede exceder 500 caracteres')
    .optional()
    .default(''),
  slug: slugSchema,
  enabled: z.boolean().optional().default(true),
  default_margin: marginSchema.optional().default(0),
  default_margin_type: z.enum(['fixed', 'percentage']).optional().default('percentage'),
});

export type CatalogFormData = z.infer<typeof catalogSchema>;

/**
 * Regla de margen para catálogos
 */
export const marginRuleSchema = z.object({
  catalog_id: z.string().min(1, 'Catálogo requerido'),
  min_price: z.number().min(0, 'Precio mínimo no válido').optional(),
  max_price: z.number().min(0, 'Precio máximo no válido').optional(),
  margin: marginSchema,
  margin_type: z.enum(['fixed', 'percentage']).optional().default('percentage'),
});

export type MarginRuleFormData = z.infer<typeof marginRuleSchema>;

// ========================================
// ESQUEMAS DE MARKETPLACES / TIENDAS
// ========================================

/**
 * Configuración de WooCommerce
 */
export const woocommerceSchema = z.object({
  store_name: z
    .string()
    .min(2, 'Nombre de tienda requerido')
    .max(100, 'Nombre de tienda inválido'),
  store_url: urlSchema,
  consumer_key: z.string().min(1, 'Consumer key requerida').trim(),
  consumer_secret: z.string().min(1, 'Consumer secret requerida').trim(),
  enabled: z.boolean().optional().default(true),
});

export type WoocommerceFormData = z.infer<typeof woocommerceSchema>;

/**
 * Configuración de Shopify
 */
export const shopifySchema = z.object({
  store_name: z
    .string()
    .min(2, 'Nombre de tienda requerido')
    .max(100, 'Nombre de tienda inválido'),
  shop_domain: z.string().regex(/^[a-z0-9-]+\.myshopify\.com$/, 'Dominio Shopify inválido'),
  access_token: z.string().min(1, 'Access token requerido').trim(),
  enabled: z.boolean().optional().default(true),
});

export type ShopifyFormData = z.infer<typeof shopifySchema>;

/**
 * Configuración de PrestaShop
 */
export const prestashopSchema = z.object({
  store_name: z
    .string()
    .min(2, 'Nombre de tienda requerido')
    .max(100, 'Nombre de tienda inválido'),
  store_url: urlSchema,
  api_key: z.string().min(1, 'API key requerida').trim(),
  enabled: z.boolean().optional().default(true),
});

export type PrestashopFormData = z.infer<typeof prestashopSchema>;

// ========================================
// ESQUEMAS DE EMAIL / COMUNICACIÓN
// ========================================

/**
 * Configuración SMTP
 */
export const smtpConfigSchema = z.object({
  smtp_host: hostSchema,
  smtp_port: portSchema.default(587),
  smtp_user: emailSchema,
  smtp_password: z.string().min(1, 'Contraseña SMTP requerida'),
  smtp_from_email: emailSchema,
  smtp_from_name: z
    .string()
    .min(2, 'Nombre remitente requerido')
    .max(100, 'Nombre remitente inválido'),
  smtp_tls: z.boolean().optional().default(true),
});

export type SmtpConfigFormData = z.infer<typeof smtpConfigSchema>;

/**
 * Plantilla de email
 */
export const emailTemplateSchema = z.object({
  template_name: z
    .string()
    .min(2, 'Nombre de plantilla requerido')
    .max(100, 'Nombre de plantilla inválido')
    .trim(),
  template_subject: z
    .string()
    .min(3, 'Asunto requerido')
    .max(200, 'Asunto muy largo')
    .trim(),
  template_body: z
    .string()
    .min(10, 'Cuerpo del email debe tener al menos 10 caracteres')
    .max(5000, 'Cuerpo del email muy largo'),
  template_type: z
    .enum(['welcome', 'password_reset', 'sync_completed', 'sync_failed', 'custom'], {
      errorMap: () => ({ message: 'Tipo de plantilla inválido' }),
    })
    .optional(),
  enabled: z.boolean().optional().default(true),
});

export type EmailTemplateFormData = z.infer<typeof emailTemplateSchema>;

// ========================================
// ESQUEMAS DE CONFIGURACIÓN GENERAL
// ========================================

/**
 * Configuración de Google Services
 */
export const googleServicesSchema = z.object({
  tag_manager_enabled: z.boolean().optional().default(false),
  tag_manager_container_id: z
    .string()
    .regex(/^GTM-[A-Z0-9]{6,}$/, 'ID de Google Tag Manager inválido')
    .optional()
    .nullable(),
  analytics_enabled: z.boolean().optional().default(false),
  analytics_measurement_id: z
    .string()
    .regex(/^G-[A-Z0-9]{10,}$/, 'ID de Google Analytics inválido')
    .optional()
    .nullable(),
  google_ads_enabled: z.boolean().optional().default(false),
  google_ads_conversion_id: z
    .string()
    .regex(/^AW-\d{9,}$/, 'ID de Google Ads inválido')
    .optional()
    .nullable(),
  search_console_enabled: z.boolean().optional().default(false),
  search_console_verification_code: z.string().optional().nullable(),
});

export type GoogleServicesFormData = z.infer<typeof googleServicesSchema>;

// ========================================
// ESQUEMAS DE VALIDACIÓN DE PERFILES
// ========================================

/**
 * Perfil de usuario (actualización)
 */
export const userProfileSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  avatar_url: urlSchema.optional(),
  company_name: z
    .string()
    .max(100, 'Nombre de empresa inválido')
    .optional(),
  timezone: z.string().optional(),
  language: z.enum(['es', 'en']).optional().default('es'),
});

export type UserProfileFormData = z.infer<typeof userProfileSchema>;

/**
 * Cambio de contraseña
 */
export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Contraseña actual requerida'),
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, 'Confirmación de contraseña requerida'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })
  .refine((data) => data.currentPassword !== data.newPassword, {
    message: 'La nueva contraseña debe ser diferente a la actual',
    path: ['newPassword'],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
