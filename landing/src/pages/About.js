import { Link } from "react-router-dom";
import { ArrowRight, Shield, Zap, Heart, Globe } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";
import { useSEO } from "../hooks/useSEO";

const DEFAULT_TIMELINE = [
  { year: "2022", title: "Fundación", description: "SyncStock nace de la frustración de gestionar proveedores con hojas de cálculo. El primer MVP conecta 3 proveedores con WooCommerce." },
  { year: "2023", title: "Primeros 100 clientes", description: "Lanzamos soporte para PrestaShop, Shopify y la integración con Dolibarr. La comunidad crece hasta 100 empresas activas." },
  { year: "2024", title: "CRM y Odoo", description: "Añadimos integración Odoo XML-RPC, sincronización automática programada y el panel de analíticas avanzadas." },
  { year: "2025", title: "+500 empresas", description: "Superamos los 500 clientes activos. Lanzamos la API pública, webhooks salientes y soporte para Wix y Magento." },
  { year: "2026", title: "8 CRMs y Marketplaces", description: "Lanzamos integración con HubSpot, Salesforce, Zoho, Pipedrive, Monday CRM y Freshsales. Además, soporte para +10 marketplaces europeos incluyendo El Corte Inglés, idealo y Google Shopping." },
];

export default function About() {
  const { branding, content, theme, APP_URL } = useApp();
  const dark = theme === "dark";

  const about = content?.about || {};

  useSEO({
    title: "Nosotros",
    description: "Conoce la historia y los valores de SyncStock. Fundada en 2022, ayudamos a más de 500 empresas a automatizar la gestión de inventario B2B en toda Europa.",
    canonical: "/nosotros",
    structuredData: {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "SyncStock",
      "url": "https://sync-stock.com",
      "description": "Plataforma SaaS B2B para sincronización automática de inventarios entre proveedores y tiendas online.",
      "foundingDate": "2022",
      "numberOfEmployees": { "@type": "QuantitativeValue", "value": "10" },
      "areaServed": "Europe",
      "logo": "https://sync-stock.com/logo.png"
    }
  });
  const values = about.values || [
    { title: "Automatización", description: "Eliminamos tareas repetitivas para que tu equipo se enfoque en el negocio." },
    { title: "Fiabilidad", description: "Nuestros sistemas funcionan 24/7 con una disponibilidad del 99.9%." },
    { title: "Simplicidad", description: "Potente funcionalidad con una interfaz intuitiva que cualquiera puede usar." },
    { title: "Privacidad", description: "Tus datos son tuyos. Nunca los compartimos ni los usamos para publicidad." },
  ];

  const valueIcons = [Zap, Shield, Globe, Heart];

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>

      {/* Hero */}
      <section className={cn("py-20 lg:py-28 relative overflow-hidden", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-96 bg-indigo-500/5 rounded-full blur-3xl" />
        </div>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <SectionLabel>Nosotros</SectionLabel>
          <SectionTitle className={cn("mt-4 text-5xl lg:text-6xl", dark ? "text-white" : "")}>
            Construimos el futuro de la <span className="text-indigo-600">gestión B2B</span>
          </SectionTitle>
          <SectionSubtitle className="mt-6 text-lg max-w-2xl mx-auto">
            {about.mission || "Nuestra misión es eliminar el trabajo manual en la gestión de inventarios B2B, permitiendo a las empresas centrarse en lo que realmente importa."}
          </SectionSubtitle>
        </div>
      </section>

      {/* Stats */}
      <section className={cn("py-12 border-y", dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-slate-50")}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
            {[
              { value: "+500", label: "Empresas activas" },
              { value: "99.9%", label: "Disponibilidad" },
              { value: "24/7", label: "Monitorización" },
              { value: "2022", label: "Fundada en" },
            ].map((stat, i) => (
              <div key={i}>
                <div className={cn("text-3xl lg:text-4xl font-bold mb-1", dark ? "text-white" : "text-slate-900")}>{stat.value}</div>
                <div className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Story */}
      <section className={cn("py-20 lg:py-28", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            <div className="reveal-right">
              <h2 className={cn("text-3xl lg:text-4xl font-bold mb-6", dark ? "text-white" : "text-slate-900")}>
                Nuestra historia
              </h2>
              <div className={cn("space-y-4 text-base leading-relaxed", dark ? "text-slate-300" : "text-slate-600")}>
                <p>
                  {about.story || "Fundada en 2022, SyncStock nació de la frustración de gestionar docenas de proveedores con hojas de cálculo. Hoy ayudamos a más de 500 empresas a automatizar sus catálogos."}
                </p>
                <p>
                  Cada día, miles de productos se sincronizan a través de nuestra plataforma entre proveedores y tiendas online en toda Europa. Lo que empezó como una solución para un problema concreto, se ha convertido en la plataforma de referencia para la gestión de inventario B2B.
                </p>
                <p>
                  Creemos que la tecnología debe trabajar para ti, no al contrario. Por eso {branding.app_name} es intuitivo, confiable y está diseñado para escalar con tu negocio.
                </p>
              </div>
            </div>
            {/* Timeline */}
            <div className="space-y-6">
              {DEFAULT_TIMELINE.map((item, i) => (
                <div key={i} className="flex gap-5">
                  <div className="flex flex-col items-center">
                    <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      {item.year.slice(-2)}
                    </div>
                    {i < DEFAULT_TIMELINE.length - 1 && (
                      <div className={cn("w-0.5 flex-1 mt-2", dark ? "bg-slate-700" : "bg-slate-200")} />
                    )}
                  </div>
                  <div className="pb-6">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={cn("text-xs font-bold text-indigo-500")}>{item.year}</span>
                      <span className={cn("font-semibold", dark ? "text-white" : "text-slate-900")}>{item.title}</span>
                    </div>
                    <p className={cn("text-sm leading-relaxed", dark ? "text-slate-400" : "text-slate-500")}>{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className={cn("py-20 lg:py-28", dark ? "bg-slate-900" : "bg-slate-50")}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className={cn("text-3xl lg:text-4xl font-bold mb-4", dark ? "text-white" : "text-slate-900")}>
              Nuestros valores
            </h2>
            <p className={cn("text-lg", dark ? "text-slate-400" : "text-slate-500")}>
              Los principios que guían cada decisión que tomamos.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((val, i) => {
              const IconComp = valueIcons[i % valueIcons.length];
              return (
                <div
                  key={i}
                  className={cn(
                    `reveal-up reveal-delay-${(i + 1) * 100}`,
                    "p-6 rounded-2xl border text-center card-hover",
                    dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100"
                  )}
                >
                  <div className={cn("w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5", dark ? "bg-indigo-950" : "bg-indigo-50")}>
                    <IconComp size={26} className="text-indigo-600" />
                  </div>
                  <h3 className={cn("font-bold text-lg mb-2", dark ? "text-white" : "text-slate-900")}>{val.title}</h3>
                  <p className={cn("text-sm leading-relaxed", dark ? "text-slate-400" : "text-slate-500")}>{val.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-br from-indigo-600 to-violet-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-5">
            ¿Quieres formar parte de la historia?
          </h2>
          <p className="text-indigo-100 mb-8 text-lg">
            Únete a más de 500 empresas que ya automatizan su gestión de inventario.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a
              href={`${APP_URL}/#/register`}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-xl hover:-translate-y-0.5"
            >
              Empezar gratis <ArrowRight size={18} />
            </a>
            <Link
              to="/contacto"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-white/30 text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
            >
              Contactar
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
