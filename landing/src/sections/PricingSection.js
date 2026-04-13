// landing/src/sections/PricingSection.js
import { useState } from 'react';
import { Check } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';

function PlanCard({ plan, billingCycle, APP_URL }) {
  const featured = plan.is_featured || plan.name?.toLowerCase().includes('pro');
  const price = billingCycle === 'annual'
    ? (plan.price_annual ?? Math.round((plan.price_monthly ?? plan.price ?? 0) * 0.8))
    : (plan.price_monthly ?? plan.price ?? 0);

  const features = plan.features || [];

  return (
    <div className={cn(
      'relative bg-white rounded-2xl p-7 flex flex-col gap-5 border transition-all',
      featured
        ? 'border-indigo-500 border-2 shadow-xl shadow-indigo-100 ring-4 ring-indigo-50'
        : 'border-slate-200 hover:border-indigo-200 hover:shadow-lg hover:shadow-slate-100'
    )}>
      {featured && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] font-bold px-4 py-1 rounded-full whitespace-nowrap">
          ⭐ Más popular
        </div>
      )}

      <div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">{plan.name}</p>
        <div className="flex items-end gap-1 mb-1">
          <span className="font-display text-4xl font-extrabold text-slate-900 tracking-tight">
            {price === 0 ? 'Gratis' : `${price}€`}
          </span>
          {price > 0 && <span className="text-slate-400 text-sm mb-1.5">/mes</span>}
        </div>
        {billingCycle === 'annual' && price > 0 && (
          <p className="text-xs text-emerald-600 font-semibold">Ahorra 20% con pago anual</p>
        )}
        <p className="text-slate-400 text-sm mt-1">{plan.description || ''}</p>
      </div>

      <hr className="border-slate-100" />

      <ul className="flex flex-col gap-2.5 flex-1">
        {features.map((feat, i) => (
          <li key={i} className="flex items-start gap-2.5 text-sm text-slate-600">
            <Check size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
            {typeof feat === 'string' ? feat : feat.label || feat.text || JSON.stringify(feat)}
          </li>
        ))}
      </ul>

      <a
        href={`${APP_URL}/#/register`}
        className={cn(
          'block text-center py-3 rounded-xl text-sm font-bold transition-all',
          featured
            ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-500/20'
            : 'bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100'
        )}
      >
        {price === 0 ? 'Empezar gratis' : featured ? 'Probar 14 días gratis' : 'Elegir plan'}
      </a>
    </div>
  );
}

export default function PricingSection() {
  const { plans, APP_URL } = useApp();
  const [billingCycle, setBillingCycle] = useState('monthly');

  const activePlans = (plans || [])
    .filter((p) => p.is_active !== false)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

  if (activePlans.length === 0) return null;

  return (
    <section className="bg-slate-50 py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">Precios</p>
          <h2 className="font-display text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            Transparente. Sin sorpresas.
          </h2>
          <p className="text-slate-500 text-lg max-w-md mx-auto mb-8">
            Empieza gratis. Escala cuando lo necesites.
          </p>

          {/* Toggle mensual / anual */}
          <div className="inline-flex items-center gap-3 bg-white border border-slate-200 rounded-xl px-4 py-2 shadow-sm">
            <span className={cn('text-sm font-semibold', billingCycle === 'monthly' ? 'text-slate-900' : 'text-slate-400')}>
              Mensual
            </span>
            <button
              onClick={() => setBillingCycle(c => c === 'monthly' ? 'annual' : 'monthly')}
              className={cn(
                'relative w-11 h-6 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                billingCycle === 'annual' ? 'bg-indigo-600' : 'bg-slate-200'
              )}
              aria-label="Cambiar ciclo de facturación"
            >
              <span className={cn(
                'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                billingCycle === 'annual' && 'translate-x-5'
              )} />
            </button>
            <span className={cn('text-sm font-semibold', billingCycle === 'annual' ? 'text-slate-900' : 'text-slate-400')}>
              Anual
            </span>
            <span className="bg-emerald-100 text-emerald-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
              Ahorra 20%
            </span>
          </div>
        </div>

        <div className={cn(
          'grid gap-5',
          activePlans.length === 1 ? 'max-w-sm mx-auto' :
          activePlans.length === 2 ? 'md:grid-cols-2 max-w-2xl mx-auto' :
          'md:grid-cols-3'
        )}>
          {activePlans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} billingCycle={billingCycle} APP_URL={APP_URL} />
          ))}
        </div>
      </div>
    </section>
  );
}
