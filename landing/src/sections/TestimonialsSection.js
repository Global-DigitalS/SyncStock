// landing/src/sections/TestimonialsSection.js
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';
import { useReveal } from '../hooks/useReveal';

const DEFAULT_TESTIMONIALS = [
  {
    quote: 'Pasamos de actualizar el stock a mano cada día a tenerlo sincronizado en tiempo real. Ahorramos 2 horas diarias y eliminamos los errores de stock.',
    author: 'Ana Martínez',
    role: 'CEO · TecnoDistrib SL',
  },
  {
    quote: 'Tenemos 8 proveedores y 3 tiendas. Antes era un caos. Ahora SyncStock lo gestiona todo solo y solo intervenimos cuando hay una alerta.',
    author: 'Jorge López',
    role: 'Director de Operaciones · PartsMadrid',
  },
  {
    quote: 'La integración con Odoo fue clave. En menos de una semana teníamos todos los catálogos sincronizados y el equipo de ventas trabajando con datos actualizados.',
    author: 'Sara Ruiz',
    role: 'IT Manager · Grupo Electro',
  },
];

const AVATAR_COLORS = ['bg-indigo-500', 'bg-violet-500', 'bg-emerald-500', 'bg-cyan-500'];

function TestimonialCard({ testimonial, index }) {
  const ref = useReveal(0.1);
  const initials = (testimonial.author || '?')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('');

  return (
    <div
      ref={ref}
      className="animate-reveal bg-slate-50 border border-slate-100 rounded-2xl p-6 flex flex-col gap-4"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex gap-0.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <span key={i} className="text-amber-400 text-sm">★</span>
        ))}
      </div>
      <p className="text-slate-600 text-sm leading-relaxed italic flex-1">
        "{testimonial.quote}"
      </p>
      <div className="flex items-center gap-3">
        <div className={cn('w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold', AVATAR_COLORS[index % AVATAR_COLORS.length])}>
          {initials}
        </div>
        <div>
          <div className="text-sm font-bold text-slate-900">{testimonial.author}</div>
          <div className="text-xs text-slate-400">{testimonial.role}</div>
        </div>
      </div>
    </div>
  );
}

export default function TestimonialsSection() {
  const { content } = useApp();
  const testimonials = content?.testimonials?.length > 0
    ? content.testimonials
    : DEFAULT_TESTIMONIALS;

  return (
    <section className="bg-white py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">Testimonios</p>
          <h2 className="font-display text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            Lo que dicen nuestros clientes
          </h2>
          <p className="text-slate-500 text-lg max-w-md mx-auto">
            Empresas reales. Resultados reales.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {testimonials.map((t, i) => (
            <TestimonialCard key={t.author || i} testimonial={t} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
