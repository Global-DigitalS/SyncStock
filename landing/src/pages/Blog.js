import { Link } from "react-router-dom";
import { ArrowRight, Clock, Tag, Rss } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";

const SAMPLE_POSTS = [
  {
    slug: "sincronizacion-inventario-woocommerce",
    title: "Cómo sincronizar tu inventario con WooCommerce automáticamente",
    excerpt: "Aprende a conectar tus proveedores FTP con WooCommerce en menos de 10 minutos usando StockHUB. Sin código, sin complicaciones.",
    category: "Guías",
    readTime: "5 min",
    date: "2025-02-15",
    featured: true,
  },
  {
    slug: "gestion-margenes-catalogo-b2b",
    title: "Estrategias de margen para catálogos B2B: guía completa",
    excerpt: "Descubre cómo configurar reglas de precio inteligentes por categoría, proveedor y canal de venta para maximizar tu rentabilidad.",
    category: "Estrategia",
    readTime: "8 min",
    date: "2025-01-28",
  },
  {
    slug: "integracion-dolibarr-stockhub",
    title: "Integración StockHUB con Dolibarr: sincronización en tiempo real",
    excerpt: "Tutorial paso a paso para conectar tu ERP Dolibarr con StockHUB y mantener productos, clientes y pedidos siempre sincronizados.",
    category: "Integraciones",
    readTime: "6 min",
    date: "2025-01-10",
  },
  {
    slug: "formatos-proveedores-ftp-sftp",
    title: "FTP, SFTP, CSV o XML: ¿qué formato es mejor para tu proveedor?",
    excerpt: "Comparativa de los formatos de conexión más habituales con proveedores de catálogos y cuándo usar cada uno.",
    category: "Guías",
    readTime: "4 min",
    date: "2024-12-20",
  },
  {
    slug: "prestashop-multitienda-gestion",
    title: "Gestión multi-tienda PrestaShop con un único panel",
    excerpt: "Cómo administrar varias tiendas PrestaShop desde una sola plataforma centralizada sin duplicar trabajo.",
    category: "Guías",
    readTime: "7 min",
    date: "2024-12-05",
  },
  {
    slug: "historial-precios-analisis",
    title: "Cómo usar el historial de precios para tomar mejores decisiones",
    excerpt: "El historial de precios de StockHUB te permite detectar tendencias, negociar mejor con proveedores y optimizar tu política de precios.",
    category: "Estrategia",
    readTime: "5 min",
    date: "2024-11-18",
  },
];

const CATEGORIES = ["Todos", "Guías", "Integraciones", "Estrategia", "Novedades"];

export default function Blog() {
  const { branding, theme, APP_URL } = useApp();
  const dark = theme === "dark";

  const featured = SAMPLE_POSTS.find(p => p.featured);
  const rest = SAMPLE_POSTS.filter(p => !p.featured);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", { year: "numeric", month: "long", day: "numeric" });
  };

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>

      {/* Hero */}
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <SectionLabel>Blog</SectionLabel>
          <SectionTitle className={cn("mt-4", dark ? "text-white" : "")}>
            Recursos y guías para <span className="text-indigo-600">escalar tu negocio</span>
          </SectionTitle>
          <SectionSubtitle className="mt-4 max-w-2xl mx-auto">
            Tutoriales, estrategias y novedades sobre gestión de inventario B2B, integraciones y automatización.
          </SectionSubtitle>

          {/* Subscribe bar */}
          <div className={cn(
            "flex flex-col sm:flex-row items-center gap-3 max-w-md mx-auto mt-8 p-2 rounded-xl border",
            dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200 shadow-sm"
          )}>
            <Rss size={18} className="text-indigo-500 flex-shrink-0" />
            <input
              type="email"
              placeholder="tu@empresa.com — recibe artículos nuevos"
              className={cn(
                "flex-1 bg-transparent text-sm outline-none px-2",
                dark ? "text-white placeholder-slate-400" : "text-slate-700 placeholder-slate-400"
              )}
            />
            <button className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors flex-shrink-0">
              Suscribirse
            </button>
          </div>
        </div>
      </section>

      {/* Category pills */}
      <section className={cn("border-b", dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-slate-50")}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex gap-2 overflow-x-auto">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors",
                cat === "Todos"
                  ? "bg-indigo-600 text-white"
                  : dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-600 hover:text-slate-900 hover:bg-white"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </section>

      {/* Content */}
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

          {/* Featured post */}
          {featured && (
            <div className={cn(
              "mb-12 rounded-2xl border overflow-hidden",
              dark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"
            )}>
              <div className="grid lg:grid-cols-2">
                {/* Image placeholder */}
                <div className={cn("h-64 lg:h-auto flex items-center justify-center", dark ? "bg-slate-700" : "bg-indigo-50")}>
                  <div className={cn("text-center p-12", dark ? "" : "")}>
                    <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <Tag size={28} className="text-white" />
                    </div>
                    <span className="text-xs font-bold text-indigo-500 bg-indigo-100 px-3 py-1 rounded-full">Artículo destacado</span>
                  </div>
                </div>
                {/* Content */}
                <div className="p-8 flex flex-col justify-center">
                  <div className="flex items-center gap-3 mb-4">
                    <span className={cn("text-xs font-bold px-3 py-1 rounded-full", dark ? "bg-indigo-950 text-indigo-400" : "bg-indigo-100 text-indigo-700")}>
                      {featured.category}
                    </span>
                    <span className={cn("flex items-center gap-1 text-xs", dark ? "text-slate-400" : "text-slate-400")}>
                      <Clock size={12} /> {featured.readTime}
                    </span>
                  </div>
                  <h2 className={cn("text-2xl font-bold mb-4 leading-tight", dark ? "text-white" : "text-slate-900")}>
                    {featured.title}
                  </h2>
                  <p className={cn("text-sm leading-relaxed mb-6", dark ? "text-slate-400" : "text-slate-500")}>
                    {featured.excerpt}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className={cn("text-xs", dark ? "text-slate-500" : "text-slate-400")}>
                      {formatDate(featured.date)}
                    </span>
                    <button className={cn(
                      "inline-flex items-center gap-2 text-sm font-semibold transition-colors",
                      dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700"
                    )}>
                      Leer artículo <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Post grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {rest.map((post, i) => (
              <div
                key={i}
                className={cn(
                  "flex flex-col rounded-2xl border overflow-hidden card-hover",
                  dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100 shadow-sm"
                )}
              >
                {/* Colored header */}
                <div className={cn(
                  "h-36 flex items-center justify-center",
                  i % 3 === 0 ? dark ? "bg-indigo-950" : "bg-indigo-50"
                    : i % 3 === 1 ? dark ? "bg-emerald-950" : "bg-emerald-50"
                    : dark ? "bg-violet-950" : "bg-violet-50"
                )}>
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center",
                    i % 3 === 0 ? "bg-indigo-600" : i % 3 === 1 ? "bg-emerald-600" : "bg-violet-600"
                  )}>
                    <Tag size={22} className="text-white" />
                  </div>
                </div>
                {/* Content */}
                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={cn("text-xs font-semibold px-2.5 py-0.5 rounded-full", dark ? "bg-slate-700 text-slate-300" : "bg-slate-100 text-slate-600")}>
                      {post.category}
                    </span>
                    <span className={cn("flex items-center gap-1 text-xs", dark ? "text-slate-500" : "text-slate-400")}>
                      <Clock size={10} /> {post.readTime}
                    </span>
                  </div>
                  <h3 className={cn("font-bold mb-2 leading-snug", dark ? "text-white" : "text-slate-900")}>
                    {post.title}
                  </h3>
                  <p className={cn("text-xs leading-relaxed flex-1 mb-4", dark ? "text-slate-400" : "text-slate-500")}>
                    {post.excerpt}
                  </p>
                  <div className="flex items-center justify-between mt-auto">
                    <span className={cn("text-xs", dark ? "text-slate-500" : "text-slate-400")}>
                      {formatDate(post.date)}
                    </span>
                    <button className={cn(
                      "text-xs font-semibold flex items-center gap-1 transition-colors",
                      dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700"
                    )}>
                      Leer <ArrowRight size={12} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Coming soon note */}
          <div className={cn(
            "mt-12 p-8 rounded-2xl border text-center",
            dark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"
          )}>
            <p className={cn("text-sm font-medium mb-2", dark ? "text-slate-300" : "text-slate-700")}>
              Más artículos en camino
            </p>
            <p className={cn("text-sm", dark ? "text-slate-500" : "text-slate-500")}>
              Suscríbete al newsletter para recibir los nuevos artículos directamente en tu email.
            </p>
          </div>

        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-br from-indigo-600 to-violet-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl lg:text-3xl font-bold text-white mb-4">
            ¿Preparado para automatizar tu inventario?
          </h2>
          <p className="text-indigo-100 mb-6">14 días de prueba gratuita. Sin tarjeta de crédito.</p>
          <a
            href={`${APP_URL}/#/register`}
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-indigo-600 font-bold rounded-xl hover:bg-slate-50 transition-all shadow-xl"
          >
            Empezar gratis <ArrowRight size={18} />
          </a>
        </div>
      </section>

    </div>
  );
}
