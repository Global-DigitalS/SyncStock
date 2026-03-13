import { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

const API_URL = (process.env.REACT_APP_API_URL || "https://api.sync-stock.com").replace(/\/$/, "");
const APP_URL = (process.env.REACT_APP_APP_URL || "https://app.sync-stock.com").replace(/\/$/, "");

const defaultBranding = {
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
  hero_subtitle: "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos.",
};

const defaultPlans = [
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
    features: ["2 proveedores", "1 catálogo", "200 productos", "1 tienda", "Soporte por email"],
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
    features: ["5 proveedores", "3 catálogos", "2.000 productos", "2 tiendas", "Soporte prioritario", "Sincronización automática"],
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
    features: ["20 proveedores", "10 catálogos", "20.000 productos", "5 tiendas", "CRM integrado", "Soporte 24/7", "Sincronización automática", "Exportación CSV/Excel"],
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
    features: ["Proveedores ilimitados", "Catálogos ilimitados", "Productos ilimitados", "Tiendas ilimitadas", "CRM Dolibarr + Odoo", "Soporte dedicado 24/7", "API personalizada", "Facturación personalizada"],
    sort_order: 3,
  },
];

const defaultContent = {
  hero: {
    title: "Sincroniza tu inventario con un clic",
    subtitle: "Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente. Ahorra horas de trabajo manual cada semana.",
    cta_primary: "Empezar Gratis",
    cta_secondary: "Ver Demo",
    badge: "✨ 14 días de prueba gratuita — sin tarjeta de crédito",
  },
  stats: [
    { value: "80%", label: "Menos tiempo en gestión" },
    { value: "0", label: "Errores de sincronización" },
    { value: "24/7", label: "Actualización automática" },
    { value: "+500", label: "Empresas confían en nosotros" },
  ],
  features: [
    { icon: "Zap", title: "Sincronización Automática", description: "Actualiza precios, stock y productos en todas tus tiendas sin mover un dedo." },
    { icon: "Database", title: "Multi-Proveedor", description: "Importa catálogos de múltiples proveedores en diferentes formatos (CSV, Excel, XML, FTP)." },
    { icon: "Store", title: "Multi-Tienda", description: "Gestiona WooCommerce, PrestaShop, Shopify y más desde un solo panel centralizado." },
    { icon: "Calculator", title: "Márgenes Inteligentes", description: "Configura reglas de precios por categoría, proveedor o producto individual con precisión." },
    { icon: "RefreshCw", title: "CRM Integrado", description: "Sincroniza con Dolibarr y Odoo para mantener todos tus sistemas siempre actualizados." },
    { icon: "Shield", title: "Datos Seguros", description: "Encriptación de extremo a extremo y copias de seguridad automáticas diarias." },
    { icon: "BarChart3", title: "Analíticas Avanzadas", description: "Dashboard con métricas en tiempo real: historial de precios, evolución de stock y más." },
    { icon: "Webhook", title: "API & Webhooks", description: "Conecta con cualquier sistema externo mediante nuestra API REST y webhooks configurables." },
    { icon: "Clock", title: "Historial de Precios", description: "Rastrea cada cambio de precio y stock con registro histórico completo y alertas automáticas." },
  ],
  integrations: [
    { name: "WooCommerce", icon: "ShoppingCart", category: "E-commerce" },
    { name: "Shopify", icon: "Store", category: "E-commerce" },
    { name: "PrestaShop", icon: "Globe", category: "E-commerce" },
    { name: "Dolibarr", icon: "Building2", category: "CRM/ERP" },
    { name: "Odoo", icon: "Cpu", category: "CRM/ERP" },
    { name: "FTP/SFTP", icon: "Database", category: "Fuentes" },
    { name: "CSV/XLSX", icon: "FileSpreadsheet", category: "Formatos" },
    { name: "XML/API", icon: "Webhook", category: "Formatos" },
    { name: "Stripe", icon: "Lock", category: "Pagos" },
  ],
  how_it_works: [
    { step: 1, title: "Conecta tus proveedores", description: "Añade fuentes de datos FTP, SFTP, URL, CSV o Excel. SyncStock importa y mapea automáticamente los campos del catálogo." },
    { step: 2, title: "Configura tus catálogos", description: "Define reglas de margen, filtra productos y organiza múltiples catálogos para diferentes canales de venta." },
    { step: 3, title: "Publica en tus tiendas", description: "Sincroniza automáticamente con WooCommerce, Shopify, PrestaShop y tu CRM. Siempre actualizado." },
  ],
  testimonials: [
    { quote: "SyncStock nos ha ahorrado más de 20 horas semanales en gestión de catálogos. Increíble.", author: "María García", role: "CEO, TechStore España", avatar: null, rating: 5 },
    { quote: "La sincronización con Dolibarr funciona perfectamente. Sin errores y en tiempo real.", author: "Carlos López", role: "Director Operaciones, Distribuciones López", avatar: null, rating: 5 },
    { quote: "Gestionamos 15 proveedores y 3 tiendas desde un panel. Antes era un caos total.", author: "Ana Martínez", role: "Gestora de Compras, Comercial Martínez SL", avatar: null, rating: 5 },
  ],
  faq: [
    { question: "¿Cuánto tiempo tarda la configuración inicial?", answer: "La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas conectar tus proveedores y tiendas." },
    { question: "¿Puedo probar antes de pagar?", answer: "¡Por supuesto! Ofrecemos 14 días de prueba gratuita con todas las funciones premium incluidas, sin necesidad de tarjeta de crédito." },
    { question: "¿Qué formatos de proveedor soportáis?", answer: "Soportamos FTP, SFTP, URL directa, CSV, Excel (XLSX/XLS) y XML. Si tu proveedor usa otro formato, contáctanos." },
    { question: "¿Qué tiendas online son compatibles?", answer: "Actualmente WooCommerce, Shopify y PrestaShop. También sincronizamos con Dolibarr y Odoo como CRM/ERP." },
    { question: "¿Qué pasa si supero los límites de mi plan?", answer: "Te avisaremos antes de llegar al límite y podrás actualizar tu plan en cualquier momento sin perder datos." },
    { question: "¿Ofrecen soporte técnico?", answer: "Sí, todos los planes incluyen soporte por email. Los planes Professional y Enterprise incluyen soporte prioritario 24/7." },
    { question: "¿Puedo cancelar en cualquier momento?", answer: "Sí, puedes cancelar tu suscripción cuando quieras. No hay permanencia ni penalizaciones por cancelación." },
    { question: "¿Los datos de mis proveedores están seguros?", answer: "Absolutamente. Usamos encriptación TLS en tránsito y en reposo, con copias de seguridad automáticas diarias en servidores europeos." },
  ],
  cta_final: {
    title: "¿Listo para automatizar tu negocio?",
    subtitle: "Únete a cientos de empresas que ya optimizan su gestión de inventario con SyncStock",
    button_text: "Comenzar Prueba Gratuita",
  },
  footer: {
    company_description: "SyncStock es la plataforma líder en sincronización de inventarios para eCommerce B2B.",
    social: { twitter: "", linkedin: "", facebook: "" },
  },
  about: {
    mission: "Nuestra misión es eliminar el trabajo manual en la gestión de inventarios B2B, permitiendo a las empresas centrarse en lo que realmente importa: vender y crecer.",
    story: "Fundada en 2022, SyncStock nació de la frustración de gestionar docenas de proveedores con hojas de cálculo. Hoy ayudamos a más de 500 empresas a automatizar sus catálogos.",
    values: [
      { title: "Automatización", description: "Eliminamos tareas repetitivas para que tu equipo se enfoque en el negocio." },
      { title: "Fiabilidad", description: "Nuestros sistemas funcionan 24/7 con una disponibilidad del 99.9%." },
      { title: "Simplicidad", description: "Potente funcionalidad con una interfaz intuitiva que cualquiera puede usar." },
      { title: "Privacidad", description: "Tus datos son tuyos. Nunca los compartimos ni los usamos para publicidad." },
    ],
    team: [
      { name: "Equipo SyncStock", role: "Desarrolladores & Soporte", description: "Un equipo apasionado por la automatización y el eCommerce B2B." },
    ],
  },
};

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [branding, setBranding] = useState(defaultBranding);
  const [plans, setPlans] = useState(defaultPlans);
  const [content, setContent] = useState(defaultContent);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      return next;
    });
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [brandingRes, plansRes, contentRes] = await Promise.allSettled([
          axios.get(`${API_URL}/api/branding/public`),
          axios.get(`${API_URL}/api/subscriptions/plans/public`),
          axios.get(`${API_URL}/api/landing/content`),
        ]);

        if (brandingRes.status === "fulfilled" && brandingRes.value.data) {
          setBranding(prev => ({ ...prev, ...brandingRes.value.data }));
        }
        if (plansRes.status === "fulfilled" && Array.isArray(plansRes.value.data) && plansRes.value.data.length > 0) {
          setPlans(plansRes.value.data);
        }
        if (contentRes.status === "fulfilled" && contentRes.value.data) {
          setContent(prev => {
            const remote = contentRes.value.data;
            const merged = { ...prev };
            Object.keys(prev).forEach(key => {
              if (remote[key]) merged[key] = remote[key];
            });
            return merged;
          });
        }
      } catch (_) {
        // use defaults
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Update favicon and page title from branding
  useEffect(() => {
    if (branding.favicon_url) {
      let link = document.querySelector("link[rel='icon']");
      if (!link) {
        link = document.createElement("link");
        link.rel = "icon";
        document.head.appendChild(link);
      }
      link.href = branding.favicon_url.startsWith("http") ? branding.favicon_url : `${API_URL}${branding.favicon_url}`;
    }
  }, [branding.favicon_url]);

  return (
    <AppContext.Provider value={{ branding, plans, content, loading, theme, toggleTheme, API_URL, APP_URL }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
