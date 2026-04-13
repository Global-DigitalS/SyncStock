// landing/src/sections/HowItWorksSection.js
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';
import { useReveal } from '../hooks/useReveal';

const DEFAULT_STEPS = [
  {
    title: 'Conecta un proveedor',
    description: 'Añade la URL, FTP o sube el archivo CSV/XLSX de tu proveedor. SyncStock mapea las columnas automáticamente.',
  },
  {
    title: 'Define tus reglas',
    description: 'Configura márgenes, exclusiones y alertas de precio. Tú controlas qué se publica y cómo se calculan los precios.',
  },
  {
    title: 'Activa la sincronización',
    description: 'Tu tienda se actualiza automáticamente cada vez que el proveedor cambia stock o precios. 24/7 sin intervención.',
  },
];

function Step({ step, number }) {
  const ref = useReveal(0.15);
  return (
    <div
      ref={ref}
      className="animate-reveal flex flex-col items-center text-center relative"
      style={{ animationDelay: `${(number - 1) * 120}ms` }}
    >
      {/* Number circle */}
      <div className={cn(
        'w-14 h-14 rounded-full flex items-center justify-center font-display font-extrabold text-xl mb-5 border-2 transition-all z-10 relative',
        number === 1
          ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg shadow-indigo-500/30'
          : 'bg-white border-indigo-200 text-indigo-600'
      )}>
        {number}
      </div>

      <h3 className="font-display font-bold text-slate-900 text-lg mb-2">
        {step.title}
      </h3>
      <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
        {step.description}
      </p>
    </div>
  );
}

export default function HowItWorksSection() {
  const { content } = useApp();
  const steps = content?.how_it_works?.length > 0 ? content.how_it_works : DEFAULT_STEPS;

  return (
    <section className="bg-white py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">¿Cómo funciona?</p>
          <h2 className="font-display text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            En marcha en menos de 5 minutos
          </h2>
          <p className="text-slate-500 text-lg max-w-md mx-auto">
            Sin código, sin instalaciones, sin configuraciones complejas.
          </p>
        </div>

        {/* Steps grid with connecting line */}
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-6">
          {/* Connecting line (desktop only) */}
          <div
            aria-hidden="true"
            className="hidden md:block absolute top-7 left-[22%] right-[22%] h-px bg-gradient-to-r from-indigo-200 via-indigo-300 to-indigo-200"
          />

          {steps.slice(0, 3).map((step, i) => (
            <Step key={step.title || i} step={step} number={i + 1} />
          ))}
        </div>
      </div>
    </section>
  );
}
