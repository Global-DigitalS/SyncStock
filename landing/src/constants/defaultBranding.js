/**
 * Constantes de branding y datos por defecto para la landing page.
 * Se utilizan como fallback cuando las llamadas API fallan.
 */

/**
 * Configuración de branding por defecto.
 * Se fusiona con datos del servidor si están disponibles.
 */
export const DEFAULT_BRANDING = {
  app_name: "SyncStock",
  app_slogan: "Sincronización de Inventario B2B",
  logo_url: null,
  favicon_url: null,
  primary_color: "#4f46e5",
  secondary_color: "#0f172a",
  accent_color: "#10b981",
  footer_text: "",
  page_title: "SyncStock — Sincronización de Inventario B2B Automatizada",
  hero_title: "Gestiona tu inventario de forma inteligente",
  hero_subtitle:
    "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos.",
};

/**
 * Array de páginas públicas por defecto.
 * Estructura esperada: { id, slug, title, content, is_published, created_at, updated_at }
 */
export const DEFAULT_PAGES = [
  {
    id: "home",
    slug: "inicio",
    title: "Inicio",
    content:
      "Bienvenido a SyncStock. Sincroniza tu inventario de forma automática y ahorra horas cada semana.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "features",
    slug: "caracteristicas",
    title: "Características",
    content:
      "Descubre todas las funcionalidades que SyncStock ofrece para automatizar tu negocio.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "pricing",
    slug: "precios",
    title: "Precios",
    content:
      "Planes flexibles para empresas de todos los tamaños. Prueba gratis 14 días sin necesidad de tarjeta.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "about",
    slug: "nosotros",
    title: "Acerca de",
    content:
      "Conoce la historia de SyncStock y nuestro compromiso con la automatización del eCommerce B2B.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "contact",
    slug: "contacto",
    title: "Contacto",
    content:
      "¿Preguntas? Estamos aquí para ayudarte. Contáctanos por email o mediante nuestro formulario.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "privacy",
    slug: "privacidad",
    title: "Política de Privacidad",
    content:
      "Cómo recopilamos, usamos y protegemos tus datos personales. Tu privacidad es nuestra prioridad.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "terms",
    slug: "terminos",
    title: "Términos de Servicio",
    content:
      "Términos y condiciones de uso de la plataforma SyncStock. Por favor, léelos cuidadosamente.",
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

/**
 * Planes de suscripción por defecto.
 * Estructura esperada: { id, name, description, price_monthly, price_yearly, max_suppliers, max_catalogs, ... }
 */
export const DEFAULT_PLANS = [
  {
    id: "free",
    name: "Free",
    description: "Para probar la plataforma",
    price_monthly: 0,
    price_yearly: 0,
    trial_days: 0,
    max_suppliers: 2,
    max_catalogs: 1,
    max_products: 200,
    max_stores: 1,
    features: [
      "2 proveedores",
      "1 catálogo",
      "200 productos",
      "1 tienda",
      "Soporte por email",
    ],
    is_default: true,
    sort_order: 0,
  },
  {
    id: "starter",
    name: "Starter",
    description: "Para pequeños negocios",
    price_monthly: 29,
    price_yearly: 290,
    trial_days: 14,
    max_suppliers: 5,
    max_catalogs: 3,
    max_products: 2000,
    max_stores: 2,
    features: [
      "5 proveedores",
      "3 catálogos",
      "2.000 productos",
      "2 tiendas",
      "Soporte prioritario",
      "Sincronización automática",
    ],
    sort_order: 1,
  },
  {
    id: "professional",
    name: "Professional",
    description: "Para negocios en crecimiento",
    price_monthly: 79,
    price_yearly: 790,
    trial_days: 14,
    max_suppliers: 20,
    max_catalogs: 10,
    max_products: 20000,
    max_stores: 5,
    features: [
      "20 proveedores",
      "10 catálogos",
      "20.000 productos",
      "5 tiendas",
      "CRM integrado",
      "Soporte 24/7",
      "Sincronización automática",
      "Exportación CSV/Excel",
    ],
    is_popular: true,
    sort_order: 2,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "Para grandes empresas",
    price_monthly: 199,
    price_yearly: 1990,
    trial_days: 30,
    max_suppliers: 9999,
    max_catalogs: 9999,
    max_products: 9999999,
    max_stores: 9999,
    features: [
      "Proveedores ilimitados",
      "Catálogos ilimitados",
      "Productos ilimitados",
      "Tiendas ilimitadas",
      "8 CRMs: HubSpot, Salesforce, Odoo...",
      "Soporte dedicado 24/7",
      "API personalizada",
      "Facturación personalizada",
    ],
    sort_order: 3,
  },
];

/**
 * Exportar un objeto con todos los valores por defecto.
 * Útil para inicializaciones de estado que requieren múltiples recursos.
 */
export const DEFAULT_DATA = {
  branding: DEFAULT_BRANDING,
  pages: DEFAULT_PAGES,
  plans: DEFAULT_PLANS,
};

export default DEFAULT_DATA;
