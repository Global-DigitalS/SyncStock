// landing/src/sections/FeaturesSection.js
import {
  RefreshCw, Store, BarChart3, Calculator,
  Bell, Webhook
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';
import { useReveal } from '../hooks/useReveal';

const ICON_MAP = {
  RefreshCw, Store, BarChart3, Calculator, Bell, Webhook,
  Zap: RefreshCw, Database: BarChart3, Shield: Bell,
  Layers: Store, Clock: Bell, Users: Store,
};

const DEFAULT_FEATURES = [
  {
    icon: 'RefreshCw',
    title: 'Sincronización multi-proveedor',
    description: 'Conecta FTP, SFTP, URL, CSV, XLSX y XML. SyncStock descarga y actualiza tu catálogo automáticamente cada hora.',
    wide: true,
  },
  {
    icon: 'Store',
    title: 'Multi-tienda',
    description: 'Publica en WooCommerce, Shopify y PrestaShop simultáneamente. Un catálogo, todas tus tiendas al día.',
  },
  {
    icon: 'BarChart3',
    title: 'Historial de precios',
    description: 'Detecta cambios de precio automáticamente y alerta cuando un proveedor supera el umbral configurado.',
  },
  {
    icon: 'Calculator',
    title: 'Reglas de margen',
    description: 'Define márgenes por categoría o proveedor. Los precios de venta se calculan solos en cada sync.',
  },
  {
    icon: 'Bell',
    title: 'Alertas en tiempo real',
    description: 'Stock bajo, precios fuera de rango, sync fallida. Notificaciones instantáneas vía WebSocket.',
  },
  {
    icon: 'Webhook',
    title: 'CRM integrado',
    description: 'Sincroniza productos, clientes y pedidos con Dolibarr y Odoo. Bidireccional y sin duplicados.',
  },
];

function FeatureCard({ feature, index }) {
  const ref = useReveal(0.1);
  const Icon = ICON_MAP[feature.icon] || RefreshCw;

  return (
    <div
      ref={ref}
      className={cn(
        'animate-reveal bg-white border border-slate-200 rounded-2xl p-6 hover:border-indigo-200 hover:shadow-lg hover:shadow-indigo-50 transition-all duration-300',
        feature.wide && 'lg:col-span-2'
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center mb-4">
        <Icon size={20} className="text-indigo-600" />
      </div>
      <h3 className="font-display font-bold text-slate-900 mb-2 text-base">
        {feature.title}
      </h3>
      <p className="text-sm text-slate-500 leading-relaxed">
        {feature.description}
      </p>

      {/* Mini progress bars for the wide card */}
      {feature.wide && (
        <div className="mt-4 space-y-2">
          {[
            { label: 'Proveedor Alpha', pct: 78, color: 'bg-indigo-500' },
            { label: 'Tech Distributors', pct: 92, color: 'bg-emerald-500' },
            { label: 'Global Parts SL', pct: 45, color: 'bg-amber-500' },
          ].map((row) => (
            <div key={row.label} className="flex items-center gap-3">
              <span className="text-[10px] text-slate-400 w-28 truncate">{row.label}</span>
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className={cn('h-full rounded-full transition-all', row.color)} style={{ width: `${row.pct}%` }} />
              </div>
              <span className="text-[10px] font-semibold text-slate-500">{row.pct}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FeaturesSection() {
  const { content } = useApp();
  const features = content?.features?.length > 0
    ? content.features.map((f, i) => ({ ...f, wide: i === 0 }))
    : DEFAULT_FEATURES;

  return (
    <section className="bg-slate-50 py-20 lg:py-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">Funcionalidades</p>
          <h2 className="font-display text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            Todo lo que necesitas para<br />gestionar tu inventario
          </h2>
          <p className="text-slate-500 text-lg max-w-xl leading-relaxed">
            Diseñado para equipos B2B que trabajan con múltiples proveedores y tiendas simultáneas.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <FeatureCard key={f.title || i} feature={f} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
