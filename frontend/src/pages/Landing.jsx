import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Zap, Database, Store, Calculator, RefreshCw, Shield, Check,
  ChevronRight, Star, ArrowRight, Menu, X, Play, ChevronDown,
  Layers, BarChart3, Clock, Users, ShoppingCart, ShoppingBag,
  Boxes, Sparkles, Globe, Server, Building2
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const APP_URL = "https://app.sync-stock.com"; // URL de la aplicación

// Icon mapping
const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield,
  Layers, BarChart3, Clock, Users, Star
};

// Platform definitions for the integrations showcase
const INTEGRATION_PLATFORMS = [
  // Tiendas
  { key: "store_woocommerce",       label: "WooCommerce",     FallbackIcon: ShoppingCart, bg: "bg-purple-500/20",  color: "text-purple-300" },
  { key: "store_prestashop",        label: "PrestaShop",      FallbackIcon: ShoppingBag,  bg: "bg-pink-500/20",    color: "text-pink-300"   },
  { key: "store_shopify",           label: "Shopify",         FallbackIcon: Boxes,        bg: "bg-green-500/20",   color: "text-green-300"  },
  { key: "store_wix",               label: "Wix",             FallbackIcon: Sparkles,     bg: "bg-blue-500/20",    color: "text-blue-300"   },
  { key: "store_magento",           label: "Magento",         FallbackIcon: Globe,        bg: "bg-orange-500/20",  color: "text-orange-300" },
  // Marketplaces
  { key: "marketplace_amazon",          label: "Amazon",          initials: "AMZ",  bg: "bg-orange-500/30" },
  { key: "marketplace_google_merchant", label: "Google Merchant", initials: "GM",   bg: "bg-blue-500/30"   },
  { key: "marketplace_ebay",            label: "eBay",            initials: "eBay", bg: "bg-sky-500/30"    },
  { key: "marketplace_facebook_shops",  label: "Meta Shops",      initials: "FB",   bg: "bg-indigo-500/30" },
  { key: "marketplace_zalando",         label: "Zalando",         initials: "ZAL",  bg: "bg-orange-700/30" },
  { key: "marketplace_miravia",         label: "Miravia",         initials: "MIR",  bg: "bg-pink-500/30"   },
  // CRM
  { key: "crm_dolibarr", label: "Dolibarr", FallbackIcon: Building2, bg: "bg-cyan-500/20",   color: "text-cyan-300"   },
  { key: "crm_odoo",     label: "Odoo",     FallbackIcon: Building2, bg: "bg-purple-500/20", color: "text-purple-300" },
  // Proveedores
  { key: "supplier_url", label: "Proveedor URL",      FallbackIcon: Globe,   bg: "bg-blue-500/20",   color: "text-blue-300"   },
  { key: "supplier_ftp", label: "Proveedor FTP/SFTP", FallbackIcon: Server,  bg: "bg-indigo-500/20", color: "text-indigo-300" },
];

const Landing = () => {
  const [content, setContent] = useState(null);
  const [plans, setPlans] = useState([]);
  const [branding, setBranding] = useState({});
  const [icons, setIcons] = useState({});
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [openFaq, setOpenFaq] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contentRes, plansRes, brandingRes, iconsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/landing/content`),
        axios.get(`${BACKEND_URL}/api/subscriptions/plans/public`),
        axios.get(`${BACKEND_URL}/api/branding/public`),
        axios.get(`${BACKEND_URL}/api/icons/public`).catch(() => ({ data: { icons: {} } }))
      ]);

      setContent(contentRes.data);
      setPlans(plansRes.data || []);
      setBranding(brandingRes.data || {});
      setIcons(iconsRes.data.icons || {});
    } catch (error) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  const getCustomIconUrl = (key) => {
    const url = icons[key];
    if (!url) return null;
    return url.startsWith("/") ? `${BACKEND_URL}${url}` : url;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  const getIcon = (iconName) => {
    const Icon = iconMap[iconName] || Zap;
    return Icon;
  };

  // Map CMS feature icon names to managed icon keys (first match wins)
  const FEATURE_ICON_KEY_MAP = {
    Store:     "store_woocommerce",
    Database:  "supplier_url",
    RefreshCw: "supplier_ftp",
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
            <div className="flex items-center gap-3">
              {branding.logo_url ? (
                <img src={branding.logo_url} alt="SyncStock" className="h-8 lg:h-10" />
              ) : (
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <RefreshCw className="w-5 h-5 text-white" />
                </div>
              )}
              <span className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                SyncStock
              </span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-8">
              <a href="#features" className="text-slate-300 hover:text-white transition-colors">
                Características
              </a>
              <a href="#pricing" className="text-slate-300 hover:text-white transition-colors">
                Precios
              </a>
              <a href="#faq" className="text-slate-300 hover:text-white transition-colors">
                FAQ
              </a>
            </div>

            {/* CTA Buttons */}
            <div className="hidden lg:flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-white/10">
                  Iniciar Sesión
                </Button>
              </Link>
              <Link to="/register">
                <Button className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6">
                  Empezar Gratis
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button 
              className="lg:hidden p-2 text-slate-300"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-slate-800 border-t border-white/5">
            <div className="px-4 py-6 space-y-4">
              <a href="#features" className="block text-slate-300 hover:text-white py-2">
                Características
              </a>
              <a href="#pricing" className="block text-slate-300 hover:text-white py-2">
                Precios
              </a>
              <a href="#faq" className="block text-slate-300 hover:text-white py-2">
                FAQ
              </a>
              <div className="pt-4 space-y-3">
                <Link to="/login" className="block">
                  <Button variant="outline" className="w-full border-slate-600 text-white">
                    Iniciar Sesión
                  </Button>
                </Link>
                <Link to="/register" className="block">
                  <Button className="w-full bg-gradient-to-r from-indigo-500 to-purple-600">
                    Empezar Gratis
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 lg:pt-40 pb-20 lg:pb-32 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjIiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-50" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-sm text-slate-300">14 días de prueba gratuita</span>
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                {content?.hero?.title || "Sincroniza tu inventario con un clic"}
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-lg lg:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              {content?.hero?.subtitle || "Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente."}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register">
                <Button size="lg" className="w-full sm:w-auto bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl shadow-2xl shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:scale-105">
                  {content?.hero?.cta_primary || "Empezar Gratis"}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="w-full sm:w-auto border-slate-600 text-white hover:bg-white/5 px-8 py-6 text-lg rounded-xl">
                <Play className="w-5 h-5 mr-2" />
                {content?.hero?.cta_secondary || "Ver Demo"}
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="mt-16 flex flex-wrap items-center justify-center gap-8 text-slate-500">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                <span className="text-sm">Datos encriptados</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                <span className="text-sm">+500 empresas</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                <span className="text-sm">4.9/5 valoración</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {(content?.benefits?.items || [
              { stat: "80%", text: "Menos tiempo en gestión" },
              { stat: "0", text: "Errores manuales" },
              { stat: "24/7", text: "Sincronización automática" },
              { stat: "+500", text: "Empresas confían" }
            ]).map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2">
                  {item.stat}
                </div>
                <div className="text-slate-400">{item.text}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations Showcase */}
      <section className="py-14 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs uppercase tracking-widest text-slate-500 mb-10 font-medium">
            Compatible con las principales plataformas
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 md:gap-6">
            {INTEGRATION_PLATFORMS.map((platform) => {
              const customUrl = getCustomIconUrl(platform.key);
              const FallbackIcon = platform.FallbackIcon;
              return (
                <div
                  key={platform.key}
                  className="flex flex-col items-center gap-2 group"
                  title={platform.label}
                >
                  <div className={`w-12 h-12 rounded-xl ${platform.bg} border border-white/10 flex items-center justify-center group-hover:scale-110 transition-transform`}>
                    {customUrl ? (
                      <img src={customUrl} alt={platform.label} className="w-8 h-8 object-contain" />
                    ) : FallbackIcon ? (
                      <FallbackIcon className={`w-6 h-6 ${platform.color}`} />
                    ) : (
                      <span className="text-white/70 text-xs font-bold leading-none text-center px-1">
                        {platform.initials}
                      </span>
                    )}
                  </div>
                  <span className="text-slate-500 text-xs text-center max-w-[60px] leading-tight group-hover:text-slate-400 transition-colors">
                    {platform.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Todo lo que necesitas para{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                automatizar tu negocio
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Herramientas potentes que trabajan juntas para optimizar tu gestión de inventario
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
            {(content?.features || []).map((feature, idx) => {
              const Icon = getIcon(feature.icon);
              const managedKey = FEATURE_ICON_KEY_MAP[feature.icon];
              const customUrl = managedKey ? getCustomIconUrl(managedKey) : null;
              return (
                <div
                  key={idx}
                  className="group p-6 lg:p-8 rounded-2xl bg-gradient-to-b from-white/[0.05] to-transparent border border-white/5 hover:border-indigo-500/30 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                    {customUrl ? (
                      <img src={customUrl} alt={feature.title} className="w-8 h-8 object-contain" />
                    ) : (
                      <Icon className="w-6 h-6 text-indigo-400" />
                    )}
                  </div>
                  <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                  <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 lg:py-32 bg-gradient-to-b from-transparent via-indigo-950/20 to-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Planes que se adaptan a tu{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                crecimiento
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
              Comienza gratis y escala cuando lo necesites
            </p>

            {/* Billing Toggle */}
            <div className="inline-flex items-center gap-4 p-1.5 bg-white/5 rounded-full border border-white/10">
              <button
                onClick={() => setBillingCycle("monthly")}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                  billingCycle === "monthly" 
                    ? "bg-white text-slate-900" 
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Mensual
              </button>
              <button
                onClick={() => setBillingCycle("yearly")}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                  billingCycle === "yearly" 
                    ? "bg-white text-slate-900" 
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Anual
                <span className="ml-2 text-xs text-green-500">-17%</span>
              </button>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, idx) => {
              const isPopular = plan.name === "Professional";
              const price = billingCycle === "monthly" ? plan.price_monthly : (plan.price_yearly / 12).toFixed(2);
              
              return (
                <div 
                  key={plan.id}
                  className={`relative rounded-2xl p-6 lg:p-8 transition-all duration-300 hover:scale-105 ${
                    isPopular 
                      ? "bg-gradient-to-b from-indigo-500/20 to-purple-500/10 border-2 border-indigo-500/50 shadow-xl shadow-indigo-500/10" 
                      : "bg-white/[0.03] border border-white/10 hover:border-white/20"
                  }`}
                >
                  {isPopular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                      <span className="px-4 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm font-semibold rounded-full">
                        Más Popular
                      </span>
                    </div>
                  )}

                  {plan.trial_days > 0 && (
                    <div className="absolute -top-4 right-4">
                      <span className="px-3 py-1 bg-amber-500 text-white text-xs font-semibold rounded-full">
                        {plan.trial_days} días gratis
                      </span>
                    </div>
                  )}

                  <div className="mb-6">
                    <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                    <p className="text-slate-400 text-sm">{plan.description}</p>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl lg:text-5xl font-bold text-white">
                        {plan.price_monthly === 0 ? "Gratis" : `€${price}`}
                      </span>
                      {plan.price_monthly > 0 && (
                        <span className="text-slate-500">/mes</span>
                      )}
                    </div>
                    {billingCycle === "yearly" && plan.price_monthly > 0 && (
                      <p className="text-sm text-slate-500 mt-1">
                        Facturado anualmente (€{plan.price_yearly})
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features?.map((feature, fidx) => (
                      <li key={fidx} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-slate-300 text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link to="/register" className="block">
                    <Button 
                      className={`w-full py-6 rounded-xl font-semibold transition-all ${
                        isPopular 
                          ? "bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25" 
                          : "bg-white/10 hover:bg-white/20 text-white"
                      }`}
                    >
                      {plan.price_monthly === 0 ? "Comenzar Gratis" : "Elegir Plan"}
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Lo que dicen{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                nuestros clientes
              </span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {(content?.testimonials || []).map((testimonial, idx) => (
              <div 
                key={idx}
                className="p-8 rounded-2xl bg-gradient-to-b from-white/[0.05] to-transparent border border-white/5"
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                  ))}
                </div>
                <p className="text-lg text-slate-300 mb-6 leading-relaxed">"{testimonial.quote}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                    {testimonial.author?.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{testimonial.author}</div>
                    <div className="text-sm text-slate-500">{testimonial.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 lg:py-32 bg-gradient-to-b from-transparent via-slate-800/30 to-transparent">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Preguntas{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Frecuentes
              </span>
            </h2>
          </div>

          <div className="space-y-4">
            {(content?.faq || []).map((item, idx) => (
              <div 
                key={idx}
                className="rounded-xl bg-white/[0.03] border border-white/5 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-white/[0.02] transition-colors"
                >
                  <span className="font-medium text-white">{item.question}</span>
                  <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${openFaq === idx ? "rotate-180" : ""}`} />
                </button>
                {openFaq === idx && (
                  <div className="px-6 pb-5">
                    <p className="text-slate-400 leading-relaxed">{item.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 lg:py-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-12 lg:p-16 rounded-3xl bg-gradient-to-r from-indigo-600 to-purple-600 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4zIj48Y2lyY2xlIGN4PSIyIiBjeT0iMiIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')]" />
            </div>
            
            <div className="relative">
              <h2 className="text-3xl lg:text-5xl font-bold text-white mb-4">
                {content?.cta_final?.title || "¿Listo para automatizar tu negocio?"}
              </h2>
              <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
                {content?.cta_final?.subtitle || "Únete a cientos de empresas que ya optimizan su gestión"}
              </p>
              <Link to="/register">
                <Button size="lg" className="bg-white text-indigo-600 hover:bg-slate-100 px-10 py-6 text-lg rounded-xl font-semibold shadow-2xl hover:scale-105 transition-all">
                  {content?.cta_final?.button_text || "Comenzar Prueba Gratuita"}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <p className="text-white/60 text-sm mt-4">Sin tarjeta de crédito requerida</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">SyncStock</span>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 text-slate-400">
              {(content?.footer?.links || []).map((link, idx) => (
                <a key={idx} href={link.url} className="hover:text-white transition-colors">
                  {link.label}
                </a>
              ))}
            </div>

            <p className="text-slate-500 text-sm">
              © {new Date().getFullYear()} SyncStock. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
