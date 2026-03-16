import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Zap, Database, Store, Calculator, RefreshCw, Shield, Check,
  ChevronRight, Star, ArrowRight, ChevronDown, Layers, BarChart3,
  Clock, Users, Globe, Package, TrendingUp, Truck, FileSpreadsheet,
  Webhook, CheckCircle2, Building2, ShoppingCart, Settings, Bell,
  ArrowUpRight, Cpu, Lock, Headphones, Play, ShoppingBag, Tag,
  BadgeDollarSign, MessageCircle, LifeBuoy
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, Button, Badge, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";

const iconMap = {
  Zap, Database, Store, Calculator, RefreshCw, Shield,
  Layers, BarChart3, Clock, Users, Star, Globe, Package,
  TrendingUp, Truck, FileSpreadsheet, Webhook, Cpu, Lock,
  Headphones, Building2, ShoppingCart, Settings, Bell,
  ShoppingBag, Tag, BadgeDollarSign, MessageCircle, LifeBuoy,
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
          app.stockhub.pro/dashboard
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

  return (
    <div className="overflow-x-hidden">

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section id="hero" className={cn(
        "relative pt-28 pb-20 lg:pt-36 lg:pb-28 overflow-hidden",
        dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 via-white to-white"
      )}>
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
          <div className="absolute top-20 -left-20 w-72 h-72 bg-violet-500/10 rounded-full blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left */}
            <div className="animate-slide-up">
              <div className={cn(
                "inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium border mb-6",
                dark ? "bg-indigo-950 text-indigo-300 border-indigo-800" : "bg-indigo-50 text-indigo-700 border-indigo-100"
              )}>
                <span className="text-base">✨</span>
                {hero.badge || branding.app_slogan || "14 días de prueba gratuita"}
              </div>

              <h1 className={cn("text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6", dark ? "text-white" : "text-slate-900")}>
                {hero.title || branding.hero_title || "Sincroniza tu inventario con un clic"}
              </h1>

              <p className={cn("text-lg lg:text-xl leading-relaxed mb-8 max-w-xl", dark ? "text-slate-300" : "text-slate-600")}>
                {hero.subtitle || branding.hero_subtitle || "Conecta proveedores, gestiona catálogos y actualiza tus tiendas automáticamente."}
              </p>

              <div className="flex flex-col sm:flex-row gap-3 mb-10">
                <a
                  href={`${APP_URL}/#/register`}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all duration-200 shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-0.5"
                >
                  {hero.cta_primary || "Empezar Gratis"}
                  <ArrowRight size={18} />
                </a>
                <a
                  href={`${APP_URL}/#/login`}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 px-6 py-3.5 font-semibold rounded-xl border-2 transition-all duration-200",
                    dark ? "border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800" : "border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  )}
                >
                  <Play size={16} />
                  {hero.cta_secondary || "Ver Demo"}
                </a>
              </div>

              {/* Trust badges */}
              <div className="flex flex-wrap items-center gap-4">
                {[
                  { icon: <Shield size={14} className="text-emerald-500" />, text: "Datos encriptados" },
                  { icon: <Users size={14} className="text-indigo-500" />, text: "+500 empresas" },
                  { icon: <Star size={14} className="text-amber-400 fill-amber-400" />, text: "4.9/5 valoración" },
                ].map((badge, i) => (
                  <div key={i} className={cn("flex items-center gap-1.5 text-xs font-medium", dark ? "text-slate-400" : "text-slate-500")}>
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

      {/* ── STATS ─────────────────────────────────────────────────────────── */}
      {stats.length > 0 && (
        <section className={cn("py-12 border-y", dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-slate-50")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
              {stats.map((stat, i) => (
                <div key={i} className="text-center">
                  <div className={cn("text-3xl lg:text-4xl font-bold mb-1", dark ? "text-white" : "text-slate-900")}>
                    {stat.value}
                  </div>
                  <div className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── HOW IT WORKS ──────────────────────────────────────────────────── */}
      {howItWorks.length > 0 && (
        <section id="how" className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Cómo funciona</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Operativo en <span className="text-indigo-600">menos de 15 minutos</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto">
                Sin código, sin complicaciones. Solo conecta tus fuentes y empieza a sincronizar.
              </SectionSubtitle>
            </div>
            <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
              {howItWorks.map((step, i) => (
                <div key={i} className="relative text-center">
                  {i < howItWorks.length - 1 && (
                    <div className={cn("hidden md:block absolute top-10 left-[60%] w-[80%] border-t-2 border-dashed", dark ? "border-slate-700" : "border-slate-200")} />
                  )}
                  <div className="relative inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-indigo-600 text-white text-3xl font-bold mb-6 shadow-lg shadow-indigo-500/20">
                    {step.step}
                  </div>
                  <h3 className={cn("text-xl font-bold mb-3", dark ? "text-white" : "text-slate-900")}>
                    {step.title}
                  </h3>
                  <p className={cn("leading-relaxed", dark ? "text-slate-400" : "text-slate-500")}>
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── FEATURES ──────────────────────────────────────────────────────── */}
      {features.length > 0 && (
        <section id="features" className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Características</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Todo lo que necesitas para <span className="text-indigo-600">automatizar</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto">
                Una plataforma completa para la gestión de inventario B2B.
              </SectionSubtitle>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feat, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-6 rounded-2xl border card-hover",
                    dark ? "bg-slate-800 border-slate-700 hover:border-indigo-500/50" : "bg-white border-slate-100 hover:border-indigo-200 hover:shadow-lg"
                  )}
                >
                  <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-4", dark ? "bg-indigo-950" : "bg-indigo-50")}>
                    <Icon name={feat.icon} size={22} className="text-indigo-600" />
                  </div>
                  <h3 className={cn("font-semibold text-lg mb-2", dark ? "text-white" : "text-slate-900")}>
                    {feat.title}
                  </h3>
                  <p className={cn("text-sm leading-relaxed", dark ? "text-slate-400" : "text-slate-500")}>
                    {feat.description}
                  </p>
                </div>
              ))}
            </div>
            <div className="text-center mt-10">
              <Link
                to="/caracteristicas"
                className={cn(
                  "inline-flex items-center gap-2 font-semibold transition-colors",
                  dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700"
                )}
              >
                Ver todas las características <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* ── INTEGRATIONS ──────────────────────────────────────────────────── */}
      {integrations.length > 0 && (
        <section id="integrations" className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <SectionLabel>Integraciones</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>
                Conecta con tus <span className="text-indigo-600">plataformas favoritas</span>
              </SectionTitle>
              <SectionSubtitle className="mt-4 max-w-2xl mx-auto">
                Compatibilidad nativa con los principales sistemas de eCommerce, CRM y fuentes de datos.
              </SectionSubtitle>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-4">
              {integrations.map((intg, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex flex-col items-center gap-3 p-5 rounded-2xl border text-center card-hover",
                    dark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"
                  )}
                >
                  <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", dark ? "bg-slate-700" : "bg-white shadow-sm")}>
                    <Icon name={intg.icon} size={22} className="text-indigo-600" />
                  </div>
                  <div>
                    <div className={cn("text-sm font-semibold", dark ? "text-white" : "text-slate-800")}>{intg.name}</div>
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
          <div className="text-center mb-12">
            <SectionLabel>Precios</SectionLabel>
            <SectionTitle className={dark ? "text-white" : ""}>
              Planes para <span className="text-indigo-600">cada negocio</span>
            </SectionTitle>
            <SectionSubtitle className="mt-4 max-w-xl mx-auto">
              Sin compromisos. Cambia o cancela cuando quieras.
            </SectionSubtitle>
            {/* Billing toggle */}
            <div className={cn("inline-flex items-center rounded-xl p-1 border mt-8", dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200")}>
              {["monthly", "yearly"].map(cycle => (
                <button
                  key={cycle}
                  onClick={() => setBillingCycle(cycle)}
                  className={cn(
                    "px-5 py-2 rounded-lg text-sm font-medium transition-all",
                    billingCycle === cycle
                      ? "bg-indigo-600 text-white shadow-sm"
                      : dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-700"
                  )}
                >
                  {cycle === "monthly" ? "Mensual" : "Anual"}{cycle === "yearly" && (
                    <span className="ml-1.5 text-xs bg-emerald-500 text-white rounded-full px-1.5 py-0.5">-17%</span>
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
                    "relative flex flex-col rounded-2xl border p-6",
                    isPopular
                      ? "border-indigo-500 shadow-xl shadow-indigo-500/10 ring-2 ring-indigo-500"
                      : dark ? "border-slate-700 bg-slate-800" : "border-slate-100 bg-white"
                  )}
                >
                  {isPopular && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="bg-indigo-600 text-white text-xs font-bold px-4 py-1 rounded-full shadow">
                        Más popular
                      </span>
                    </div>
                  )}
                  <div className="mb-4">
                    <h3 className={cn("text-lg font-bold mb-1", dark ? "text-white" : "text-slate-900")}>{plan.name}</h3>
                    <p className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>{plan.description}</p>
                  </div>
                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className={cn("text-4xl font-bold", dark ? "text-white" : "text-slate-900")}>
                        {price === 0 ? "Gratis" : `€${billingCycle === "yearly" ? monthlyEquiv : price}`}
                      </span>
                      {price > 0 && (
                        <span className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>
                          /mes{billingCycle === "yearly" && <span className="block text-xs text-emerald-500">Facturado anualmente</span>}
                        </span>
                      )}
                    </div>
                    {plan.trial_days > 0 && (
                      <p className="text-xs text-indigo-500 mt-1">{plan.trial_days} días de prueba gratis</p>
                    )}
                  </div>
                  <ul className="space-y-2.5 flex-1 mb-6">
                    {(plan.features || []).slice(0, 5).map((feat, j) => (
                      <li key={j} className="flex items-start gap-2">
                        <Check size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                        <span className={cn("text-sm", dark ? "text-slate-300" : "text-slate-600")}>{feat}</span>
                      </li>
                    ))}
                    {(plan.features || []).length > 5 && (
                      <li className={cn("text-xs pl-5", dark ? "text-slate-500" : "text-slate-400")}>
                        +{(plan.features || []).length - 5} más...
                      </li>
                    )}
                  </ul>
                  <a
                    href={`${APP_URL}/#/register`}
                    className={cn(
                      "w-full text-center px-4 py-2.5 rounded-xl text-sm font-semibold transition-all",
                      isPopular
                        ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm"
                        : dark ? "bg-slate-700 text-white hover:bg-slate-600" : "bg-slate-100 text-slate-800 hover:bg-slate-200"
                    )}
                  >
                    {price === 0 ? "Empezar gratis" : `Empezar${plan.trial_days > 0 ? " prueba" : ""}`}
                  </a>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-8">
            <Link
              to="/precios"
              className={cn(
                "inline-flex items-center gap-2 font-semibold transition-colors",
                dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700"
              )}
            >
              Ver comparativa completa de planes <ArrowRight size={16} />
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
            <div className="grid md:grid-cols-3 gap-6">
              {testimonials.map((t, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-6 rounded-2xl border",
                    dark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"
                  )}
                >
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: t.rating || 5 }).map((_, j) => (
                      <Star key={j} size={14} className="text-amber-400 fill-amber-400" />
                    ))}
                  </div>
                  <p className={cn("text-sm leading-relaxed mb-5 italic", dark ? "text-slate-300" : "text-slate-600")}>
                    "{t.quote}"
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white text-sm font-bold">
                      {t.author?.[0] || "?"}
                    </div>
                    <div>
                      <div className={cn("text-sm font-semibold", dark ? "text-white" : "text-slate-800")}>{t.author}</div>
                      <div className={cn("text-xs", dark ? "text-slate-400" : "text-slate-500")}>{t.role}</div>
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
              <SectionLabel>FAQ</SectionLabel>
              <SectionTitle className={dark ? "text-white" : ""}>Preguntas frecuentes</SectionTitle>
            </div>
            <div className="space-y-3">
              {faq.slice(0, 6).map((item, i) => (
                <div
                  key={i}
                  className={cn("rounded-xl border overflow-hidden", dark ? "border-slate-700" : "border-slate-200")}
                >
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className={cn(
                      "w-full flex items-center justify-between px-5 py-4 text-left transition-colors",
                      dark
                        ? openFaq === i ? "bg-slate-700" : "bg-slate-800 hover:bg-slate-750"
                        : openFaq === i ? "bg-indigo-50" : "bg-white hover:bg-slate-50"
                    )}
                  >
                    <span className={cn("font-medium text-sm pr-4", dark ? "text-white" : "text-slate-900")}>{item.question}</span>
                    <ChevronDown
                      size={16}
                      className={cn(
                        "flex-shrink-0 transition-transform",
                        openFaq === i ? "rotate-180 text-indigo-500" : dark ? "text-slate-400" : "text-slate-400"
                      )}
                    />
                  </button>
                  {openFaq === i && (
                    <div className={cn("px-5 pb-5 pt-2 faq-content-enter", dark ? "bg-slate-800 text-slate-300" : "bg-white text-slate-600")}>
                      <p className="text-sm leading-relaxed">{item.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── FINAL CTA ─────────────────────────────────────────────────────── */}
      <section className="py-20 lg:py-28 bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-700 animate-gradient relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-64 h-64 bg-violet-500/20 rounded-full blur-3xl" />
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6">
            {ctaFinal.title || "¿Listo para automatizar tu negocio?"}
          </h2>
          <p className="text-lg text-indigo-100 mb-10 max-w-2xl mx-auto">
            {ctaFinal.subtitle || "Únete a cientos de empresas que ya optimizan su gestión de inventario"}
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a
              href={`${APP_URL}/#/register`}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-xl hover:shadow-2xl hover:-translate-y-0.5"
            >
              {ctaFinal.button_text || "Comenzar Prueba Gratuita"}
              <ArrowRight size={18} />
            </a>
            <a
              href={`${APP_URL}/#/login`}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-white/30 text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
            >
              Ya tengo cuenta
            </a>
          </div>
          <p className="text-indigo-200 text-sm mt-6">Sin tarjeta de crédito · Cancela en cualquier momento</p>
        </div>
      </section>

    </div>
  );
}
