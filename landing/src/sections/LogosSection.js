const LOGOS = [
  { name: 'WooCommerce', color: '#7f54b3' },
  { name: 'Shopify',     color: '#95bf47' },
  { name: 'PrestaShop',  color: '#df0067' },
  { name: 'Odoo',        color: '#714b67' },
  { name: 'Dolibarr',    color: '#4c9be8' },
  { name: 'WordPress',   color: '#21759b' },
];

const TRACK = [...LOGOS, ...LOGOS];

function LogoPill({ logo }) {
  return (
    <div className="flex items-center gap-2 bg-white shadow-sm border border-slate-100 rounded-full px-4 py-2 shrink-0">
      <span
        className="w-2.5 h-2.5 rounded-full shrink-0"
        style={{ backgroundColor: logo.color }}
      />
      <span className="text-sm font-medium text-slate-700 whitespace-nowrap">
        {logo.name}
      </span>
    </div>
  );
}

export default function LogosSection() {
  return (
    <section className="bg-white border-t border-b border-slate-100 py-10 overflow-hidden">
      <p className="text-center text-xs uppercase tracking-widest text-slate-400 mb-6">
        Integra con las plataformas que ya usas
      </p>
      <div className="overflow-hidden" role="region" aria-label="Plataformas integradas">
        <div className="animate-ticker flex gap-6 w-max" aria-hidden="true">
          {TRACK.map((logo, i) => (
            <LogoPill key={i} logo={logo} />
          ))}
        </div>
      </div>
    </section>
  );
}
