import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, X, ArrowRight, HelpCircle } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";

const COMPARISON_FEATURES = [
  { category: "Proveedores y Fuentes", features: [
    { label: "Proveedores activos", keys: ["max_suppliers"], format: "limit" },
    { label: "Conexión FTP/SFTP", values: [true, true, true, true] },
    { label: "Importación CSV/Excel/XML", values: [true, true, true, true] },
    { label: "URL directa (HTTP/HTTPS)", values: [true, true, true, true] },
    { label: "API de proveedores (webhooks)", values: [false, false, true, true] },
  ]},
  { category: "Catálogos y Productos", features: [
    { label: "Catálogos activos", keys: ["max_catalogs"], format: "limit" },
    { label: "Productos gestionados", keys: ["max_products"], format: "limit" },
    { label: "Reglas de margen por producto", values: [false, true, true, true] },
    { label: "Historial de precios", values: [false, true, true, true] },
    { label: "Alertas de cambio de precio", values: [false, false, true, true] },
  ]},
  { category: "Tiendas y Sincronización", features: [
    { label: "Tiendas conectadas", keys: ["max_stores"], format: "limit" },
    { label: "WooCommerce", values: [true, true, true, true] },
    { label: "Shopify", values: [false, true, true, true] },
    { label: "PrestaShop", values: [false, true, true, true] },
    { label: "Wix eCommerce", values: [false, false, true, true] },
    { label: "Magento", values: [false, false, true, true] },
    { label: "Sincronización manual", values: [true, true, true, true] },
    { label: "Sincronización automática", values: [false, true, true, true] },
    { label: "Sincronización en tiempo real", values: [false, false, true, true] },
  ]},
  { category: "CRM e Integraciones", features: [
    { label: "Conexiones CRM", keys: ["max_crm_connections"], format: "limit" },
    { label: "Dolibarr", values: [false, false, true, true] },
    { label: "Odoo (XML-RPC)", values: [false, false, true, true] },
    { label: "HubSpot", values: [false, false, true, true] },
    { label: "Salesforce", values: [false, false, false, true] },
    { label: "Zoho CRM", values: [false, false, true, true] },
    { label: "Pipedrive", values: [false, false, true, true] },
    { label: "Monday CRM", values: [false, false, false, true] },
    { label: "Freshsales", values: [false, false, false, true] },
    { label: "API REST propia", values: [false, false, false, true] },
    { label: "Webhooks salientes", values: [false, false, true, true] },
  ]},
  { category: "Soporte", features: [
    { label: "Soporte por email", values: [true, true, true, true] },
    { label: "Soporte prioritario", values: [false, false, true, true] },
    { label: "Soporte 24/7", values: [false, false, false, true] },
    { label: "Gestor de cuenta dedicado", values: [false, false, false, true] },
    { label: "Onboarding personalizado", values: [false, false, false, true] },
  ]},
];

function formatLimit(val) {
  if (!val && val !== 0) return "—";
  if (val >= 9999) return "Ilimitado";
  return val.toLocaleString("es-ES");
}

function PlanValue({ val, plans, featureKey, format }) {
  if (featureKey && plans[featureKey] !== undefined) {
    const v = plans[featureKey];
    return <span className="text-sm font-medium">{formatLimit(v)}</span>;
  }
  if (typeof val === "boolean") {
    return val
      ? <Check size={18} className="text-emerald-500 mx-auto" />
      : <X size={15} className="text-slate-300 mx-auto" />;
  }
  return <span className="text-sm">{val || "—"}</span>;
}

export default function Pricing() {
  const { plans, theme, APP_URL } = useApp();
  const dark = theme === "dark";
  const [billing, setBilling] = useState("monthly");
  const [openFaq, setOpenFaq] = useState(null);

  const displayedPlans = plans
    .filter(p => p.is_active !== false)
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

  const FAQS = [
    { q: "¿Puedo cambiar de plan en cualquier momento?", a: "Sí. Puedes subir o bajar de plan cuando quieras. Los cambios se aplican de inmediato y la facturación se prorratea automáticamente." },
    { q: "¿Qué métodos de pago aceptáis?", a: "Aceptamos tarjetas de crédito/débito (Visa, Mastercard, Amex) y transferencia bancaria para planes Enterprise mediante Stripe." },
    { q: "¿Hay permanencia mínima?", a: "No. Puedes cancelar cuando quieras. Si cancelas, mantendrás el acceso hasta el final del período facturado." },
    { q: "¿Qué pasa con mis datos si cancelo?", a: "Tus datos se conservan durante 30 días tras la cancelación. Puedes exportarlos en cualquier momento antes de ese plazo." },
    { q: "¿Ofrecéis descuentos para ONGs o startups?", a: "Sí. Contacta con nosotros en el formulario de contacto para hablar de condiciones especiales." },
    { q: "¿Está incluido el soporte en el precio?", a: "Sí. El soporte por email está incluido en todos los planes sin coste adicional." },
  ];

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>

      {/* Hero */}
      <section className={cn("py-20 lg:py-24 text-center", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <SectionLabel>Precios</SectionLabel>
          <SectionTitle className={cn("mt-4 text-5xl", dark ? "text-white" : "")}>
            Planes simples y <span className="text-indigo-600">transparentes</span>
          </SectionTitle>
          <SectionSubtitle className="mt-5 text-lg">
            Sin sorpresas. Sin comisiones ocultas. Cancela en cualquier momento.
          </SectionSubtitle>

          {/* Billing toggle */}
          <div className={cn("inline-flex items-center rounded-xl p-1 border mt-8", dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200 shadow-sm")}>
            {["monthly", "yearly"].map(cycle => (
              <button
                key={cycle}
                onClick={() => setBilling(cycle)}
                className={cn(
                  "px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  billing === cycle
                    ? "bg-indigo-600 text-white shadow-sm"
                    : dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-700"
                )}
              >
                {cycle === "monthly" ? "Mensual" : "Anual"}
                {cycle === "yearly" && (
                  <span className={cn("ml-2 text-xs px-1.5 py-0.5 rounded-full font-bold",
                    billing === "yearly" ? "bg-white/20 text-white" : "bg-emerald-100 text-emerald-700"
                  )}>-17%</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Plan cards */}
      <section className={cn("pb-16", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {displayedPlans.map(plan => {
              const price = billing === "yearly" ? plan.price_yearly : plan.price_monthly;
              const monthlyEquiv = billing === "yearly" && plan.price_yearly > 0
                ? (plan.price_yearly / 12).toFixed(0) : null;
              const isPopular = plan.is_popular || plan.name?.toLowerCase() === "professional" || plan.name?.toLowerCase() === "pro";

              return (
                <div
                  key={plan.id}
                  className={cn(
                    "relative flex flex-col rounded-2xl border p-7",
                    isPopular
                      ? dark ? "bg-indigo-950 border-indigo-500 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/20" : "border-indigo-500 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/10 bg-white"
                      : dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100 shadow-sm"
                  )}
                >
                  {isPopular && (
                    <div className="absolute -top-4 left-0 right-0 flex justify-center">
                      <span className="bg-indigo-600 text-white text-xs font-bold px-5 py-1.5 rounded-full shadow-lg">
                        Más popular
                      </span>
                    </div>
                  )}

                  <div className="mb-5 pt-2">
                    <h3 className={cn("text-xl font-bold mb-1.5", dark ? "text-white" : "text-slate-900")}>{plan.name}</h3>
                    <p className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>{plan.description}</p>
                  </div>

                  <div className="mb-6">
                    {price === 0 ? (
                      <div className={cn("text-4xl font-bold", dark ? "text-white" : "text-slate-900")}>Gratis</div>
                    ) : (
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className={cn("text-4xl font-bold", dark ? "text-white" : "text-slate-900")}>
                            €{billing === "yearly" ? monthlyEquiv : price}
                          </span>
                          <span className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>/mes</span>
                        </div>
                        {billing === "yearly" && (
                          <p className="text-xs text-emerald-500 mt-1">
                            €{plan.price_yearly}/año · Ahorra €{((plan.price_monthly * 12) - plan.price_yearly).toFixed(0)}
                          </p>
                        )}
                      </div>
                    )}
                    {plan.trial_days > 0 && (
                      <p className={cn("text-xs mt-2", dark ? "text-indigo-400" : "text-indigo-600")}>
                        {plan.trial_days} días de prueba gratuita incluidos
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 flex-1 mb-7">
                    {(plan.features || []).map((feat, j) => (
                      <li key={j} className="flex items-start gap-2.5">
                        <Check size={15} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                        <span className={cn("text-sm", dark ? "text-slate-300" : "text-slate-600")}>{feat}</span>
                      </li>
                    ))}
                  </ul>

                  <a
                    href={`${APP_URL}/#/register`}
                    className={cn(
                      "block w-full text-center px-4 py-3 rounded-xl text-sm font-bold transition-all",
                      isPopular
                        ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg"
                        : dark ? "bg-slate-700 text-white hover:bg-slate-600" : "border-2 border-slate-200 text-slate-800 hover:border-slate-300 hover:bg-slate-50"
                    )}
                  >
                    {price === 0 ? "Empezar gratis" : `Empezar${plan.trial_days > 0 ? " — " + plan.trial_days + " días gratis" : ""}`}
                  </a>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Feature comparison table */}
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-900" : "bg-slate-50")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className={cn("text-2xl lg:text-3xl font-bold mb-12 text-center", dark ? "text-white" : "text-slate-900")}>
            Comparativa completa de planes
          </h2>

          <div className={cn("rounded-2xl border overflow-hidden", dark ? "border-slate-700" : "border-slate-200")}>
            {/* Header */}
            <div className={cn("grid border-b", dark ? "border-slate-700 bg-slate-800" : "border-slate-200 bg-white")} style={{ gridTemplateColumns: "2fr repeat(4, 1fr)" }}>
              <div className="p-5" />
              {displayedPlans.map(plan => {
                const isPopular = plan.is_popular || plan.name?.toLowerCase() === "professional" || plan.name?.toLowerCase() === "pro";
                return (
                  <div key={plan.id} className={cn("p-5 text-center border-l", dark ? "border-slate-700" : "border-slate-100")}>
                    <div className={cn("font-bold mb-1", dark ? "text-white" : "text-slate-900")}>{plan.name}</div>
                    {isPopular && (
                      <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-semibold">Popular</span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Feature rows */}
            {COMPARISON_FEATURES.map((cat, ci) => (
              <div key={ci}>
                <div className={cn("px-5 py-3 border-b", dark ? "bg-slate-800/50 border-slate-700 text-slate-400" : "bg-slate-50 border-slate-100 text-slate-500")}>
                  <span className="text-xs font-bold uppercase tracking-wider">{cat.category}</span>
                </div>
                {cat.features.map((feat, fi) => (
                  <div
                    key={fi}
                    className={cn(
                      "grid items-center border-b last:border-0",
                      dark ? "border-slate-700 hover:bg-slate-800/50" : "border-slate-100 hover:bg-slate-50"
                    )}
                    style={{ gridTemplateColumns: "2fr repeat(4, 1fr)" }}
                  >
                    <div className={cn("p-4 text-sm", dark ? "text-slate-300" : "text-slate-700")}>{feat.label}</div>
                    {displayedPlans.map((plan, pi) => (
                      <div key={plan.id} className={cn("p-4 text-center border-l", dark ? "border-slate-700" : "border-slate-100")}>
                        <PlanValue
                          val={feat.values?.[pi]}
                          plans={plan}
                          featureKey={feat.keys?.[0]}
                          format={feat.format}
                        />
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className={cn("text-2xl lg:text-3xl font-bold mb-10 text-center", dark ? "text-white" : "text-slate-900")}>
            Preguntas sobre los precios
          </h2>
          <div className="space-y-3">
            {FAQS.map((item, i) => (
              <div key={i} className={cn("rounded-xl border overflow-hidden", dark ? "border-slate-700" : "border-slate-200")}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className={cn(
                    "w-full flex items-center justify-between px-5 py-4 text-left",
                    dark
                      ? openFaq === i ? "bg-slate-800" : "bg-slate-900 hover:bg-slate-800"
                      : openFaq === i ? "bg-indigo-50" : "bg-white hover:bg-slate-50"
                  )}
                >
                  <span className={cn("font-medium text-sm pr-4", dark ? "text-white" : "text-slate-900")}>{item.q}</span>
                  <HelpCircle size={16} className={cn("flex-shrink-0", dark ? "text-slate-400" : "text-slate-400")} />
                </button>
                {openFaq === i && (
                  <div className={cn("px-5 pb-5 pt-2", dark ? "bg-slate-800 text-slate-300" : "bg-white text-slate-600")}>
                    <p className="text-sm leading-relaxed">{item.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className={cn("text-sm text-center mt-8", dark ? "text-slate-400" : "text-slate-500")}>
            ¿Más preguntas?{" "}
            <Link to="/contacto" className={cn("font-medium", dark ? "text-indigo-400" : "text-indigo-600")}>
              Contáctanos
            </Link>
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-br from-indigo-600 to-violet-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Empieza gratis hoy mismo</h2>
          <p className="text-indigo-100 mb-8">14 días de prueba sin necesidad de tarjeta de crédito.</p>
          <a
            href={`${APP_URL}/#/register`}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-xl"
          >
            Crear cuenta gratis <ArrowRight size={18} />
          </a>
        </div>
      </section>

    </div>
  );
}
