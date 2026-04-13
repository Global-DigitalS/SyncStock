// landing/src/sections/CtaSection.js
import { useApp } from '../context/AppContext';

const DEFAULT_CTA = {
  title: '¿Listo para sincronizar\ntu inventario?',
  subtitle: '14 días gratis. Sin tarjeta de crédito. Cancela cuando quieras.',
  button_text: 'Empezar gratis ahora',
};

export default function CtaSection() {
  const { content, APP_URL } = useApp();
  const cta = { ...DEFAULT_CTA, ...(content?.cta_final || {}) };
  const titleLines = cta.title.split('\n');

  return (
    <section className="bg-slate-900 py-20 lg:py-28">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="font-display text-4xl lg:text-5xl font-extrabold text-white tracking-tight mb-4">
          {titleLines.map((line, i) => <span key={i} className="block">{line}</span>)}
        </h2>
        <p className="text-slate-400 text-lg mb-10">{cta.subtitle}</p>
        <div className="flex flex-wrap gap-4 justify-center">
          <a
            href={`${APP_URL}/#/register`}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-4 rounded-xl text-sm shadow-xl shadow-indigo-500/25 transition-all"
          >
            {cta.button_text} →
          </a>
          <a
            href="/contacto"
            className="inline-flex items-center gap-2 bg-white/8 border border-white/12 hover:bg-white/12 text-slate-300 font-semibold px-7 py-4 rounded-xl text-sm transition-all"
          >
            Reservar una demo
          </a>
        </div>
      </div>
    </section>
  );
}
