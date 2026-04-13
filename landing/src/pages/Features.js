import { Link } from "react-router-dom";
import {
  Zap, Database, Store, Calculator, RefreshCw, Shield, BarChart3,
  Clock, Globe, Package, TrendingUp, Truck, FileSpreadsheet, Webhook,
  Cpu, Lock, Headphones, Layers, Check, ArrowRight, Building2,
  ShoppingCart, Bell, Settings, CheckCircle2, MessageCircle, LifeBuoy,
  BookOpen, GraduationCap, ShoppingBag, Tag, BadgeDollarSign, Boxes,
  Cloud, Users, Sparkles, Search, Monitor
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";
import { useSEO } from "../hooks/useSEO";

const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield, BarChart3, Clock,
  Globe, Package, TrendingUp, Truck, FileSpreadsheet, Webhook, Cpu, Lock,
  Headphones, Layers, Building2, ShoppingCart, Bell, Settings, MessageCircle,
  LifeBuoy, BookOpen, GraduationCap, ShoppingBag, Tag, BadgeDollarSign, Boxes,
  Cloud, Users, Sparkles, Search, Monitor
};

function Icon({ name, ...props }) {
  const Comp = iconMap[name] || Zap;
  return <Comp {...props} />;
}

const FEATURE_CATEGORIES = [
  {
    title: "Sincronización de datos",
    description: "Mantén todos tus sistemas siempre actualizados sin intervención manual.",
    features: [
      { icon: "Zap", title: "Sincronización automática", description: "Actualiza precios, stock y productos en todas tus tiendas en tiempo real. Configura intervalos personalizados desde cada 15 minutos." },
      { icon: "RefreshCw", title: "Sincronización bidireccional", description: "Los cambios fluyen en ambas direcciones. Pedidos recibidos en WooCommerce se reflejan en tu CRM automáticamente." },
      { icon: "Clock", title: "Historial de cambios", description: "Rastrea cada modificación de precio, stock o atributo con timestamps precisos. Auditoría completa disponible." },
      { icon: "Bell", title: "Alertas en tiempo real", description: "Recibe notificaciones al instante cuando hay cambios significativos de precio, stock bajo o errores de sincronización." },
    ]
  },
  {
    title: "Gestión de proveedores",
    description: "Importa y gestiona catálogos de cualquier proveedor en cualquier formato.",
    features: [
      { icon: "Database", title: "Multi-proveedor", description: "Conecta docenas de proveedores diferentes desde un único panel. Sin límite en planes Enterprise." },
      { icon: "Truck", title: "FTP/SFTP nativo", description: "Conexión directa a servidores FTP y SFTP de tus proveedores con autenticación segura y re-intentos automáticos." },
      { icon: "FileSpreadsheet", title: "CSV, Excel y XML", description: "Importa archivos CSV, XLSX, XLS y XML con mapeo de columnas personalizable. Detección automática de formato." },
      { icon: "Webhook", title: "API y webhooks", description: "Conecta proveedores con API REST. Recibe actualizaciones push mediante webhooks configurables." },
    ]
  },
  {
    title: "Tiendas y canales de venta",
    description: "Publica en 5 plataformas de eCommerce con un solo clic.",
    features: [
      { icon: "ShoppingCart", title: "WooCommerce", description: "Integración profunda con WooCommerce: productos, variantes, precios, stock, imágenes y categorías." },
      { icon: "Boxes", title: "Shopify", description: "Publica y actualiza tu catálogo en Shopify incluyendo metafields, colecciones y variantes de producto." },
      { icon: "ShoppingBag", title: "PrestaShop", description: "Compatibilidad completa con PrestaShop 1.7+ y 8.x con soporte para combinaciones y características." },
      { icon: "Sparkles", title: "Wix eCommerce", description: "Conecta tu tienda Wix para sincronizar productos, precios y stock automáticamente con tu catálogo." },
      { icon: "Globe", title: "Magento", description: "Integración completa con Magento 2.x para gestionar productos, stock y precios en tu tienda." },
      { icon: "Store", title: "Multi-tienda", description: "Gestiona múltiples tiendas de diferentes plataformas desde un único panel. Reglas de precio independientes por tienda." },
    ]
  },
  {
    title: "Precios y márgenes",
    description: "Control total sobre tu política de precios.",
    features: [
      { icon: "Calculator", title: "Reglas de margen", description: "Define márgenes por proveedor, categoría, marca o producto individual. Actualización automática al cambiar el precio base." },
      { icon: "TrendingUp", title: "Historial de precios", description: "Visualiza la evolución del precio de cada producto a lo largo del tiempo con gráficos detallados." },
      { icon: "BarChart3", title: "Análisis de rentabilidad", description: "Calcula automáticamente márgenes brutos y netos incluyendo costes de envío y gestión." },
      { icon: "Package", title: "Catálogos personalizados", description: "Crea catálogos B2B con precios diferenciados para diferentes clientes o canales de distribución." },
    ]
  },
  {
    title: "CRM e integraciones ERP",
    description: "Conecta tu plataforma con 8 sistemas CRM/ERP líderes del mercado.",
    features: [
      { icon: "Building2", title: "Dolibarr", description: "Sincronización completa con Dolibarr: productos, clientes, pedidos y facturas en tiempo real." },
      { icon: "Cpu", title: "Odoo", description: "Integración XML-RPC con Odoo para sincronizar inventario, partners y facturas bidireccionalmente." },
      { icon: "Zap", title: "HubSpot", description: "Conecta con HubSpot para sincronizar productos, contactos y datos de ventas. CRM líder en marketing y ventas." },
      { icon: "Cloud", title: "Salesforce", description: "Integración con Salesforce, el CRM empresarial líder mundial. Sincroniza productos, partners y oportunidades." },
      { icon: "BarChart3", title: "Zoho CRM", description: "Conecta con Zoho CRM para gestionar productos, contactos y pedidos. CRM completo para pymes y empresas." },
      { icon: "TrendingUp", title: "Pipedrive", description: "Sincroniza tu catálogo con Pipedrive, el CRM de ventas más intuitivo. Gestiona productos y deals automáticamente." },
      { icon: "Layers", title: "Monday CRM", description: "Integración con Monday CRM para gestionar tu catálogo dentro del entorno flexible de Monday.com." },
      { icon: "Users", title: "Freshsales", description: "Conecta con Freshsales de Freshworks. CRM inteligente con IA integrada para gestión de ventas y productos." },
    ]
  },
  {
    title: "API y automatizaciones",
    description: "Extiende la plataforma con integraciones personalizadas y automatizaciones.",
    features: [
      { icon: "Settings", title: "API REST propia", description: "Accede a todos tus datos mediante nuestra API REST documentada. Perfecta para integraciones personalizadas." },
      { icon: "Webhook", title: "Webhooks salientes", description: "Notifica a sistemas externos cuando ocurren eventos: nuevos productos, cambios de stock, sincronización completada." },
      { icon: "Search", title: "Google Services", description: "Integración con Google Analytics, Search Console, Tag Manager y Google Ads para monitorizar tu rendimiento." },
      { icon: "Monitor", title: "Dashboard avanzado", description: "Panel de control en tiempo real con métricas, alertas y KPIs para tomar decisiones basadas en datos." },
    ]
  },
  {
    title: "Seguridad y soporte",
    description: "Tu negocio protegido y con soporte cuando lo necesitas.",
    features: [
      { icon: "Shield", title: "Encriptación TLS", description: "Todos los datos en tránsito y en reposo están encriptados con TLS 1.3. Cumplimiento GDPR." },
      { icon: "Lock", title: "Autenticación segura", description: "JWT con expiración configurable, hashing bcrypt y control de acceso por roles (RBAC)." },
      { icon: "Database", title: "Backups automáticos", description: "Copias de seguridad diarias automáticas con retención configurable. Restauración en un clic." },
      { icon: "Headphones", title: "Soporte dedicado", description: "Soporte por email en todos los planes. Soporte prioritario 24/7 en planes Professional y Enterprise." },
    ]
  },
  {
    title: "Soporte técnico",
    description: "Acompañamiento experto en cada paso para que tu negocio nunca se detenga.",
    features: [
      { icon: "LifeBuoy", title: "Centro de ayuda", description: "Base de conocimiento completa con guías paso a paso, tutoriales en vídeo y documentación actualizada para resolver cualquier duda." },
      { icon: "MessageCircle", title: "Chat y email", description: "Contacta con nuestro equipo de soporte por chat en vivo o email. Respuesta garantizada en menos de 2 horas en días laborables." },
      { icon: "GraduationCap", title: "Onboarding personalizado", description: "Sesiones de configuración guiada con un especialista para que tu equipo esté operativo desde el primer día." },
      { icon: "BookOpen", title: "Formación continua", description: "Webinars mensuales, novedades de producto y mejores prácticas para sacar el máximo partido a la plataforma." },
    ]
  },
  {
    title: "Conexión con Marketplaces",
    description: "Publica y sincroniza tu catálogo en más de 10 marketplaces europeos.",
    features: [
      { icon: "ShoppingBag", title: "Amazon", description: "Sincroniza productos, precios y stock con Amazon Seller Central. Gestión automática de listados y actualización en tiempo real." },
      { icon: "Tag", title: "eBay", description: "Publica y actualiza tu catálogo en eBay con sincronización bidireccional de stock, precios y pedidos." },
      { icon: "BadgeDollarSign", title: "Miravia", description: "Conecta con Miravia para gestionar tu catálogo en uno de los marketplaces de mayor crecimiento en Europa." },
      { icon: "Building2", title: "El Corte Inglés", description: "Publica tu catálogo en el marketplace de El Corte Inglés, el gran almacén líder en España." },
      { icon: "Search", title: "idealo y comparadores", description: "Genera feeds para idealo, Kelkoo, Trovaprezzi y PriceRunner. Comparadores de precio líderes en Europa." },
      { icon: "Globe", title: "Google & Bing Shopping", description: "Publica automáticamente en Google Merchant Center y Bing Shopping para maximizar tu visibilidad." },
    ]
  },
];

export default function Features() {
  const { content, theme, APP_URL } = useApp();
  const dark = theme === "dark";

  const allFeatures = content?.features || [];

  useSEO({
    title: "Características",
    description: "Descubre todas las funcionalidades de SyncStock: sincronización automática, gestión de proveedores, integración con WooCommerce, Shopify, PrestaShop, CRM y más de 50 plataformas.",
    canonical: "/caracteristicas",
    structuredData: {
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": "Características de SyncStock",
      "description": "Funcionalidades de la plataforma de gestión de inventario B2B SyncStock",
      "itemListElement": FEATURE_CATEGORIES.slice(0, 5).map((cat, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "name": cat.title,
        "description": cat.description
      }))
    }
  });

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>

      {/* Hero */}
      <section className={cn("py-20 lg:py-28 relative overflow-hidden", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <SectionLabel>Características</SectionLabel>
          <SectionTitle className={cn("mt-4 text-5xl lg:text-6xl", dark ? "text-white" : "")}>
            Una plataforma, <span className="text-indigo-600">todas las funciones</span>
          </SectionTitle>
          <SectionSubtitle className="mt-6 max-w-2xl mx-auto text-lg">
            Todo lo que necesitas para automatizar la gestión de inventario B2B y escalar sin límites.
          </SectionSubtitle>
          <div className="flex flex-col sm:flex-row justify-center gap-4 mt-10">
            <a
              href={`${APP_URL}/#/register`}
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg hover:-translate-y-0.5"
            >
              Empezar gratis <ArrowRight size={18} />
            </a>
            <Link
              to="/precios"
              className={cn(
                "inline-flex items-center justify-center gap-2 px-6 py-3.5 border-2 font-semibold rounded-xl transition-all",
                dark ? "border-slate-700 text-slate-300 hover:border-slate-600" : "border-slate-200 text-slate-700 hover:border-slate-300"
              )}
            >
              Ver precios
            </Link>
          </div>
        </div>
      </section>

      {/* Quick highlights */}
      {allFeatures.length > 0 && (
        <section className={cn("py-12 border-y", dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-slate-50")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {allFeatures.slice(0, 6).map((feat, i) => (
                <div key={i} className="flex flex-col items-center text-center gap-2 p-3">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", dark ? "bg-indigo-950" : "bg-indigo-50")}>
                    <Icon name={feat.icon} size={18} className="text-indigo-600" />
                  </div>
                  <span className={cn("text-xs font-semibold", dark ? "text-slate-300" : "text-slate-700")}>{feat.title}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Feature categories */}
      {FEATURE_CATEGORIES.map((cat, catIdx) => (
        <section key={catIdx} className={cn(
          "py-20 lg:py-24",
          catIdx % 2 === 0
            ? dark ? "bg-slate-950" : "bg-white"
            : dark ? "bg-slate-900" : "bg-slate-50"
        )}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-12 reveal-right">
              <h2 className={cn("text-2xl lg:text-3xl font-bold mb-3", dark ? "text-white" : "text-slate-900")}>
                {cat.title}
              </h2>
              <p className={cn("text-lg", dark ? "text-slate-400" : "text-slate-500")}>{cat.description}</p>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {cat.features.map((feat, i) => (
                <div
                  key={i}
                  className={cn(
                    `reveal-up reveal-delay-${(i + 1) * 100}`,
                    "p-6 rounded-2xl border card-hover",
                    dark ? "bg-slate-800 border-slate-700 hover:border-indigo-500/50" : "bg-white border-slate-100 hover:shadow-md"
                  )}
                >
                  <div className={cn("w-11 h-11 rounded-xl flex items-center justify-center mb-4", dark ? "bg-indigo-950" : "bg-indigo-50")}>
                    <Icon name={feat.icon} size={20} className="text-indigo-600" />
                  </div>
                  <h3 className={cn("font-semibold mb-2", dark ? "text-white" : "text-slate-900")}>{feat.title}</h3>
                  <p className={cn("text-sm leading-relaxed", dark ? "text-slate-400" : "text-slate-500")}>{feat.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ))}

      {/* CTA */}
      <section className="py-20 bg-gradient-to-br from-indigo-600 to-violet-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-5">¿Listo para verlo en acción?</h2>
          <p className="text-indigo-100 mb-8">14 días de prueba gratuita. Sin tarjeta de crédito.</p>
          <a
            href={`${APP_URL}/#/register`}
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-xl hover:-translate-y-0.5"
          >
            Empezar prueba gratuita <ArrowRight size={18} />
          </a>
        </div>
      </section>

    </div>
  );
}
