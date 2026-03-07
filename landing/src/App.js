import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Zap, Database, Store, Calculator, RefreshCw, Shield, Check, 
  ChevronRight, Star, ArrowRight, Menu, X, Play, ChevronDown,
  Layers, BarChart3, Clock, Users
} from "lucide-react";

// Configuration
const API_URL = process.env.REACT_APP_API_URL || "https://api.sync-stock.com";
const APP_URL = process.env.REACT_APP_APP_URL || "https://app.sync-stock.com";

// Icon mapping
const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield, 
  Layers, BarChart3, Clock, Users, Star
};

// Button Component
const Button = ({ children, className = "", variant = "default", size = "default", ...props }) => {
  const baseStyles = "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";
  
  const variants = {
    default: "btn-primary",
    outline: "border-2 border-slate-600 text-white hover:bg-white/5",
    ghost: "text-slate-300 hover:text-white hover:bg-white/10",
  };
  
  const sizes = {
    default: "px-6 py-3 text-sm",
    lg: "px-8 py-4 text-base",
    sm: "px-4 py-2 text-sm",
  };
  
  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

function App() {
  const [content, setContent] = useState(null);
  const [plans, setPlans] = useState([]);
  const [branding, setBranding] = useState({});
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [openFaq, setOpenFaq] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contentRes, plansRes, brandingRes] = await Promise.all([
        axios.get(`${API_URL}/api/landing/content`).catch(() => ({ data: null })),
        axios.get(`${API_URL}/api/subscriptions/plans/public`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/branding/public`).catch(() => ({ data: {} }))
      ]);
      
      setContent(contentRes.data);
      setPlans(plansRes.data || []);
      setBranding(brandingRes.data || {});
    } catch (error) {
      console.error("Error loading landing data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full spinner" />
      </div>
    );
  }

  const getIcon = (iconName) => {
    const Icon = iconMap[iconName] || Zap;
    return Icon;
  };

  const navigateToApp = (path = "") => {
    window.location.href = `${APP_URL}/#${path}`;
  };

  // Default content if API doesn't return data
  const defaultContent = {
    hero: {
      title: "Sincroniza tu inventario con un clic",
      subtitle: "Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente.",
      cta_primary: "Empezar Gratis",
      cta_secondary: "Ver Demo"
    },
    benefits: {
      items: [
        { stat: "80%", text: "Menos tiempo en gestión" },
        { stat: "0", text: "Errores manuales" },
        { stat: "24/7", text: "Sincronización automática" },
        { stat: "+500", text: "Empresas confían" }
      ]
    },
    features: [
      { icon: "RefreshCw", title: "Sincronización Automática", description: "Actualiza precios, stock y productos desde tus proveedores sin intervención manual." },
      { icon: "Database", title: "Gestión de Catálogos", description: "Organiza productos en catálogos personalizados con reglas de precios y márgenes." },
      { icon: "Store", title: "Exportación WooCommerce", description: "Publica productos directamente en tu tienda WooCommerce con un clic." },
      { icon: "Calculator", title: "Cálculo de Márgenes", description: "Aplica reglas de precios automáticas según categoría, proveedor o producto." },
      { icon: "Layers", title: "Multi-proveedor", description: "Conecta múltiples proveedores y centraliza toda tu gestión de inventario." },
      { icon: "Shield", title: "Seguridad Empresarial", description: "Datos encriptados y backups automáticos para proteger tu información." }
    ],
    testimonials: [
      { quote: "SyncStock nos ha ahorrado más de 20 horas semanales en gestión de inventario. Increíble.", author: "María García", role: "CEO, TechStore" },
      { quote: "La sincronización con Dolibarr funciona perfectamente. Nuestro stock siempre está actualizado.", author: "Carlos López", role: "Director, ElectroShop" }
    ],
    faq: [
      { question: "¿Cuánto tiempo tarda la configuración inicial?", answer: "La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas los datos de acceso de tu proveedor y tu tienda WooCommerce." },
      { question: "¿Puedo probar antes de pagar?", answer: "¡Por supuesto! Ofrecemos 14 días de prueba gratuita con todas las funcionalidades premium." },
      { question: "¿Qué pasa si necesito más proveedores?", answer: "Puedes actualizar tu plan en cualquier momento desde tu panel de control. El cambio es inmediato." }
    ],
    cta_final: {
      title: "¿Listo para automatizar tu negocio?",
      subtitle: "Únete a cientos de empresas que ya optimizan su gestión",
      button_text: "Comenzar Prueba Gratuita"
    }
  };

  const displayContent = content || defaultContent;

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
                {branding.app_name || "SyncStock"}
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
              <Button variant="ghost" onClick={() => navigateToApp("/login")}>
                Iniciar Sesión
              </Button>
              <Button onClick={() => navigateToApp("/register")}>
                Empezar Gratis
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <button 
              className="lg:hidden p-2 text-slate-300"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-slate-800 border-t border-white/5">
            <div className="px-4 py-6 space-y-4">
              <a href="#features" className="block text-slate-300 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>
                Características
              </a>
              <a href="#pricing" className="block text-slate-300 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>
                Precios
              </a>
              <a href="#faq" className="block text-slate-300 hover:text-white py-2" onClick={() => setMobileMenuOpen(false)}>
                FAQ
              </a>
              <div className="pt-4 space-y-3">
                <Button variant="outline" className="w-full" onClick={() => navigateToApp("/login")}>
                  Iniciar Sesión
                </Button>
                <Button className="w-full" onClick={() => navigateToApp("/register")}>
                  Empezar Gratis
                </Button>
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
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full mb-8 animate-fade-in">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-sm text-slate-300">14 días de prueba gratuita</span>
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight animate-slide-up" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                {displayContent.hero?.title}
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-lg lg:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed animate-slide-up" style={{ animationDelay: '0.1s' }}>
              {displayContent.hero?.subtitle}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Button size="lg" onClick={() => navigateToApp("/register")} className="w-full sm:w-auto text-lg rounded-xl shadow-2xl">
                {displayContent.hero?.cta_primary || "Empezar Gratis"}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg rounded-xl">
                <Play className="w-5 h-5 mr-2" />
                {displayContent.hero?.cta_secondary || "Ver Demo"}
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
            {(displayContent.benefits?.items || []).map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  {item.stat}
                </div>
                <div className="text-slate-400">{item.text}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
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
            {(displayContent.features || []).map((feature, idx) => {
              const Icon = getIcon(feature.icon);
              return (
                <div 
                  key={idx}
                  className="group p-6 lg:p-8 rounded-2xl bg-gradient-to-b from-white/[0.05] to-transparent border border-white/5 card-hover"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                    <Icon className="w-6 h-6 text-indigo-400" />
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
            <h2 className="text-3xl lg:text-5xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
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
            {plans.map((plan) => {
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
                      <span className="text-4xl lg:text-5xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
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

                  <Button 
                    onClick={() => navigateToApp("/register")}
                    className={`w-full py-6 rounded-xl font-semibold ${
                      isPopular 
                        ? "" 
                        : "bg-white/10 hover:bg-white/20 shadow-none"
                    }`}
                    variant={isPopular ? "default" : "outline"}
                  >
                    {plan.price_monthly === 0 ? "Comenzar Gratis" : "Elegir Plan"}
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
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
            <h2 className="text-3xl lg:text-5xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Lo que dicen{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                nuestros clientes
              </span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {(displayContent.testimonials || []).map((testimonial, idx) => (
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
            <h2 className="text-3xl lg:text-5xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Preguntas{" "}
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Frecuentes
              </span>
            </h2>
          </div>

          <div className="space-y-4">
            {(displayContent.faq || []).map((item, idx) => (
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
              <h2 className="text-3xl lg:text-5xl font-bold text-white mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {displayContent.cta_final?.title}
              </h2>
              <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
                {displayContent.cta_final?.subtitle}
              </p>
              <Button 
                size="lg" 
                onClick={() => navigateToApp("/register")}
                className="bg-white text-indigo-600 hover:bg-slate-100 px-10 py-6 text-lg rounded-xl font-semibold shadow-2xl hover:scale-105 transition-all"
              >
                {displayContent.cta_final?.button_text || "Comenzar Prueba Gratuita"}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
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
              <span className="text-xl font-bold text-white">{branding.app_name || "SyncStock"}</span>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 text-slate-400">
              <a href="#features" className="hover:text-white transition-colors">Características</a>
              <a href="#pricing" className="hover:text-white transition-colors">Precios</a>
              <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
              <button onClick={() => navigateToApp("/login")} className="hover:text-white transition-colors">Acceder</button>
            </div>

            <p className="text-slate-500 text-sm">
              © {new Date().getFullYear()} {branding.app_name || "SyncStock"}. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
