// landing/src/sections/HeroSection.js
import { Database, CheckCircle2, RefreshCw, BarChart3 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';

const DEFAULT_HERO = {
  badge: 'Sincronización en tiempo real',
  title: 'Inventario B2B\nsin fricciones',
  subtitle: 'Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente. Sin código. Sin errores manuales.',
  cta_primary: 'Prueba gratis 14 días',
  cta_secondary: 'Ver demo en vivo',
  social_proof_text: 'Usado por 500+ empresas en España y LATAM',
};

function DashboardMockup() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl shadow-indigo-100 overflow-hidden w-full max-w-md">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-100">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <div className="w-3 h-3 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 mx-3 h-6 rounded bg-white border border-slate-200 text-[10px] flex items-center px-3 text-slate-400">
          app.syncstock.io/dashboard
        </div>
      </div>
      {/* Body */}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-700">Panel general</span>
          <div className="flex gap-1.5">
            <span className="text-[10px] bg-indigo-50 text-indigo-600 font-semibold px-2 py-1 rounded">Sync activa</span>
          </div>
        </div>
        {/* Stats */}
        <div className="grid grid-cols-4 gap-2">
          {[
            { val: '1.247', label: 'Productos', color: 'text-indigo-600' },
            { val: '12',    label: 'Proveedores', color: 'text-emerald-600' },
            { val: '3',     label: 'Tiendas', color: 'text-amber-600' },
            { val: '99%',   label: 'Uptime', color: 'text-violet-600' },
          ].map((s) => (
            <div key={s.label} className="bg-slate-50 rounded-xl p-2.5 text-center">
              <div className={cn('text-sm font-bold font-display', s.color)}>{s.val}</div>
              <div className="text-[9px] text-slate-400 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
        {/* Supplier table */}
        <div className="rounded-xl overflow-hidden border border-slate-100">
          {[
            { name: 'Proveedor Alpha', products: '342', status: 'sync' },
            { name: 'Tech Distributors', products: '891', status: 'ok' },
            { name: 'Global Parts SL',  products: '214', status: 'ok' },
          ].map((row) => (
            <div key={row.name} className="flex items-center justify-between px-3 py-2 border-b border-slate-50 last:border-0 hover:bg-slate-50">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded bg-indigo-50 flex items-center justify-center">
                  <Database size={9} className="text-indigo-500" />
                </div>
                <span className="text-[10px] font-semibold text-slate-700">{row.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-slate-400">{row.products} prods.</span>
                {row.status === 'sync' ? (
                  <span className="flex items-center gap-0.5 text-amber-500 text-[9px] font-semibold">
                    <RefreshCw size={8} className="animate-spin" /> Sync
                  </span>
                ) : (
                  <span className="flex items-center gap-0.5 text-emerald-500 text-[9px] font-semibold">
                    <CheckCircle2 size={8} /> OK
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
        {/* Mini chart */}
        <div className="flex items-end gap-1 h-12 bg-slate-50 rounded-xl px-3 py-2">
          {[40, 65, 45, 80, 60, 90, 75, 95, 70, 88, 85, 92].map((h, i) => (
            <div
              key={i}
              className={cn('flex-1 rounded-sm transition-all', i === 11 ? 'bg-indigo-600' : 'bg-indigo-200')}
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function FloatingBadge({ children, className = '' }) {
  return (
    <div className={cn(
      'absolute bg-white border border-slate-200 rounded-xl px-3 py-2 shadow-lg shadow-slate-100 flex items-center gap-2 text-xs font-semibold text-slate-700 animate-float z-10',
      className
    )}>
      {children}
    </div>
  );
}

export default function HeroSection() {
  const { content, APP_URL } = useApp();
  const hero = { ...DEFAULT_HERO, ...(content?.hero || {}) };

  const titleLines = hero.title.split('\n');

  return (
    <section className="relative pt-28 pb-20 lg:pt-36 lg:pb-28 bg-gradient-to-b from-white via-white to-slate-50 overflow-hidden">
      {/* Subtle bg decoration */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-32 -right-32 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-20 w-64 h-64 bg-violet-500/5 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">

          {/* LEFT — copy */}
          <div className="flex flex-col gap-6 animate-slide-up">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-full px-4 py-1.5 text-sm font-semibold w-fit">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse-dot" />
              {hero.badge}
            </div>

            {/* H1 */}
            <h1 className="font-display text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.05]">
              {titleLines.map((line, i) => (
                <span key={i} className={cn('block', i > 0 && 'text-indigo-600')}>
                  {line}
                </span>
              ))}
            </h1>

            {/* Subtitle */}
            <p className="text-lg text-slate-500 leading-relaxed max-w-lg">
              {hero.subtitle}
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-3">
              <a
                href={`${APP_URL}/#/register`}
                className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-7 py-3.5 rounded-xl text-sm shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all"
              >
                {hero.cta_primary} →
              </a>
              <a
                href={`${APP_URL}/#/demo`}
                className="inline-flex items-center gap-2 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 font-semibold px-6 py-3.5 rounded-xl text-sm transition-all hover:bg-slate-50"
              >
                ▶ {hero.cta_secondary}
              </a>
            </div>

            {/* Social proof */}
            <div className="flex items-center gap-3">
              <div className="flex -space-x-2">
                {['bg-indigo-500', 'bg-violet-500', 'bg-cyan-500', 'bg-emerald-500'].map((c, i) => (
                  <div key={i} className={cn('w-8 h-8 rounded-full border-2 border-white flex items-center justify-center text-white text-[10px] font-bold', c)}>
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <p className="text-sm text-slate-500">
                {hero.social_proof_text}
              </p>
            </div>
          </div>

          {/* RIGHT — dashboard + floating badges */}
          <div className="relative hidden lg:flex items-center justify-center animate-slide-left">
            {/* Floating badge 1 */}
            <FloatingBadge className="-top-6 -left-10">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              1.247 productos sync
            </FloatingBadge>

            {/* Floating badge 2 */}
            <FloatingBadge className="bottom-12 -right-8">
              <span className="w-2 h-2 rounded-full bg-indigo-400" />
              99.9% uptime garantizado
            </FloatingBadge>

            {/* Floating badge 3 */}
            <FloatingBadge className="-bottom-4 left-8">
              <BarChart3 size={13} className="text-violet-500" />
              Sync cada hora
            </FloatingBadge>

            <DashboardMockup />
          </div>

        </div>
      </div>
    </section>
  );
}
