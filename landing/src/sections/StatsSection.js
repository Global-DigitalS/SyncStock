// landing/src/sections/StatsSection.js
import { useRef, useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useCountUp } from '../hooks/useCountUp';

const DEFAULT_STATS = [
  { stat: '500+',  text: 'Empresas activas',      change: '↑ creciendo' },
  { stat: '2M+',   text: 'Productos gestionados',  change: '↑ en tiempo real' },
  { stat: '99.9%', text: 'Uptime garantizado',     change: '↑ SLA enterprise' },
  { stat: '4.9★',  text: 'Valoración media',       change: '↑ 500+ reseñas' },
];

function StatBox({ stat, text, change, trigger }) {
  const animated = useCountUp(stat, 1600, trigger);
  return (
    <div className="text-center">
      <div className="font-display text-5xl font-extrabold text-white tracking-tight mb-1">
        {trigger ? animated : '0'}
      </div>
      <div className="text-indigo-200 text-sm mb-1">{text}</div>
      <div className="text-cyan-300 text-xs font-semibold">{change}</div>
    </div>
  );
}

export default function StatsSection() {
  const { content } = useApp();
  const stats = content?.benefits?.items?.length > 0
    ? content.benefits.items
    : DEFAULT_STATS;

  const sectionRef = useRef(null);
  const [triggered, setTriggered] = useState(false);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setTriggered(true); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="bg-gradient-to-r from-indigo-600 to-indigo-700 py-16 lg:py-20"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-10">
          {stats.slice(0, 4).map((s, i) => (
            <StatBox
              key={s.text || i}
              stat={s.stat}
              text={s.text || s.label || ''}
              change={s.change || ''}
              trigger={triggered}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
