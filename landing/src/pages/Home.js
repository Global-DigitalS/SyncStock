import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Zap, Database, Store, Calculator, RefreshCw, Shield, Check,
  ChevronRight, Star, ArrowRight, ChevronDown, Layers, BarChart3,
  Clock, Users, Globe, Package, TrendingUp, Truck, FileSpreadsheet,
  Webhook, CheckCircle2, Building2, ShoppingCart, Settings, Bell,
  ArrowUpRight, Cpu, Lock, Headphones, Play, ShoppingBag, Tag,
  BadgeDollarSign, MessageCircle, LifeBuoy, Cloud, Sparkles, Boxes,
  Search, Monitor, Lightbulb, Target, Rocket, Award, Code2, Workflow
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, Button, Badge, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";

const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield,
  Layers, BarChart3, Clock, Users, Star, Globe, Package,
  TrendingUp, Truck, FileSpreadsheet, Webhook, Cpu, Lock,
  Headphones, Building2, ShoppingCart, Settings, Bell,
  ShoppingBag, Tag, BadgeDollarSign, MessageCircle, LifeBuoy,
  Cloud, Sparkles, Boxes, Search, Monitor, Lightbulb, Target,
  Rocket, Award, Code2, Workflow
};

function Icon({ name, ...props }) {
  const Comp = iconMap[name];
  if (!Comp) return <Zap {...props} />;
  return <Comp {...props} />;
}

function DashboardMockup({ dark }) {
  return (
    <div className={cn(
      "rounded-2xl border shadow-2xl overflow-hidden",
      dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200"
    )}>
      {/* Title bar */}
      <div className={cn("flex items-center gap-2 px-4 py-3 border-b", dark ? "border-slate-700 bg-slate-900" : "border-slate-100 bg-slate-50")}>
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <div className="w-3 h-3 rounded-full bg-green-400" />
        </div>
        <div className={cn("flex-1 mx-4 h-6 rounded text-xs flex items-center px-3", dark ? "bg-slate-800 text-slate-400" : "bg-white text-slate-400 border border-slate-200")}>
          app.syncstock.io/dashboard
        </div>
      </div>
      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div className={cn("h-5 w-32 rounded-lg", dark ? "bg-slate-700" : "bg-slate-100")} />
          <div className="flex gap-2">
            <div className="h-7 w-20 rounded-lg bg-indigo-100" />
            <div className="h-7 w-16 rounded-lg bg-indigo-600" />
          </div>
        </div>
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-2">
          {[
            { color: "indigo", value: "1.247", label: "Productos" },
            { color: "emerald", value: "12", label: "Proveedores" },
            { color: "amber", value: "3", label: "Tiendas" },
            { color: "violet", value: "99%", label: "Uptime" },
          ].map((stat, i) => (
            <div key={i} className={cn("rounded-xl p-3", dark ? "bg-slate-700" : "bg-slate-50")}>
              <div className={`text-sm font-bold text-${stat.color}-600`}>{stat.value}</div>
              <div className={cn("text-xs", dark ? "text-slate-400" : "text-slate-500")}>{stat.label}</div>
            </div>
          ))}
        </div>
        {/* Table */}
        <div className={cn("rounded-xl overflow-hidden border", dark ? "border-slate-700" : "border-slate-100")}>
          {[
            { name: "Proveedor Alpha", status: "sync", products: 342, time: "Hace 2m" },
            { name: "Tech Distributors", status: "ok", products: 891, time: "Hace 15m" },
            { name: "Global Parts SL", status: "ok", products: 214, time: "Hace 1h" },
          ].map((row, i) => (
            <div key={i} className={cn(
              "flex items-center justify-between px-3 py-2.5 text-xs border-b last:border-0",
              dark ? "border-slate-700 hover:bg-slate-700/50" : "border-slate-50 hover:bg-slate-50"
            )}>
              <div className="flex items-center gap-2">
                <div className={cn("w-6 h-6 rounded-lg flex items-center justify-center", dark ? "bg-slate-600" : "bg-indigo-100")}>
                  <Database size={10} className="text-indigo-600" />
                </div>
                <span className={cn("font-medium", dark ? "text-slate-200" : "text-slate-700")}>{row.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn("text-xs", dark ? "text-slate-400" : "text-slate-400")}>{row.products} prods.</span>
                {row.status === "sync" ? (
                  <span className="flex items-center gap-1 text-amber-500 text-xs"><RefreshCw size={10} className="animate-spin" /> Sync</span>
                ) : (
                  <span className="flex items-center gap-1 text-emerald-500 text-xs"><CheckCircle2 size={10} /> OK</span>
                )}
                <span className={cn("text-xs", dark ? "text-slate-500" : "text-slate-400")}>{row.time}</span>
              </div>
            </div>
          ))}
        </div>
        {/* Chart placeholder */}
        <div className={cn("rounded-xl p-3 flex items-end gap-1 h-20", dark ? "bg-slate-700" : "bg-slate-50")}>
          {[40, 65, 45, 80, 60, 90, 75, 95, 70, 85, 88, 92].map((h, i) => (
            <div
              key={i}
              className={cn("flex-1 rounded-sm", i === 11 ? "bg-indigo-600" : dark ? "bg-slate-600" : "bg-indigo-200")}
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const { branding, plans, content, theme, APP_URL } = useApp();
  const dark = theme === "dark";
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [openFaq, setOpenFaq] = useState(null);

  const hero = content?.hero || {};
  const stats = content?.stats || [];
  const features = content?.features || [];
  const integrations = content?.integrations || [];
  const howItWorks = content?.how_it_works || [];
  const testimonials = content?.testimonials || [];
  const faq = content?.faq || [];
  const ctaFinal = content?.cta_final || {};

  const displayedPlans = plans.filter(p => p.is_active !== false).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

  // Agregar schema.org structured data para SEO
  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "SyncStock",
      "description": "Plataforma SaaS para sincronización automática de inventarios B2B. Conecta proveedores, gestiona catálogos y actualiza tiendas online en tiempo real.",
      "url": window.location.origin,
      "image": `${window.location.origin}/logo.png`,
      "applicationCategory": "BusinessApplication",
      "operatingSystem": "Web",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "EUR",
        "description": "Plan Free incluido"
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "ratingCount": "500"
      }
    });
    document.head.appendChild(script);
    return () => script.remove();
  }, []);

  return (
    <div className="overflow-x-hidden">

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section id="hero" className={cn(
        "relative pt-32 pb-24 lg:pt-40 lg:pb-32 overflow-hidden",
        dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 via-white to-white"
      )}>
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
          <div className="absolute top-20 -left-20 w-72 h-72 bg-violet-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 right-20 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left */}
            <div className="animate-slide-up">
              <div className={cn(
                "inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium border mb-8",
                dark ? "bg-indigo-950 text-indigo-300 border-indigo-800" : "bg-indigo-50 text-indigo-700 border-indigo-100"
              )}>
                <Rocket size={14} />
                {hero.badge || branding.app_slogan || "14 días de prueba gratuita"}
              </div>

              <h1 className={cn(
                "text-5xl sm:text-6xl lg:text-7xl font-black leading-tight tracking-tight mb-8",
                dark ? "text-white" : "text-slate-900"
              )}>
                {hero.title || branding.hero_title || "Automatiza tu inventario completamente"}
              </h1>

              <p className={cn(
                "text-xl lg:text-2xl leading-relaxed mb-10 max-w-xl font-light",
                dark ? "text-slate-300" : "text-slate-600"
              )}>
                {hero.subtitle || branding.hero_subtitle || "Conecta proveedores, gestiona catálogos y actualiza tus tiendas automáticamente. Ahorra 20+ horas semanales."}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <a
                  href={`${APP_URL}/#/register`}
                  className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-all duration-200 shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-1 text-lg"
                >
                  {hero.cta_primary || "Empezar Gratis"}
                  <ArrowRight size={20} />
                </a>
                <a
                  href={`${APP_URL}/#/login`}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 px-8 py-4 font-semibold rounded-xl border-2 transition-all duration-200 text-lg",
                    dark ? "border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800" : "border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  )}
                >
                  <Play size={18} />
                  {hero.cta_secondary || "Ver Demo"}
                </a>
              </div>

              {/* Trust badges */}
              <div className="flex flex-wrap items-center gap-6">
                {[
                  { icon: <Shield size={16} className="text-emerald-500" />, text: "Datos encriptados" },
                  { icon: <Users size={16} className="text-indigo-500" />, text: "+500 empresas" },
                  { icon: <Star size={16} className="text-amber-400 fill-amber-400" />, text: "4.9/5 rating" },
                ].map((badge, i) => (
                  <div key={i} className={cn("flex items-center gap-2 text-sm font-medium", dark ? "text-slate-400" : "text-slate-600")}>
                    {badge.icon} {badge.text}
                  </div>
                ))}
              </div>
            </div>

            {/* Right - Dashboard mockup */}
            <div className="lg:block animate-float">
              <DashboardMockup dark={dark} />
            </div>
          </div>
        </div>
      </section>

      {/* ── STATS STRIPE ──────────────────────────────────────────────────── */}
      {stats.length > 0 && (
        <section className={cn("py-16 border-y", dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-gradient-to-r from-slate-50 to-slate-100")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
              {stats.map((stat, i) => (
                <div key={i} className="text-center">
                  <div className={cn("text-4xl lg:text-5xl font-black mb-2 bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent")}>
                    {stat.value}
                  </div>
                  <div className={cn("text-sm font-medium", dark ? "text-slate-400" : "text-slate-600")}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── PROBLEMA & SOLUCIÓN ─────────────────────────────────────────── */}
      <section className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Problem */}
            <div className="animate-slide-up">
              <Badge className="mb-4">El Problema</Badge>
              <h2 className={cn("text-4xl font-black mb-6 leading-tight", dark ? "text-white" : "text-slate-900")}>
                Gestionar múltiples proveedores es un caos
              </h2>
              <div className="space-y-4 mb-8">
                {[
                  "❌ Hojas de cálculo desincronizadas",
                  "❌ Actualizaciones manuales que toman horas",
                  "❌ Errores de precios y stock",
                  "❌ Impacto en ventas y confianza del cliente",
                  "❌ Escalabilidad limitada"
                ].map((item, i) => (
                  <p key={i} className={cn("text-lg font-medium", dark ? "text-slate-300" : "text-slate-600")}>
                    {item}
                  </p>
                ))}
              </div>
            </div>

            {/* Solution */}
            <div className="animate-float">
              <Badge className="mb-4 bg-emerald-50 text-emerald-700">La Solución</Badge>
              <h2 className={cn("text-4xl font-black mb-6 leading-tight text-emerald-600")}>
                SyncStock lo automatiza todo
              </h2>
              <div className="space-y-4 mb-8">
                {[
                  "✅ Sincronización 100% automática 24/7",
                  "✅ Cero errores manuales",
                  "✅ Actualización en tiempo real",
                  "✅ Gestión centralizada",
                  "✅ Escala a millones de productos"
                ].map((item, i) => (
                  <p key={i} className={cn("text-lg font-medium", dark ? "text-slate-300" : "text-slate-600")}>
                    {item}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────────────────────── */}
      {howItWorks.length > 0 && (
        <section id="how" className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Cómo funciona</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                3 pasos para <span className="text-indigo-600">automatizar tu inventario</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto text-lg">
                Operativo en menos de 15 minutos. Sin código, sin complicaciones.
              </SectionSubtitle>
            </div>
            <div className="grid md:grid-cols-3 gap-10">
              {howItWorks.map((step, i) => (
                <div key={i} className="relative text-center group">
                  {i < howItWorks.length - 1 && (
                    <div className={cn("hidden md:block absolute top-12 left-[60%] w-[80%] border-t-2 border-dashed group-hover:border-indigo-400 transition-colors", dark ? "border-slate-700" : "border-slate-300")} />
                  )}
                  <div className={cn(
                    "relative inline-flex items-center justify-center w-24 h-24 rounded-2xl text-white text-3xl font-black mb-6 shadow-lg transition-all group-hover:shadow-xl group-hover:scale-110",
                    dark ? "bg-indigo-600 shadow-indigo-500/20" : "bg-indigo-600 shadow-indigo-500/20"
                  )}>
                    {step.step}
                  </div>
                  <h3 className={cn("text-2xl font-bold mb-3", dark ? "text-white" : "text-slate-900")}>
                    {step.title}
                  </h3>
                  <p className={cn("text-lg leading-relaxed", dark ? "text-slate-400" : "text-slate-600")}>
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── FEATURES DESTACADAS ───────────────────────────────────────────── */}
      {features.length > 0 && (
        <section id="features" className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Características</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Potencia empresarial <span className="text-indigo-600">para cualquier tamaño</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto text-lg">
                Funciones avanzadas pensadas para crecer con tu negocio.
              </SectionSubtitle>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feat, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-8 rounded-2xl border transition-all duration-300 group cursor-pointer",
                    dark
                      ? "bg-slate-800 border-slate-700 hover:border-indigo-500 hover:shadow-xl hover:shadow-indigo-500/10 hover:bg-slate-750"
                      : "bg-white border-slate-100 hover:border-indigo-300 hover:shadow-2xl hover:shadow-indigo-500/10"
                  )}
                >
                  <div className={cn(
                    "w-14 h-14 rounded-xl flex items-center justify-center mb-5 transition-all group-hover:scale-110",
                    dark ? "bg-indigo-950" : "bg-indigo-50"
                  )}>
                    <Icon name={feat.icon} size={24} className="text-indigo-600" />
                  </div>
                  <h3 className={cn("font-bold text-lg mb-3", dark ? "text-white" : "text-slate-900")}>
                    {feat.title}
                  </h3>
                  <p className={cn("text-base leading-relaxed", dark ? "text-slate-400" : "text-slate-600")}>
                    {feat.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── POR QUÉ SYNCSTOCK ─────────────────────────────────────────────── */}
      <section className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <SectionLabel>Ventajas Competitivas</SectionLabel>
            <SectionTitle className={dark ? "text-white" : ""}>
              Por qué elegir <span className="text-indigo-600">SyncStock</span>
            </SectionTitle>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: "Zap", title: "Velocidad", desc: "Sincronización instantánea en tiempo real" },
              { icon: "Shield", title: "Seguridad", desc: "Encriptación de extremo a extremo" },
              { icon: "Headphones", title: "Soporte", desc: "Equipo dedicado 24/7" },
              { icon: "TrendingUp", title: "Escalabilidad", desc: "Gestiona millones de productos" },
              { icon: "Code2", title: "API Potente", desc: "Integración con cualquier sistema" },
              { icon: "Workflow", title: "Automatización", desc: "Workflows personalizables ilimitados" },
              { icon: "Award", title: "Fiabilidad", desc: "99.9% uptime garantizado" },
              { icon: "Target", title: "Precisión", desc: "Cero errores de sincronización" },
            ].map((item, i) => (
              <div key={i} className={cn(
                "p-6 rounded-xl border text-center transition-all hover:scale-105",
                dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200"
              )}>
                <Icon name={item.icon} size={28} className="text-indigo-600 mx-auto mb-3" />
                <h3 className={cn("font-bold mb-2", dark ? "text-white" : "text-slate-900")}>{item.title}</h3>
                <p className={cn("text-sm", dark ? "text-slate-400" : "text-slate-600")}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── INTEGRATIONS ──────────────────────────────────────────────────── */}
      {integrations.length > 0 && (
        <section id="integrations" className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Integraciones</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Conecta con tus <span className="text-indigo-600">plataformas favoritas</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto text-lg">
                Compatibilidad nativa con +50 plataformas. Sin configuración extra.
              </SectionSubtitle>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-4">
              {integrations.map((intg, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex flex-col items-center gap-3 p-6 rounded-2xl border text-center transition-all hover:scale-110 cursor-pointer",
                    dark ? "bg-slate-800 border-slate-700 hover:border-indigo-500 hover:shadow-lg hover:shadow-indigo-500/20" : "bg-slate-50 border-slate-100 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-500/10"
                  )}
                >
                  <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", dark ? "bg-slate-700" : "bg-white shadow-sm")}>
                    <Icon name={intg.icon} size={22} className="text-indigo-600" />
                  </div>
                  <div>
                    <div className={cn("text-sm font-bold", dark ? "text-white" : "text-slate-800")}>{intg.name}</div>
                    <div className={cn("text-xs", dark ? "text-slate-500" : "text-slate-400")}>{intg.category}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── PRICING PREVIEW ───────────────────────────────────────────────── */}
      <section id="pricing" className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <SectionLabel>Precios</SectionLabel>
            <SectionTitle className={dark ? "text-white" : ""}>
              Planes para <span className="text-indigo-600">cada negocio</span>
            </SectionTitle>
            <SectionSubtitle className="mt-4 max-w-xl mx-auto text-lg">
              Sin compromisos. Cambia o cancela cuando quieras. Prueba gratis 14 días.
            </SectionSubtitle>
            {/* Billing toggle */}
            <div className={cn("inline-flex items-center rounded-xl p-1 border mt-8", dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200")}>
              {["monthly", "yearly"].map(cycle => (
                <button
                  key={cycle}
                  onClick={() => setBillingCycle(cycle)}
                  className={cn(
                    "px-6 py-2.5 rounded-lg text-sm font-semibold transition-all",
                    billingCycle === cycle
                      ? "bg-indigo-600 text-white shadow-md"
                      : dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-700"
                  )}
                >
                  {cycle === "monthly" ? "Mensual" : "Anual"}{cycle === "yearly" && (
                    <span className="ml-2 text-xs bg-emerald-500 text-white rounded-full px-2 py-0.5">Ahorra 17%</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {displayedPlans.map((plan) => {
              const price = billingCycle === "yearly" ? plan.price_yearly : plan.price_monthly;
              const monthlyEquiv = billingCycle === "yearly" && plan.price_yearly > 0
                ? (plan.price_yearly / 12).toFixed(0)
                : null;
              const isPopular = plan.is_popular || plan.name?.toLowerCase() === "professional" || plan.name?.toLowerCase() === "pro";

              return (
                <div
                  key={plan.id}
                  className={cn(
                    "relative flex flex-col rounded-2xl border p-8 transition-all hover:scale-105",
                    isPopular
                      ? "border-indigo-500 shadow-2xl shadow-indigo-500/20 ring-2 ring-indigo-500"
                      : dark ? "border-slate-700 bg-slate-800 hover:border-slate-600" : "border-slate-100 bg-white hover:border-slate-200"
                  )}
                >
                  {isPopular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                      <span className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg">
                        ⭐ Más Popular
                      </span>
                    </div>
                  )}
                  <div className="mb-6">
                    <h3 className={cn("text-2xl font-bold mb-2", dark ? "text-white" : "text-slate-900")}>{plan.name}</h3>
                    <p className={cn("text-sm", dark ? "text-slate-400" : "text-slate-600")}>{plan.description}</p>
                  </div>
                  <div className="mb-8">
                    <div className="flex items-baseline gap-1">
                      <span className={cn("text-5xl font-black", dark ? "text-white" : "text-slate-900")}>
                        {price === 0 ? "Gratis" : `€${billingCycle === "yearly" ? monthlyEquiv : price}`}
                      </span>
                      {price > 0 && (
                        <span className={cn("text-sm font-medium", dark ? "text-slate-400" : "text-slate-600")}>
                          /mes
                        </span>
                      )}
                    </div>
                    {billingCycle === "yearly" && price > 0 && (
                      <p className="text-xs text-emerald-500 mt-2 font-semibold">Facturado anualmente</p>
                    )}
                    {plan.trial_days > 0 && (
                      <p className="text-xs text-indigo-600 mt-2 font-medium">{plan.trial_days} días de prueba gratis</p>
                    )}
                  </div>
                  <ul className="space-y-3 flex-1 mb-8">
                    {(plan.features || []).slice(0, 5).map((feat, j) => (
                      <li key={j} className="flex items-start gap-3">
                        <Check size={16} className="text-emerald-500 mt-0.5 flex-shrink-0 font-bold" />
                        <span className={cn("text-sm font-medium", dark ? "text-slate-300" : "text-slate-700")}>{feat}</span>
                      </li>
                    ))}
                    {(plan.features || []).length > 5 && (
                      <li className={cn("text-xs pl-7 font-medium", dark ? "text-slate-500" : "text-slate-500")}>
                        +{(plan.features || []).length - 5} características más...
                      </li>
                    )}
                  </ul>
                  <a
                    href={`${APP_URL}/#/register`}
                    className={cn(
                      "w-full text-center px-4 py-3 rounded-xl font-bold transition-all",
                      isPopular
                        ? "bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:shadow-lg hover:shadow-indigo-500/30"
                        : dark ? "bg-slate-700 text-white hover:bg-slate-600" : "bg-slate-100 text-slate-900 hover:bg-slate-200"
                    )}
                  >
                    {price === 0 ? "Empezar Gratis" : "Empezar Prueba"}
                  </a>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/precios"
              className={cn(
                "inline-flex items-center gap-2 font-bold text-lg transition-colors",
                dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700"
              )}
            >
              Ver comparativa completa <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ──────────────────────────────────────────────────── */}
      {testimonials.length > 0 && (
        <section className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Testimonios</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Lo que dicen <span className="text-indigo-600">nuestros clientes</span>
              </SectionTitle>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              {testimonials.map((t, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-8 rounded-2xl border transition-all hover:scale-105 hover:shadow-lg",
                    dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100 shadow-sm"
                  )}
                >
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: t.rating || 5 }).map((_, j) => (
                      <Star key={j} size={16} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className={cn("text-base leading-relaxed mb-6 italic font-medium", dark ? "text-slate-300" : "text-slate-700")}>
                    "{t.quote}"
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                      {t.author?.[0] || "?"}
                    </div>
                    <div>
                      <div className={cn("text-sm font-bold", dark ? "text-white" : "text-slate-900")}>{t.author}</div>
                      <div className={cn("text-xs font-medium", dark ? "text-slate-400" : "text-slate-500")}>{t.role}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── FAQ ───────────────────────────────────────────────────────────── */}
      {faq.length > 0 && (
        <section id="faq" className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Preguntas Frecuentes</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Todo lo que necesitas saber
              </SectionTitle>
            </div>
            <div className="space-y-3">
              {faq.slice(0, 6).map((item, i) => (
                <div
                  key={i}
                  className={cn("rounded-xl border overflow-hidden transition-all", dark ? "border-slate-700" : "border-slate-200")}
                >
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className={cn(
                      "w-full flex items-center justify-between px-6 py-4 text-left transition-colors",
                      dark
                        ? openFaq === i ? "bg-slate-700" : "bg-slate-800 hover:bg-slate-750"
                        : openFaq === i ? "bg-indigo-50" : "bg-white hover:bg-slate-50"
                    )}
                  >
                    <span className={cn("font-semibold text-base pr-4", dark ? "text-white" : "text-slate-900")}>{item.question}</span>
                    <ChevronDown
                      size={18}
                      className={cn(
                        "flex-shrink-0 transition-transform",
                        openFaq === i ? "rotate-180 text-indigo-500" : dark ? "text-slate-400" : "text-slate-400"
                      )}
                    />
                  </button>
                  {openFaq === i && (
                    <div className={cn("px-6 pb-6 pt-4", dark ? "bg-slate-800 text-slate-300" : "bg-white text-slate-700")}>
                      <p className="text-base leading-relaxed font-medium">{item.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── FINAL CTA ─────────────────────────────────────────────────────── */}
      <section className="py-24 lg:py-32 bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-700 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-72 h-72 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-72 h-72 bg-violet-500/20 rounded-full blur-3xl" />
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <h2 className="text-5xl lg:text-6xl font-black text-white mb-8 leading-tight">
            {ctaFinal.title || "¿Listo para revolucionar tu negocio?"}
          </h2>
          <p className="text-xl text-indigo-100 mb-12 max-w-2xl mx-auto font-medium leading-relaxed">
            {ctaFinal.subtitle || "Únete a cientos de empresas que han automatizado su gestión de inventario y ahorran miles de euros cada mes"}
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-5">
            <a
              href={`${APP_URL}/#/register`}
              className="inline-flex items-center justify-center gap-2 px-10 py-4 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-2xl hover:shadow-3xl hover:-translate-y-1 text-lg"
            >
              {ctaFinal.button_text || "Comenzar Prueba Gratuita"}
              <ArrowRight size={20} />
            </a>
            <a
              href={`${APP_URL}/#/login`}
              className="inline-flex items-center justify-center gap-2 px-10 py-4 border-2 border-white/40 text-white font-bold rounded-xl hover:bg-white/10 transition-all text-lg backdrop-blur"
            >
              Acceder si tengo cuenta
            </a>
          </div>
          <p className="text-indigo-200 text-sm mt-8 font-medium">
            Sin tarjeta de crédito · Acceso inmediato · Cancela en cualquier momento
          </p>
        </div>
      </section>

    </div>
  );
}
