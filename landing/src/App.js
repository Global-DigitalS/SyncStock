import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import {
  Zap, Database, Store, Calculator, RefreshCw, Shield, Check,
  ChevronRight, Star, ArrowRight, Menu, X, ChevronDown,
  Layers, BarChart3, Clock, Users, Sun, Moon, Globe, Package,
  TrendingUp, Truck, FileSpreadsheet, Webhook, CheckCircle2,
  Building2, ShoppingCart, Settings, Bell, ArrowUpRight, Play,
  Cpu, Lock, Headphones
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "https://api.sync-stock.com";
const APP_URL = process.env.REACT_APP_APP_URL || "https://app.sync-stock.com";

const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield,
  Layers, BarChart3, Clock, Users, Star, Globe, Package,
  TrendingUp, Truck, FileSpreadsheet, Webhook, Cpu, Lock, Headphones
};

// ─── Componentes base ────────────────────────────────────────────────────────

const cn = (...classes) => classes.filter(Boolean).join(" ");

const Button = ({ children, className = "", variant = "primary", size = "md", ...props }) => {
  const base = "inline-flex items-center justify-center font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none rounded-sm";
  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm",
    secondary: "bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 shadow-sm",
    ghost: "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
    dark: "bg-slate-900 text-white hover:bg-slate-800 shadow-sm",
    white: "bg-white text-indigo-600 hover:bg-slate-100 shadow-lg",
  };
  const sizes = {
    sm: "px-4 py-2 text-sm gap-1.5",
    md: "px-5 py-2.5 text-sm gap-2",
    lg: "px-7 py-3.5 text-base gap-2",
    xl: "px-9 py-4 text-lg gap-2.5",
  };
  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
};

const Badge = ({ children, className = "" }) => (
  <span className={cn("inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border", className)}>
    {children}
  </span>
);

// ─── Mockup del dashboard ────────────────────────────────────────────────────

const DashboardMockup = () => (
  <div className="w-full max-w-2xl mx-auto">
    <div className="bg-white rounded-lg border border-slate-200 shadow-2xl overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
        </div>
        <div className="flex-1 mx-4">
          <div className="bg-slate-800 rounded px-3 py-1 text-slate-400 text-xs text-center">
            app.stockhub.pro/dashboard
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded bg-slate-700 flex items-center justify-center">
            <Bell className="w-3 h-3 text-slate-400" />
          </div>
          <div className="w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center">
            <span className="text-white text-[8px] font-bold">U</span>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-36 bg-slate-50 border-r border-slate-200 p-3 hidden sm:block">
          <div className="space-y-0.5">
            {[
              { icon: BarChart3, label: "Dashboard", active: true },
              { icon: Truck, label: "Proveedores" },
              { icon: Package, label: "Productos" },
              { icon: Layers, label: "Catálogos" },
              { icon: Store, label: "Tiendas" },
            ].map(({ icon: Icon, label, active }) => (
              <div key={label} className={cn(
                "flex items-center gap-2 px-2 py-1.5 rounded text-xs",
                active ? "bg-indigo-50 text-indigo-700 font-medium" : "text-slate-500"
              )}>
                <Icon className="w-3 h-3 flex-shrink-0" />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Main */}
        <div className="flex-1 p-4 bg-white">
          {/* Stats row */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              { label: "Productos", value: "12,847", change: "+3.2%", up: true },
              { label: "Sincronizados", value: "11,203", change: "+8.1%", up: true },
              { label: "Tiendas activas", value: "4", change: "WooCommerce", up: null },
            ].map((s) => (
              <div key={s.label} className="bg-slate-50 border border-slate-100 rounded p-2">
                <div className="text-slate-400 text-[10px] mb-0.5">{s.label}</div>
                <div className="text-slate-900 text-sm font-bold font-mono">{s.value}</div>
                {s.up !== null ? (
                  <div className={cn("text-[10px] font-medium", s.up ? "text-emerald-600" : "text-rose-600")}>
                    {s.change}
                  </div>
                ) : (
                  <div className="text-[10px] text-slate-400">{s.change}</div>
                )}
              </div>
            ))}
          </div>

          {/* Table preview */}
          <div className="border border-slate-100 rounded overflow-hidden">
            <div className="bg-slate-50 px-3 py-1.5 flex items-center justify-between">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">Productos recientes</span>
              <div className="w-3 h-3 rounded bg-indigo-500" />
            </div>
            <div className="divide-y divide-slate-50">
              {[
                { name: "Monitor 27\" 4K", price: "€349.99", stock: "87", status: "sync" },
                { name: "Teclado mecánico RGB", price: "€129.00", stock: "203", status: "sync" },
                { name: "Auriculares BT Pro", price: "€89.99", stock: "12", status: "low" },
                { name: "Webcam HD 1080p", price: "€64.00", stock: "0", status: "out" },
              ].map((p) => (
                <div key={p.name} className="px-3 py-1.5 flex items-center gap-2 text-[10px]">
                  <div className="flex-1 text-slate-700 font-medium truncate">{p.name}</div>
                  <div className="text-slate-500 font-mono w-14 text-right">{p.price}</div>
                  <div className="text-slate-400 w-8 text-right">{p.stock}</div>
                  <div className={cn(
                    "w-1.5 h-1.5 rounded-full flex-shrink-0",
                    p.status === "sync" ? "bg-emerald-500" :
                    p.status === "low" ? "bg-amber-500" : "bg-rose-500"
                  )} />
                </div>
              ))}
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-3">
            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
              <span>Sincronización en progreso...</span>
              <span className="text-indigo-600 font-semibold">73%</span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full w-[73%] animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ─── App principal ────────────────────────────────────────────────────────────

function App() {
  const [plans, setPlans] = useState([]);
  const [branding, setBranding] = useState({});
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [openFaq, setOpenFaq] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  const [theme, setTheme] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem("landing-theme") || "light" : "light"
  );

  const isDark = theme === "dark";

  const toggleTheme = useCallback(() => {
    const next = isDark ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("landing-theme", next);
  }, [isDark]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const [brandingRes, plansRes, contentRes] = await Promise.all([
          axios.get(`${API_URL}/api/branding/public`).catch(() => ({ data: {} })),
          axios.get(`${API_URL}/api/subscriptions/plans/public`).catch(() => ({ data: [] })),
          axios.get(`${API_URL}/api/landing/content`).catch(() => ({ data: null })),
        ]);
        setBranding(brandingRes.data || {});
        setPlans(plansRes.data || []);
        setContent(contentRes.data);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Aplicar favicon y título dinámicos
  useEffect(() => {
    if (branding.favicon_url) {
      const url = branding.favicon_url.startsWith("http")
        ? branding.favicon_url
        : `${API_URL}${branding.favicon_url}`;
      let link = document.querySelector("link[rel~='icon']");
      if (!link) { link = document.createElement("link"); link.rel = "icon"; document.head.appendChild(link); }
      link.href = url;
    }
    if (branding.app_name || branding.page_title) {
      document.title = branding.page_title || `${branding.app_name} — Sincronización de Inventario B2B`;
    }
  }, [branding]);

  const getAssetUrl = (url) => {
    if (!url) return null;
    return url.startsWith("http") ? url : `${API_URL}${url}`;
  };

  const navigateTo = (path = "") => { window.location.href = `${APP_URL}${path}`; };

  const appName = branding.app_name || "StockHUB";
  const logoUrl = getAssetUrl(branding.logo_url);

  // Contenido por defecto (fallback si la API no responde)
  const defaultContent = {
    hero: {
      badge: "14 días de prueba gratuita · Sin tarjeta de crédito",
      title: "Sincroniza proveedores, catálogos y tiendas",
      title_accent: "sin esfuerzo manual",
      subtitle: "Conecta tus proveedores FTP, SFTP o URL, gestiona catálogos con márgenes personalizados y publica en WooCommerce, Shopify o PrestaShop automáticamente.",
      cta_primary: "Empezar gratis",
      cta_secondary: "Ver demo",
    },
    stats: [
      { value: "80%", label: "Menos tiempo en gestión de stock" },
      { value: "0", label: "Errores de actualización manual" },
      { value: "24/7", label: "Sincronización automática activa" },
      { value: "+500", label: "Empresas confían en la plataforma" },
    ],
    how_it_works: [
      { step: "01", title: "Conecta tus proveedores", desc: "Añade proveedores vía FTP, SFTP o URL. Importa CSV, XLSX o XML automáticamente con mapeo de columnas inteligente." },
      { step: "02", title: "Gestiona tus catálogos", desc: "Crea catálogos personalizados con reglas de márgenes por categoría, proveedor o producto. Define precios con total flexibilidad." },
      { step: "03", title: "Publica en tus tiendas", desc: "Exporta a WooCommerce, Shopify o PrestaShop con un clic. Sincronización automática cada vez que tu proveedor actualiza." },
    ],
    features: [
      { icon: "RefreshCw", title: "Sincronización automática", desc: "Conecta con FTP, SFTP o URLs públicas. Actualiza precios, stock y descripciones sin intervención manual." },
      { icon: "Calculator", title: "Reglas de márgenes", desc: "Aplica márgenes por categoría, proveedor o producto. Fija precios mínimos, máximos y reglas de redondeo." },
      { icon: "Layers", title: "Multi-catálogo", desc: "Crea catálogos diferenciados para distintos canales, clientes o precios. Cada catálogo con su propia configuración." },
      { icon: "TrendingUp", title: "Historial de precios", desc: "Rastrea la evolución de precios de cada producto. Recibe alertas cuando un proveedor modifica su tarifa." },
      { icon: "Database", title: "Multi-proveedor", desc: "Centraliza catálogos de múltiples proveedores en una sola plataforma. Evita duplicados con detección inteligente." },
      { icon: "BarChart3", title: "Panel de control", desc: "Métricas en tiempo real: productos sincronizados, errores, actividad y estado de todas tus conexiones." },
    ],
    integrations: [
      { name: "WooCommerce", category: "E-commerce" },
      { name: "Shopify", category: "E-commerce" },
      { name: "PrestaShop", category: "E-commerce" },
      { name: "Dolibarr", category: "CRM / ERP" },
      { name: "Odoo", category: "CRM / ERP" },
      { name: "FTP / SFTP", category: "Protocolo" },
      { name: "CSV / XLSX", category: "Formato" },
      { name: "XML / API", category: "Formato" },
      { name: "Stripe", category: "Pagos" },
    ],
    testimonials: [
      { quote: "StockHUB nos ha ahorrado más de 20 horas semanales. Antes gestionábamos el stock a mano entre proveedor y tienda; ahora es automático.", author: "María García", role: "CEO · TechStore Madrid" },
      { quote: "La integración con Dolibarr es perfecta. Nuestros pedidos y el stock siempre están sincronizados sin ningún esfuerzo extra.", author: "Carlos López", role: "Director de Operaciones · ElectroShop" },
      { quote: "Empecé con el plan Starter y en tres meses necesité el Professional. La plataforma creció con mi negocio sin problemas.", author: "Ana Martínez", role: "Fundadora · Hogar & Deco Online" },
    ],
    faq: [
      { q: "¿Cuánto tiempo lleva la configuración inicial?", a: "La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas los datos de tu proveedor (FTP, URL…) y los credenciales de tu tienda." },
      { q: "¿Puedo probar antes de pagar?", a: "Sí. Todos los planes incluyen 14 días de prueba gratuita con acceso completo. No se requiere tarjeta de crédito." },
      { q: "¿Con qué plataformas de e-commerce es compatible?", a: "WooCommerce, Shopify y PrestaShop con sincronización directa. También puedes exportar catálogos en CSV/XLSX para cualquier otra plataforma." },
      { q: "¿Puedo conectar más de un proveedor?", a: "Sí. Cada plan incluye un número de proveedores simultáneos. El plan Professional admite hasta 50; Enterprise es ilimitado." },
      { q: "¿Qué pasa si mi proveedor actualiza el catálogo?", a: "StockHUB detecta los cambios automáticamente y los aplica en tus tiendas según el intervalo de sincronización que configures." },
      { q: "¿Está disponible en español?", a: "Sí, la interfaz completa está en español. El soporte técnico también se ofrece en español." },
    ],
  };

  const c = content || defaultContent;

  if (loading) {
    return (
      <div className={cn("min-h-screen flex items-center justify-center", isDark ? "bg-slate-900" : "bg-slate-50")}>
        <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  const bg = isDark ? "bg-slate-900" : "bg-white";
  const bgAlt = isDark ? "bg-slate-800" : "bg-slate-50";
  const text = isDark ? "text-white" : "text-slate-900";
  const textSub = isDark ? "text-slate-400" : "text-slate-600";
  const textMuted = isDark ? "text-slate-500" : "text-slate-400";
  const border = isDark ? "border-white/10" : "border-slate-200";
  const cardBg = isDark ? "bg-white/[0.04]" : "bg-white";

  return (
    <div className={cn("min-h-screen overflow-x-hidden transition-colors duration-300", bg, text)}>

      {/* ── Navegación ─────────────────────────────────────────────────────── */}
      <nav className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? cn("border-b shadow-sm", isDark ? "bg-slate-900/95 border-white/10" : "bg-white/95 border-slate-200")
          : "bg-transparent border-transparent"
      )}>
        <div style={{ backdropFilter: scrolled ? "blur(16px)" : "none" }}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16 lg:h-18">

              {/* Logo */}
              <a href="#hero" className="flex items-center gap-2.5 flex-shrink-0">
                {logoUrl ? (
                  <img src={logoUrl} alt={appName} className="h-8 object-contain" />
                ) : (
                  <div className="w-8 h-8 bg-indigo-600 rounded-sm flex items-center justify-center flex-shrink-0">
                    <RefreshCw className="w-4 h-4 text-white" />
                  </div>
                )}
                <span className={cn("text-lg font-bold", text)}>{appName}</span>
              </a>

              {/* Nav desktop */}
              <div className="hidden lg:flex items-center gap-7 text-sm">
                {[
                  { label: "Características", href: "#features" },
                  { label: "Cómo funciona", href: "#how" },
                  { label: "Integraciones", href: "#integrations" },
                  { label: "Precios", href: "#pricing" },
                  { label: "FAQ", href: "#faq" },
                ].map(({ label, href }) => (
                  <a key={href} href={href} className={cn("transition-colors hover:text-indigo-600", textSub)}>
                    {label}
                  </a>
                ))}
              </div>

              {/* CTA + toggle */}
              <div className="hidden lg:flex items-center gap-3">
                <button
                  onClick={toggleTheme}
                  className={cn("p-2 rounded-sm transition-colors", isDark ? "text-slate-400 hover:text-white hover:bg-white/10" : "text-slate-500 hover:text-slate-900 hover:bg-slate-100")}
                  aria-label="Cambiar tema"
                >
                  {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>
                <Button variant="ghost" size="sm" onClick={() => navigateTo("/#/login")}>
                  Iniciar sesión
                </Button>
                <Button variant="primary" size="sm" onClick={() => navigateTo("/#/register")}>
                  Empezar gratis
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>

              {/* Hamburguesa móvil */}
              <div className="flex lg:hidden items-center gap-2">
                <button onClick={toggleTheme} className={cn("p-2", textSub)}>
                  {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className={cn("p-2", textSub)}
                  aria-label="Menú"
                >
                  {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Menú móvil */}
        {mobileMenuOpen && (
          <div className={cn("lg:hidden border-t", isDark ? "bg-slate-900 border-white/10" : "bg-white border-slate-200")}>
            <div className="px-4 py-5 space-y-1">
              {[
                { label: "Características", href: "#features" },
                { label: "Cómo funciona", href: "#how" },
                { label: "Integraciones", href: "#integrations" },
                { label: "Precios", href: "#pricing" },
                { label: "FAQ", href: "#faq" },
              ].map(({ label, href }) => (
                <a
                  key={href}
                  href={href}
                  className={cn("block py-2.5 text-sm transition-colors hover:text-indigo-600", textSub)}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {label}
                </a>
              ))}
              <div className="pt-4 space-y-2">
                <Button variant="secondary" size="md" className="w-full justify-center" onClick={() => navigateTo("/#/login")}>
                  Iniciar sesión
                </Button>
                <Button variant="primary" size="md" className="w-full justify-center" onClick={() => navigateTo("/#/register")}>
                  Empezar gratis <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <section id="hero" className="relative pt-28 lg:pt-36 pb-20 lg:pb-28 overflow-hidden">
        {/* Fondo decorativo */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className={cn("absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full blur-3xl opacity-20", isDark ? "bg-indigo-500" : "bg-indigo-400")} />
          <div className={cn("absolute top-1/2 -left-40 w-[400px] h-[400px] rounded-full blur-3xl opacity-10", isDark ? "bg-purple-500" : "bg-purple-400")} />
          {/* Grid pattern */}
          <div className="absolute inset-0 opacity-[0.03]"
            style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%236366f1' fill-opacity='1'%3E%3Cpath d='M0 40L40 0H20L0 20M40 40V20L20 40'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }} />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">

            {/* Columna izquierda */}
            <div className="animate-fade-in">
              {/* Badge */}
              <div className="mb-6">
                <Badge className={cn("border", isDark ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-300" : "bg-indigo-50 border-indigo-100 text-indigo-700")}>
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                  </span>
                  {c.hero?.badge || defaultContent.hero.badge}
                </Badge>
              </div>

              {/* Título */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] mb-6" style={{ fontFamily: "Manrope, sans-serif" }}>
                {c.hero?.title || defaultContent.hero.title}{" "}
                <span className="text-indigo-600">
                  {c.hero?.title_accent || defaultContent.hero.title_accent}
                </span>
              </h1>

              <p className={cn("text-lg leading-relaxed mb-8 max-w-xl", textSub)}>
                {c.hero?.subtitle || defaultContent.hero.subtitle}
              </p>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-3 mb-10">
                <Button variant="primary" size="lg" onClick={() => navigateTo("/#/register")}>
                  {c.hero?.cta_primary || "Empezar gratis"}
                  <ArrowRight className="w-5 h-5" />
                </Button>
                <Button variant={isDark ? "ghost" : "secondary"} size="lg" onClick={() => navigateTo("/#/login")}>
                  <Play className="w-4 h-4" />
                  {c.hero?.cta_secondary || "Ver demo"}
                </Button>
              </div>

              {/* Trust */}
              <div className={cn("flex flex-wrap gap-5 text-sm", textMuted)}>
                <div className="flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  <span>Datos encriptados</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-indigo-500" />
                  <span>+500 empresas</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Star className="w-4 h-4 text-amber-400" />
                  <span>4.9/5 valoración</span>
                </div>
              </div>
            </div>

            {/* Columna derecha — mockup */}
            <div className="animate-slide-up lg:order-last">
              <DashboardMockup />
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ──────────────────────────────────────────────────────────── */}
      <section className={cn("py-14 border-y", isDark ? "bg-white/[0.02] border-white/10" : "bg-slate-50 border-slate-200")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            {(c.stats || defaultContent.stats).map((s, i) => (
              <div key={i}>
                <div className="text-3xl lg:text-4xl font-bold text-indigo-600 mb-1 font-mono" style={{ fontFamily: "Manrope, sans-serif" }}>
                  {s.value}
                </div>
                <div className={cn("text-sm", textSub)}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Cómo funciona ──────────────────────────────────────────────────── */}
      <section id="how" className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">Proceso</p>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
              Empieza a sincronizar en{" "}
              <span className="text-indigo-600">3 pasos</span>
            </h2>
            <p className={cn("text-lg max-w-2xl mx-auto", textSub)}>
              Sin instalaciones complicadas ni técnicos. Configura y olvídate.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Línea conectora */}
            <div className="hidden md:block absolute top-10 left-[calc(16.6%+2rem)] right-[calc(16.6%+2rem)] h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent" />

            {(c.how_it_works || defaultContent.how_it_works).map((step, i) => (
              <div key={i} className="relative text-center">
                <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 relative">
                  <span className="text-2xl font-bold text-white font-mono">{step.step}</span>
                  {i < 2 && (
                    <div className="hidden md:block absolute -right-[2.5rem] top-1/2 -translate-y-1/2">
                      <ChevronRight className="w-5 h-5 text-indigo-300" />
                    </div>
                  )}
                </div>
                <h3 className={cn("text-xl font-semibold mb-3", text)}>{step.title}</h3>
                <p className={cn("text-sm leading-relaxed max-w-xs mx-auto", textSub)}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Características ────────────────────────────────────────────────── */}
      <section id="features" className={cn("py-20 lg:py-28 border-y", isDark ? "border-white/10" : "border-slate-100")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">Funcionalidades</p>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
              Todo lo que necesita tu negocio{" "}
              <span className="text-indigo-600">en una plataforma</span>
            </h2>
            <p className={cn("text-lg max-w-2xl mx-auto", textSub)}>
              Herramientas diseñadas para distribuidores, mayoristas y tiendas online que trabajan con múltiples proveedores.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {(c.features || defaultContent.features).map((f, i) => {
              const Icon = iconMap[f.icon] || Zap;
              return (
                <div key={i} className={cn(
                  "group p-6 rounded-sm border transition-all duration-200 hover:border-indigo-300 hover:shadow-md",
                  isDark ? "border-white/10 bg-white/[0.03] hover:bg-white/[0.05]" : "border-slate-200 bg-white hover:bg-slate-50/50"
                )}>
                  <div className={cn("w-10 h-10 rounded-sm flex items-center justify-center mb-4 transition-colors group-hover:bg-indigo-600",
                    isDark ? "bg-indigo-500/20" : "bg-indigo-50"
                  )}>
                    <Icon className={cn("w-5 h-5 transition-colors group-hover:text-white", isDark ? "text-indigo-400" : "text-indigo-600")} />
                  </div>
                  <h3 className={cn("font-semibold mb-2", text)}>{f.title}</h3>
                  <p className={cn("text-sm leading-relaxed", textSub)}>{f.desc || f.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Integraciones ──────────────────────────────────────────────────── */}
      <section id="integrations" className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">Integraciones</p>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
              Conecta con tu stack actual
            </h2>
            <p className={cn("text-lg max-w-xl mx-auto", textSub)}>
              Compatible con las principales plataformas de e-commerce, ERP y CRM del mercado.
            </p>
          </div>

          <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-10">
            {(c.integrations || defaultContent.integrations).map((intg, i) => (
              <div key={i} className={cn(
                "flex flex-col items-center justify-center gap-2 p-4 rounded-sm border text-center transition-all duration-200 hover:border-indigo-300 hover:shadow-sm cursor-default",
                isDark ? "border-white/10 bg-white/[0.03] hover:bg-white/[0.05]" : "border-slate-200 bg-white hover:bg-slate-50"
              )}>
                <div className={cn("w-8 h-8 rounded-sm flex items-center justify-center", isDark ? "bg-indigo-500/20" : "bg-indigo-50")}>
                  <Globe className={cn("w-4 h-4", isDark ? "text-indigo-400" : "text-indigo-600")} />
                </div>
                <div>
                  <div className={cn("text-sm font-semibold", text)}>{intg.name}</div>
                  <div className={cn("text-xs mt-0.5", textMuted)}>{intg.category}</div>
                </div>
              </div>
            ))}
            {/* Más integraciones */}
            <div className={cn(
              "flex flex-col items-center justify-center gap-2 p-4 rounded-sm border text-center border-dashed",
              isDark ? "border-white/10" : "border-slate-200"
            )}>
              <div className={cn("w-8 h-8 rounded-sm flex items-center justify-center", isDark ? "bg-white/5" : "bg-slate-50")}>
                <ArrowUpRight className={cn("w-4 h-4", textMuted)} />
              </div>
              <div className={cn("text-xs", textMuted)}>Y más…</div>
            </div>
          </div>

          {/* Highlight features de integraciones */}
          <div className="grid md:grid-cols-3 gap-4 mt-8">
            {[
              { icon: Cpu, title: "Conexión directa", desc: "API nativa con WooCommerce, Shopify y PrestaShop. Sin plugins adicionales." },
              { icon: Lock, title: "Seguridad empresarial", desc: "Credenciales cifradas. Tokens OAuth y API Keys almacenados de forma segura." },
              { icon: Headphones, title: "Soporte técnico", desc: "Asistencia en español para configurar tus integraciones desde el primer día." },
            ].map(({ icon: Icon, title, desc }, i) => (
              <div key={i} className={cn("flex items-start gap-4 p-5 rounded-sm border", isDark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-slate-50")}>
                <div className={cn("w-9 h-9 rounded-sm flex items-center justify-center flex-shrink-0", isDark ? "bg-indigo-500/20" : "bg-indigo-100")}>
                  <Icon className={cn("w-4 h-4", isDark ? "text-indigo-400" : "text-indigo-600")} />
                </div>
                <div>
                  <div className={cn("font-semibold text-sm mb-1", text)}>{title}</div>
                  <div className={cn("text-xs leading-relaxed", textSub)}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Precios ────────────────────────────────────────────────────────── */}
      <section id="pricing" className={cn("py-20 lg:py-28 border-y", isDark ? "bg-white/[0.02] border-white/10" : "bg-slate-50 border-slate-200")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">Precios</p>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
              Planes que crecen contigo
            </h2>
            <p className={cn("text-lg max-w-xl mx-auto mb-8", textSub)}>
              Comienza gratis y escala cuando lo necesites. Sin permanencia.
            </p>

            {/* Toggle facturación */}
            <div className={cn("inline-flex items-center p-1 rounded-sm border gap-1", isDark ? "bg-white/5 border-white/10" : "bg-white border-slate-200")}>
              {[
                { key: "monthly", label: "Mensual" },
                { key: "yearly", label: "Anual", badge: "−17%" },
              ].map(({ key, label, badge }) => (
                <button
                  key={key}
                  onClick={() => setBillingCycle(key)}
                  className={cn(
                    "px-5 py-2 text-sm font-medium rounded-sm transition-all flex items-center gap-2",
                    billingCycle === key
                      ? "bg-indigo-600 text-white shadow-sm"
                      : cn("hover:opacity-80", textSub)
                  )}
                >
                  {label}
                  {badge && <span className={cn("text-xs font-semibold", billingCycle === key ? "text-indigo-200" : "text-emerald-500")}>{badge}</span>}
                </button>
              ))}
            </div>
          </div>

          {plans.length > 0 ? (
            <div className={cn(
              "grid gap-5",
              plans.length === 1 ? "max-w-sm mx-auto" :
              plans.length === 2 ? "md:grid-cols-2 max-w-3xl mx-auto" :
              plans.length === 3 ? "md:grid-cols-3" :
              "md:grid-cols-2 lg:grid-cols-4"
            )}>
              {plans.map((plan) => {
                const isPopular = plan.name === "Professional" || plan.highlighted;
                const price = billingCycle === "monthly"
                  ? plan.price_monthly
                  : plan.price_yearly
                    ? (plan.price_yearly / 12).toFixed(2)
                    : plan.price_monthly;
                const isFree = plan.price_monthly === 0;
                return (
                  <div
                    key={plan.id}
                    className={cn(
                      "relative flex flex-col rounded-sm border transition-all duration-200",
                      isPopular
                        ? "border-indigo-500 shadow-xl shadow-indigo-500/15 scale-[1.02]"
                        : isDark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white"
                    )}
                  >
                    {isPopular && (
                      <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                        <span className="bg-indigo-600 text-white text-xs font-bold px-4 py-1 rounded-full">
                          Más popular
                        </span>
                      </div>
                    )}

                    <div className={cn("p-6 border-b flex-1", isDark ? "border-white/10" : "border-slate-100", isPopular && "bg-indigo-600/5")}>
                      <div className="mb-4">
                        <h3 className={cn("text-lg font-bold mb-1", text)}>{plan.name}</h3>
                        <p className={cn("text-sm", textSub)}>{plan.description}</p>
                      </div>

                      <div className="mb-5">
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-bold font-mono" style={{ fontFamily: "Manrope, sans-serif" }}>
                            {isFree ? "Gratis" : `€${price}`}
                          </span>
                          {!isFree && <span className={cn("text-sm", textMuted)}>/mes</span>}
                        </div>
                        {billingCycle === "yearly" && !isFree && plan.price_yearly && (
                          <p className={cn("text-xs mt-1", textMuted)}>Facturado anualmente (€{plan.price_yearly})</p>
                        )}
                        {plan.trial_days > 0 && (
                          <p className="text-xs text-emerald-600 font-medium mt-1">
                            {plan.trial_days} días de prueba gratuita
                          </p>
                        )}
                      </div>

                      <ul className="space-y-2.5">
                        {(plan.features || []).map((feat, fi) => (
                          <li key={fi} className="flex items-start gap-2.5">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                            <span className={cn("text-sm", textSub)}>{feat}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-5">
                      <Button
                        variant={isPopular ? "primary" : isDark ? "ghost" : "secondary"}
                        size="md"
                        className="w-full justify-center"
                        onClick={() => navigateTo("/#/register")}
                      >
                        {isFree ? "Empezar gratis" : "Elegir plan"}
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Fallback si no hay planes de la API */
            <div className="grid md:grid-cols-3 gap-5 max-w-5xl mx-auto">
              {[
                {
                  name: "Starter", price: "29", desc: "Para tiendas que empiezan a crecer.", popular: false,
                  features: ["3 proveedores", "1.000 productos", "1 tienda", "Sincronización cada 12h", "Soporte por email"]
                },
                {
                  name: "Professional", price: "79", desc: "Para negocios con múltiples canales.", popular: true,
                  features: ["15 proveedores", "10.000 productos", "5 tiendas", "Sincronización cada 1h", "CRM (Dolibarr / Odoo)", "Historial de precios", "Soporte prioritario"]
                },
                {
                  name: "Enterprise", price: "199", desc: "Para operaciones a gran escala.", popular: false,
                  features: ["Proveedores ilimitados", "Productos ilimitados", "Tiendas ilimitadas", "Sincronización en tiempo real", "API personalizada", "SLA garantizado", "Soporte dedicado"]
                },
              ].map((plan) => (
                <div
                  key={plan.name}
                  className={cn(
                    "relative flex flex-col rounded-sm border transition-all duration-200",
                    plan.popular
                      ? "border-indigo-500 shadow-xl shadow-indigo-500/15 scale-[1.02]"
                      : isDark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white"
                  )}
                >
                  {plan.popular && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="bg-indigo-600 text-white text-xs font-bold px-4 py-1 rounded-full">Más popular</span>
                    </div>
                  )}
                  <div className={cn("p-6 border-b flex-1", isDark ? "border-white/10" : "border-slate-100", plan.popular && "bg-indigo-600/5")}>
                    <div className="mb-4">
                      <h3 className={cn("text-lg font-bold mb-1", text)}>{plan.name}</h3>
                      <p className={cn("text-sm", textSub)}>{plan.desc}</p>
                    </div>
                    <div className="mb-5">
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-bold font-mono">€{billingCycle === "yearly" ? (parseFloat(plan.price) * 0.83).toFixed(0) : plan.price}</span>
                        <span className={cn("text-sm", textMuted)}>/mes</span>
                      </div>
                      <p className="text-xs text-emerald-600 font-medium mt-1">14 días de prueba gratuita</p>
                    </div>
                    <ul className="space-y-2.5">
                      {plan.features.map((f, fi) => (
                        <li key={fi} className="flex items-start gap-2.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span className={cn("text-sm", textSub)}>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-5">
                    <Button
                      variant={plan.popular ? "primary" : isDark ? "ghost" : "secondary"}
                      size="md"
                      className="w-full justify-center"
                      onClick={() => navigateTo("/#/register")}
                    >
                      Elegir plan <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Nota al pie de precios */}
          <p className={cn("text-center text-sm mt-8", textMuted)}>
            Todos los planes incluyen 14 días de prueba gratuita · Sin tarjeta de crédito · Cancela cuando quieras
          </p>
        </div>
      </section>

      {/* ── Testimonios ────────────────────────────────────────────────────── */}
      <section className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">Testimonios</p>
            <h2 className="text-3xl lg:text-4xl font-bold mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
              Lo que dicen{" "}
              <span className="text-indigo-600">nuestros clientes</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-5">
            {(c.testimonials || defaultContent.testimonials).map((t, i) => (
              <div key={i} className={cn(
                "flex flex-col p-6 rounded-sm border",
                isDark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white"
              )}>
                <div className="flex gap-1 mb-4">
                  {Array(5).fill(0).map((_, j) => (
                    <Star key={j} className="w-4 h-4 text-amber-400 fill-amber-400" />
                  ))}
                </div>
                <p className={cn("text-sm leading-relaxed flex-1 mb-5", textSub)}>"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    {t.author?.charAt(0)}
                  </div>
                  <div>
                    <div className={cn("text-sm font-semibold", text)}>{t.author}</div>
                    <div className={cn("text-xs", textMuted)}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ────────────────────────────────────────────────────────────── */}
      <section id="faq" className={cn("py-20 lg:py-28 border-y", isDark ? "bg-white/[0.02] border-white/10" : "bg-slate-50 border-slate-200")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <p className="text-indigo-600 text-sm font-semibold uppercase tracking-widest mb-3">FAQ</p>
            <h2 className="text-3xl lg:text-4xl font-bold" style={{ fontFamily: "Manrope, sans-serif" }}>
              Preguntas frecuentes
            </h2>
          </div>

          <div className="space-y-2">
            {(c.faq || defaultContent.faq).map((item, i) => {
              const q = item.q || item.question;
              const a = item.a || item.answer;
              const isOpen = openFaq === i;
              return (
                <div key={i} className={cn("rounded-sm border overflow-hidden", isDark ? "border-white/10 bg-white/[0.03]" : "border-slate-200 bg-white")}>
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className={cn(
                      "w-full flex items-center justify-between gap-4 px-5 py-4 text-left transition-colors",
                      isDark ? "hover:bg-white/5" : "hover:bg-slate-50"
                    )}
                  >
                    <span className={cn("font-medium text-sm", text)}>{q}</span>
                    <ChevronDown className={cn("w-4 h-4 flex-shrink-0 transition-transform text-indigo-500", isOpen && "rotate-180")} />
                  </button>
                  {isOpen && (
                    <div className={cn("px-5 pb-4 border-t", isDark ? "border-white/5" : "border-slate-100")}>
                      <p className={cn("text-sm leading-relaxed pt-3", textSub)}>{a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-8 text-center">
            <p className={cn("text-sm", textMuted)}>
              ¿No encuentras tu respuesta?{" "}
              <button onClick={() => navigateTo("/#/register")} className="text-indigo-600 hover:underline font-medium">
                Contáctanos
              </button>
            </p>
          </div>
        </div>
      </section>

      {/* ── CTA Final ──────────────────────────────────────────────────────── */}
      <section className="py-20 lg:py-28">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative bg-indigo-600 rounded-sm overflow-hidden p-12 lg:p-16 text-center">
            {/* Pattern de fondo */}
            <div className="absolute inset-0 opacity-10"
              style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23fff' fill-opacity='0.4'%3E%3Ccircle cx='2' cy='2' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }} />
            <div className="absolute top-0 right-0 w-72 h-72 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

            <div className="relative">
              <h2 className="text-3xl lg:text-5xl font-bold text-white mb-4" style={{ fontFamily: "Manrope, sans-serif" }}>
                {c.cta_final?.title || "¿Listo para automatizar tu negocio?"}
              </h2>
              <p className="text-indigo-200 text-lg mb-8 max-w-2xl mx-auto">
                {c.cta_final?.subtitle || "Únete a cientos de empresas que ya gestionan su inventario con StockHUB."}
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <Button variant="white" size="xl" onClick={() => navigateTo("/#/register")}>
                  {c.cta_final?.button_text || "Comenzar prueba gratuita"}
                  <ArrowRight className="w-5 h-5" />
                </Button>
                <Button
                  size="xl"
                  className="text-indigo-100 border-2 border-white/30 hover:border-white/60 hover:bg-white/5 rounded-sm"
                  onClick={() => navigateTo("/#/login")}
                >
                  Ya tengo cuenta
                </Button>
              </div>
              <p className="text-indigo-300 text-sm mt-5">14 días gratis · Sin tarjeta de crédito · Cancela cuando quieras</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className={cn("border-t py-12", isDark ? "border-white/10 bg-slate-900" : "border-slate-200 bg-slate-50")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-10">
            {/* Marca */}
            <div className="col-span-2 md:col-span-1 lg:col-span-2">
              <div className="flex items-center gap-2.5 mb-3">
                {logoUrl ? (
                  <img src={logoUrl} alt={appName} className="h-7 object-contain" />
                ) : (
                  <div className="w-7 h-7 bg-indigo-600 rounded-sm flex items-center justify-center">
                    <RefreshCw className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
                <span className={cn("font-bold", text)}>{appName}</span>
              </div>
              <p className={cn("text-sm max-w-xs leading-relaxed", textMuted)}>
                Plataforma SaaS B2B para sincronización de catálogos de proveedores y gestión multi-tienda.
              </p>
            </div>

            {/* Producto */}
            <div>
              <h4 className={cn("text-sm font-semibold mb-3", text)}>Producto</h4>
              <ul className={cn("space-y-2 text-sm", textMuted)}>
                {[
                  { label: "Características", href: "#features" },
                  { label: "Integraciones", href: "#integrations" },
                  { label: "Precios", href: "#pricing" },
                  { label: "Changelog", href: "#" },
                ].map(({ label, href }) => (
                  <li key={label}>
                    <a href={href} className="hover:text-indigo-600 transition-colors">{label}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Recursos */}
            <div>
              <h4 className={cn("text-sm font-semibold mb-3", text)}>Recursos</h4>
              <ul className={cn("space-y-2 text-sm", textMuted)}>
                {[
                  { label: "Documentación", href: "#" },
                  { label: "API Reference", href: "#" },
                  { label: "Blog", href: "#" },
                  { label: "FAQ", href: "#faq" },
                ].map(({ label, href }) => (
                  <li key={label}>
                    <a href={href} className="hover:text-indigo-600 transition-colors">{label}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Empresa */}
            <div>
              <h4 className={cn("text-sm font-semibold mb-3", text)}>Empresa</h4>
              <ul className={cn("space-y-2 text-sm", textMuted)}>
                {[
                  { label: "Acerca de", href: "#" },
                  { label: "Privacidad", href: "#" },
                  { label: "Términos", href: "#" },
                  { label: "Contacto", href: "#" },
                ].map(({ label, href }) => (
                  <li key={label}>
                    <a href={href} className="hover:text-indigo-600 transition-colors">{label}</a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className={cn("flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t text-sm", isDark ? "border-white/10" : "border-slate-200", textMuted)}>
            <p>© {new Date().getFullYear()} {appName}. Todos los derechos reservados.</p>
            <div className="flex items-center gap-4">
              <button onClick={() => navigateTo("/#/login")} className="hover:text-indigo-600 transition-colors">
                Acceder
              </button>
              <button onClick={() => navigateTo("/#/register")} className="hover:text-indigo-600 transition-colors font-medium text-indigo-600">
                Empezar gratis →
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
