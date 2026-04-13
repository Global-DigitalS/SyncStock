# Landing Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar la landing de SyncStock con estilo Clean Enterprise (blanco + indigo), animaciones flotantes + contadores, y hero split — separando Home.js en 9 secciones independientes. Los textos de todas las secciones se editan desde AdminLanding del frontend.

**Architecture:** Se crea `landing/src/sections/` con un archivo por sección. `Home.js` queda como orquestador puro que importa las secciones. El Navbar se actualiza para mostrar glassmorphism permanente. El Footer se actualiza a estilo oscuro. `AdminLanding.jsx` recibe 2 nuevos campos en Hero y un nuevo tab "Cómo funciona".

**Tech Stack:** React 18, Tailwind CSS 3.4, Lucide React, @radix-ui/react-accordion, CSS keyframes nativos, IntersectionObserver API, requestAnimationFrame — sin dependencias nuevas.

---

## Mapa de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `landing/public/index.html` | Modificar | Añadir Google Fonts (Manrope) |
| `landing/src/index.css` | Modificar | Añadir keyframes: `revealScale`, `pulseDot`, `.animate-ticker`, `.animate-reveal` |
| `landing/src/hooks/useCountUp.js` | Crear | Hook para contar de 0 a N con easing |
| `landing/src/hooks/useReveal.js` | Crear | Hook IntersectionObserver → clase `revealed` |
| `landing/src/sections/HeroSection.js` | Crear | Hero split: texto + dashboard mockup + badges flotantes |
| `landing/src/sections/LogosSection.js` | Crear | Marquee infinito de logos de integración |
| `landing/src/sections/FeaturesSection.js` | Crear | Bento grid 3×2 de features |
| `landing/src/sections/HowItWorksSection.js` | Crear | 3 pasos numerados con línea conectora |
| `landing/src/sections/StatsSection.js` | Crear | Banda indigo con 4 contadores animados |
| `landing/src/sections/PricingSection.js` | Crear | 3 planes con toggle mensual/anual |
| `landing/src/sections/TestimonialsSection.js` | Crear | Grid 3 columnas de testimonios |
| `landing/src/sections/FaqSection.js` | Crear | Acordeón Radix de FAQs |
| `landing/src/sections/CtaSection.js` | Crear | CTA final fondo slate-900 |
| `landing/src/components/Navbar.js` | Modificar | Glassmorphism permanente, sin modo transparente inicial |
| `landing/src/components/Footer.js` | Modificar | Fondo oscuro slate-950, trust badges |
| `landing/src/pages/Home.js` | Modificar | Reducir a orquestador puro (~30 líneas) |
| `frontend/src/pages/AdminLanding.jsx` | Modificar | +2 campos en Hero tab, +tab "Cómo funciona" |

---

## Task 1: Google Fonts + CSS keyframes nuevos

**Files:**
- Modify: `landing/public/index.html`
- Modify: `landing/src/index.css`

- [ ] **Step 1: Añadir Manrope a index.html**

Añadir dentro de `<head>`, antes del cierre `</head>`, justo después de la línea `<meta name="author" content="SyncStock" />`:

```html
<!-- Google Fonts: Manrope (display) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Añadir keyframes a index.css**

Al final del bloque `/* KEYFRAMES */` (después de la línea `@keyframes borderGlow { ... }`, antes de `/* CLASES DE ANIMACIÓN SIMPLES */`), añadir:

```css
@keyframes revealScale {
  from { opacity: 0; transform: scale(0.94) translateY(14px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.75); }
}

@keyframes marquee {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
```

- [ ] **Step 3: Añadir clases de animación nuevas**

Al final del bloque `/* CLASES DE ANIMACIÓN SIMPLES */` (después de `.animate-spin`), añadir:

```css
.animate-ticker      { animation: marquee 22s linear infinite; }
.animate-reveal      { opacity: 0; }
.animate-reveal.revealed { animation: revealScale 0.55s cubic-bezier(0.16,1,0.3,1) forwards; }
.animate-pulse-dot   { animation: pulseDot 2s ease-in-out infinite; }
```

- [ ] **Step 4: Verificar en navegador**

```bash
cd landing && yarn start
```

Abrir http://localhost:3000, abrir DevTools → Network → filtrar "Manrope" → debe aparecer la fuente cargada. Inspeccionar cualquier elemento con `font-family: Manrope` → debe renderizar con la fuente correcta.

- [ ] **Step 5: Commit**

```bash
git add landing/public/index.html landing/src/index.css
git commit -m "feat(landing): add Manrope font + animation keyframes for redesign"
```

---

## Task 2: Hook useCountUp

**Files:**
- Create: `landing/src/hooks/useCountUp.js`

- [ ] **Step 1: Crear el hook**

```js
// landing/src/hooks/useCountUp.js
import { useState, useEffect, useRef } from 'react';

/**
 * Anima un número de 0 hasta `target` usando requestAnimationFrame.
 * Solo arranca cuando `trigger` es true (útil con IntersectionObserver).
 * Soporta targets con sufijos: "500+" → anima hasta 500, devuelve "500+".
 */
export function useCountUp(rawTarget, duration = 1800, trigger = true) {
  const [display, setDisplay] = useState('0');
  const rafRef = useRef(null);

  useEffect(() => {
    if (!trigger) return;

    const suffix = rawTarget.toString().replace(/[\d.]/g, '');
    const numTarget = parseFloat(rawTarget.toString().replace(/[^\d.]/g, ''));

    if (isNaN(numTarget)) { setDisplay(rawTarget); return; }

    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = Math.floor(eased * numTarget);

      const formatted = numTarget >= 1000
        ? (current / 1000).toFixed(current >= 1000 ? 0 : 1) + 'M'
        : current.toString();

      setDisplay(formatted + suffix);

      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [rawTarget, duration, trigger]);

  return display;
}
```

- [ ] **Step 2: Verificar que no hay errores de lint**

```bash
cd landing && yarn build 2>&1 | grep -E "Error|Warning" | head -20
```

Esperado: sin errores relacionados con `useCountUp.js`.

- [ ] **Step 3: Commit**

```bash
git add landing/src/hooks/useCountUp.js
git commit -m "feat(landing): add useCountUp hook for animated number counters"
```

---

## Task 3: Hook useReveal

**Files:**
- Create: `landing/src/hooks/useReveal.js`

- [ ] **Step 1: Crear el hook**

```js
// landing/src/hooks/useReveal.js
import { useEffect, useRef } from 'react';

/**
 * Devuelve un ref. Cuando el elemento entra en el viewport,
 * añade la clase "revealed" (activa .animate-reveal.revealed en CSS).
 * Se dispara solo una vez por elemento.
 */
export function useReveal(threshold = 0.15) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('revealed');
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return ref;
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/hooks/useReveal.js
git commit -m "feat(landing): add useReveal hook for IntersectionObserver scroll animations"
```

---

## Task 4: HeroSection

**Files:**
- Create: `landing/src/sections/HeroSection.js`

- [ ] **Step 1: Crear HeroSection.js**

```js
// landing/src/sections/HeroSection.js
import { Database, CheckCircle2, RefreshCw, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
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
  const { content, branding, APP_URL } = useApp();
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
            <FloatingBadge className="-top-6 -left-10" style={{ animationDelay: '0s' }}>
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              1.247 productos sync
            </FloatingBadge>

            {/* Floating badge 2 */}
            <FloatingBadge className="bottom-12 -right-8" style={{ animationDelay: '-1.5s' }}>
              <span className="w-2 h-2 rounded-full bg-indigo-400" />
              99.9% uptime garantizado
            </FloatingBadge>

            {/* Floating badge 3 */}
            <FloatingBadge className="-bottom-4 left-8" style={{ animationDelay: '-0.75s' }}>
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
```

- [ ] **Step 2: Verificar renderizado**

Añadir temporalmente `import HeroSection from '../sections/HeroSection';` en Home.js y renderizarlo. Abrir http://localhost:3000. Verificar:
- Badge con punto pulsante
- H1 en dos líneas, segunda en indigo
- 2 botones CTA
- Dashboard mockup visible (desktop)
- Badges flotantes con animación

Revertir el import temporal de Home.js cuando pase al Task 14.

- [ ] **Step 3: Commit**

```bash
git add landing/src/sections/HeroSection.js
git commit -m "feat(landing): add HeroSection - split layout with dashboard mockup and floating badges"
```

---

## Task 5: LogosSection

**Files:**
- Create: `landing/src/sections/LogosSection.js`

- [ ] **Step 1: Crear LogosSection.js**

```js
// landing/src/sections/LogosSection.js
import { cn } from '../components/ui';

const LOGOS = [
  { name: 'WooCommerce',  color: '#7f54b3', initial: 'W' },
  { name: 'Shopify',      color: '#95bf47', initial: 'S' },
  { name: 'PrestaShop',   color: '#df0067', initial: 'P' },
  { name: 'Odoo',         color: '#714b67', initial: 'O' },
  { name: 'Dolibarr',     color: '#1a73e8', initial: 'D' },
  { name: 'WordPress',    color: '#21759b', initial: 'W' },
];

// Duplicar para loop infinito sin salto visual
const TRACK = [...LOGOS, ...LOGOS];

export default function LogosSection() {
  return (
    <section className="bg-white border-y border-slate-100 py-8 overflow-hidden">
      <p className="text-center text-xs font-semibold text-slate-400 uppercase tracking-widest mb-6">
        Integra con las plataformas que ya usas
      </p>
      <div className="overflow-hidden">
        <div className="flex items-center gap-10 animate-ticker w-max">
          {TRACK.map((logo, i) => (
            <div key={i} className="flex items-center gap-2.5 opacity-50 hover:opacity-80 transition-opacity cursor-default select-none">
              <div
                className="w-6 h-6 rounded"
                style={{ background: logo.color }}
              />
              <span className="text-sm font-bold text-slate-600 whitespace-nowrap">
                {logo.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/LogosSection.js
git commit -m "feat(landing): add LogosSection with infinite marquee ticker"
```

---

## Task 6: FeaturesSection

**Files:**
- Create: `landing/src/sections/FeaturesSection.js`

- [ ] **Step 1: Crear FeaturesSection.js**

```js
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
            <FeatureCard key={i} feature={f} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/FeaturesSection.js
git commit -m "feat(landing): add FeaturesSection with bento grid and scroll-reveal animations"
```

---

## Task 7: HowItWorksSection

**Files:**
- Create: `landing/src/sections/HowItWorksSection.js`

- [ ] **Step 1: Crear HowItWorksSection.js**

```js
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

function Step({ step, number, isLast }) {
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
            <Step key={i} step={step} number={i + 1} isLast={i === steps.length - 1} />
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/HowItWorksSection.js
git commit -m "feat(landing): add HowItWorksSection with numbered steps and connecting line"
```

---

## Task 8: StatsSection

**Files:**
- Create: `landing/src/sections/StatsSection.js`

- [ ] **Step 1: Crear StatsSection.js**

```js
// landing/src/sections/StatsSection.js
import { useRef, useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';
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
              key={i}
              stat={s.stat || s.stat}
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
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/StatsSection.js
git commit -m "feat(landing): add StatsSection with animated counters triggered by IntersectionObserver"
```

---

## Task 9: PricingSection

**Files:**
- Create: `landing/src/sections/PricingSection.js`

- [ ] **Step 1: Crear PricingSection.js**

```js
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
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/PricingSection.js
git commit -m "feat(landing): add PricingSection with monthly/annual toggle from AppContext plans"
```

---

## Task 10: TestimonialsSection

**Files:**
- Create: `landing/src/sections/TestimonialsSection.js`

- [ ] **Step 1: Crear TestimonialsSection.js**

```js
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
            <TestimonialCard key={i} testimonial={t} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/TestimonialsSection.js
git commit -m "feat(landing): add TestimonialsSection with scroll-reveal card grid"
```

---

## Task 11: FaqSection

**Files:**
- Create: `landing/src/sections/FaqSection.js`

- [ ] **Step 1: Crear FaqSection.js**

```js
// landing/src/sections/FaqSection.js
import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDown } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../components/ui';

const DEFAULT_FAQ = [
  { question: '¿Cuánto tiempo tarda la configuración inicial?', answer: 'La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas la URL o credenciales FTP de tu proveedor y las claves API de tu tienda.' },
  { question: '¿Qué pasa si el proveedor cambia el formato del archivo?', answer: 'SyncStock detecta cambios de estructura y te notifica inmediatamente. El mapeo de columnas se puede actualizar desde el panel en menos de 2 minutos.' },
  { question: '¿Funciona con múltiples monedas y mercados?', answer: 'Sí. Puedes configurar reglas de margen y precios por mercado. Los precios se calculan automáticamente según las reglas que definas.' },
  { question: '¿Puedo cancelar en cualquier momento?', answer: 'Sí, sin permanencia ni penalizaciones. Si cancelas, tu cuenta pasa a plan Free y mantienes acceso a tus datos.' },
  { question: '¿Mis datos están seguros?', answer: 'Todos los datos se almacenan cifrados. Las credenciales FTP y API se guardan encriptadas y nunca son accesibles en texto plano.' },
];

export default function FaqSection() {
  const { content } = useApp();
  const faq = content?.faq?.length > 0 ? content.faq : DEFAULT_FAQ;

  return (
    <section className="bg-slate-50 py-20 lg:py-28">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-3">FAQ</p>
          <h2 className="font-display text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
            Preguntas frecuentes
          </h2>
          <p className="text-slate-500 text-lg">
            ¿No encuentras tu respuesta? <a href="/contacto" className="text-indigo-600 font-semibold hover:underline">Escríbenos</a>.
          </p>
        </div>

        <Accordion.Root type="single" collapsible className="space-y-3">
          {faq.map((item, i) => (
            <Accordion.Item
              key={i}
              value={`item-${i}`}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden"
            >
              <Accordion.Trigger className="w-full flex items-center justify-between px-6 py-4 text-left text-sm font-semibold text-slate-800 hover:text-indigo-600 transition-colors group">
                {item.question}
                <ChevronDown
                  size={16}
                  className="text-slate-400 group-data-[state=open]:rotate-180 transition-transform flex-shrink-0 ml-3"
                />
              </Accordion.Trigger>
              <Accordion.Content className="overflow-hidden data-[state=open]:animate-accordion-down data-[state=closed]:animate-accordion-up">
                <div className="px-6 pb-5 text-sm text-slate-500 leading-relaxed border-t border-slate-100 pt-4">
                  {item.answer}
                </div>
              </Accordion.Content>
            </Accordion.Item>
          ))}
        </Accordion.Root>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/FaqSection.js
git commit -m "feat(landing): add FaqSection with Radix accordion"
```

---

## Task 12: CtaSection

**Files:**
- Create: `landing/src/sections/CtaSection.js`

- [ ] **Step 1: Crear CtaSection.js**

```js
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
```

- [ ] **Step 2: Commit**

```bash
git add landing/src/sections/CtaSection.js
git commit -m "feat(landing): add CtaSection with dark background and dynamic content"
```

---

## Task 13: Navbar — actualizar glassmorphism permanente

**Files:**
- Modify: `landing/src/components/Navbar.js`

El Navbar actual ya tiene glassmorphism al hacer scroll (`scrolled === true`). El cambio es: mostrar el fondo blanco/blur **siempre** (no solo al hacer scroll), y mantener el comportamiento móvil existente.

- [ ] **Step 1: Actualizar el className del header**

Localizar el bloque:
```js
<header className={cn(
  "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
  scrolled
    ? dark ? "bg-slate-900/95 backdrop-blur-md shadow-lg border-b border-slate-800" : "bg-white/95 backdrop-blur-md shadow-sm border-b border-slate-100"
    : dark ? "bg-transparent" : "bg-transparent"
)}>
```

Reemplazar con:
```js
<header className={cn(
  "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
  dark
    ? "bg-slate-900/95 backdrop-blur-md border-b border-slate-800"
    : "bg-white/92 backdrop-blur-xl border-b border-slate-100",
  scrolled && (dark ? "shadow-lg shadow-slate-900/50" : "shadow-sm shadow-slate-200/60")
)}>
```

- [ ] **Step 2: Actualizar altura del nav a 64px consistente**

Localizar:
```js
<div className="flex items-center justify-between h-16 lg:h-18">
```

Reemplazar con:
```js
<div className="flex items-center justify-between h-16">
```

- [ ] **Step 3: Actualizar estilo del logo text para Manrope**

Localizar:
```js
<span className={cn("font-bold text-lg hidden sm:block", dark ? "text-white" : "text-slate-900")}>
```

Reemplazar con:
```js
<span className={cn("font-display font-bold text-lg hidden sm:block", dark ? "text-white" : "text-slate-900")}>
```

- [ ] **Step 4: Verificar en navegador**

```bash
cd landing && yarn start
```

Abrir http://localhost:3000. Verificar que el Navbar es visible desde el primer scroll position (no transparente). En mobile, abrir el menú hamburguesa y verificar que funciona.

- [ ] **Step 5: Commit**

```bash
git add landing/src/components/Navbar.js
git commit -m "feat(landing): update Navbar - permanent glassmorphism, Manrope font"
```

---

## Task 14: Footer — actualizar a estilo oscuro con trust badges

**Files:**
- Modify: `landing/src/components/Footer.js`

- [ ] **Step 1: Actualizar clases del footer principal**

Localizar:
```js
<footer className={cn(
  "border-t",
  dark ? "bg-slate-900 border-slate-800" : "bg-slate-50 border-slate-200"
)}>
```

Reemplazar con:
```js
<footer className="bg-slate-950 border-t border-slate-900">
```

- [ ] **Step 2: Actualizar clases de textos dentro del footer**

Todos los textos del footer pasan a usar paleta oscura fija (no dependen de `dark`). Aplicar estos reemplazos:

a) Logo text:
```js
// Antes:
className={cn("font-bold text-lg", dark ? "text-white" : "text-slate-900")}
// Después:
className="font-display font-bold text-lg text-white"
```

b) Company description:
```js
// Antes:
className={cn("text-sm leading-relaxed mb-6 font-medium", dark ? "text-slate-400" : "text-slate-600")}
// Después:
className="text-sm leading-relaxed mb-6 text-slate-400"
```

c) Social links (iconos):
```js
// Antes:
className={cn("p-2.5 rounded-lg transition-all hover:scale-110", dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-600 hover:text-indigo-600 hover:bg-indigo-50")}
// Después:
className="p-2.5 rounded-lg transition-all hover:scale-110 text-slate-500 hover:text-white hover:bg-slate-800"
```

d) Column titles:
```js
// Antes:
className={cn("font-bold text-base mb-5", dark ? "text-white" : "text-slate-900")}
// Después:
className="font-display font-bold text-sm uppercase tracking-widest text-slate-500 mb-5"
```

e) Footer links (ambas columnas y el mapa de links):
```js
// Antes:
className={cn("text-sm font-medium transition-colors hover:text-indigo-600", dark ? "text-slate-400" : "text-slate-600")}
// Después:
className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
```

f) Bottom bar border y copyright:
```js
// Antes:
className={cn("border-t mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4", dark ? "border-slate-800" : "border-slate-200")}
// Después:
className="border-t border-slate-900 mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4"
```

```js
// Antes:
className={cn("text-sm", dark ? "text-slate-500" : "text-slate-400")}
// Después:
className="text-xs text-slate-600"
```

g) Bottom bar links:
```js
// Antes:
className={cn("text-xs transition-colors", dark ? "text-slate-500 hover:text-slate-300" : "text-slate-400 hover:text-slate-600")}
// Después:
className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
```

- [ ] **Step 3: Añadir trust badges al bottom bar**

Localizar el `<div>` que contiene los links legales en el bottom bar:
```js
<div className="flex items-center gap-4">
  {LEGAL_LINKS.map(...)}
</div>
```

Añadir antes de ese div:
```js
<div className="flex items-center gap-2">
  <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">🔒 SSL</span>
  <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">🇪🇺 RGPD</span>
  <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">99.9% SLA</span>
</div>
```

- [ ] **Step 4: Verificar en navegador**

Abrir http://localhost:3000 y hacer scroll hasta el footer. Verificar fondo oscuro, textos legibles, badges y que los links de RRSS funcionan.

- [ ] **Step 5: Commit**

```bash
git add landing/src/components/Footer.js
git commit -m "feat(landing): update Footer - dark style slate-950, Manrope font, trust badges"
```

---

## Task 15: Home.js — refactor a orquestador puro

**Files:**
- Modify: `landing/src/pages/Home.js`

- [ ] **Step 1: Reemplazar Home.js completo**

```js
// landing/src/pages/Home.js
import { useSEO } from '../hooks/useSEO';
import HeroSection        from '../sections/HeroSection';
import LogosSection       from '../sections/LogosSection';
import FeaturesSection    from '../sections/FeaturesSection';
import HowItWorksSection  from '../sections/HowItWorksSection';
import StatsSection       from '../sections/StatsSection';
import PricingSection     from '../sections/PricingSection';
import TestimonialsSection from '../sections/TestimonialsSection';
import FaqSection         from '../sections/FaqSection';
import CtaSection         from '../sections/CtaSection';

export default function Home() {
  useSEO({
    description:
      'Plataforma SaaS para sincronización automática de inventarios B2B. Conecta proveedores, gestiona catálogos y actualiza tus tiendas online en tiempo real. 14 días gratis.',
    canonical: '/',
    structuredData: {
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      name: 'SyncStock',
      description:
        'Plataforma SaaS para sincronización automática de inventarios B2B. Conecta proveedores, gestiona catálogos y actualiza tiendas online en tiempo real.',
      url: 'https://sync-stock.com',
      applicationCategory: 'BusinessApplication',
      operatingSystem: 'Web',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'EUR', description: 'Plan Free incluido' },
      aggregateRating: { '@type': 'AggregateRating', ratingValue: '4.9', ratingCount: '500' },
    },
  });

  return (
    <main>
      <HeroSection />
      <LogosSection />
      <FeaturesSection />
      <HowItWorksSection />
      <StatsSection />
      <PricingSection />
      <TestimonialsSection />
      <FaqSection />
      <CtaSection />
    </main>
  );
}
```

- [ ] **Step 2: Verificar en navegador**

```bash
cd landing && yarn start
```

Abrir http://localhost:3000. Hacer scroll completo de la página. Verificar que las 9 secciones aparecen en orden: Hero → Logos → Features → HowItWorks → Stats → Pricing → Testimonials → FAQ → CTA.

Verificar en consola que no hay errores (F12 → Console).

- [ ] **Step 3: Build de producción sin errores**

```bash
cd landing && yarn build 2>&1 | tail -20
```

Esperado: `The build folder is ready to be deployed.` sin errores.

- [ ] **Step 4: Commit**

```bash
git add landing/src/pages/Home.js
git commit -m "feat(landing): refactor Home.js to pure orchestrator - 9 independent sections"
```

---

## Task 16: AdminLanding — nuevos campos Hero + tab Cómo funciona

**Files:**
- Modify: `frontend/src/pages/AdminLanding.jsx`

- [ ] **Step 1: Añadir campos al estado `content.hero`**

Localizar:
```js
const [content, setContent] = useState({
  hero: {
    title: "",
    subtitle: "",
    cta_primary: "",
    cta_secondary: ""
  },
```

Reemplazar con:
```js
const [content, setContent] = useState({
  hero: {
    title: "",
    subtitle: "",
    cta_primary: "",
    cta_secondary: "",
    badge: "",
    social_proof_text: "",
  },
```

- [ ] **Step 2: Añadir `how_it_works` al estado inicial**

Localizar el final del objeto inicial de `content` (antes del `}`  del `useState`):
```js
    footer: { company_description: "", links: [] }
  });
```

Reemplazar con:
```js
    footer: { company_description: "", links: [] },
    how_it_works: [],
  });
```

- [ ] **Step 3: Añadir helpers para how_it_works**

Añadir después de `removeBenefitItem` (línea ~219):
```js
  const updateHowItWorksStep = (index, field, value) => {
    const newSteps = [...(content.how_it_works || [])];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setContent(prev => ({ ...prev, how_it_works: newSteps }));
  };

  const addHowItWorksStep = () => {
    setContent(prev => ({
      ...prev,
      how_it_works: [
        ...(prev.how_it_works || []),
        { title: "", description: "" }
      ]
    }));
  };

  const removeHowItWorksStep = (index) => {
    setContent(prev => ({
      ...prev,
      how_it_works: (prev.how_it_works || []).filter((_, i) => i !== index)
    }));
  };
```

- [ ] **Step 4: Añadir campos badge y social_proof_text al Tab Hero**

Localizar dentro de `<TabsContent value="hero">`, el bloque de los dos inputs de CTAs:
```jsx
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Botón Principal</Label>
```

Añadir **justo antes** de ese bloque:
```jsx
              <div className="space-y-2">
                <Label>Texto del badge</Label>
                <Input
                  value={content.hero?.badge || ""}
                  onChange={(e) => updateHero("badge", e.target.value)}
                  placeholder="Sincronización en tiempo real"
                />
                <p className="text-xs text-slate-400">Aparece encima del título principal como pill destacado</p>
              </div>
              <div className="space-y-2">
                <Label>Texto de social proof</Label>
                <Input
                  value={content.hero?.social_proof_text || ""}
                  onChange={(e) => updateHero("social_proof_text", e.target.value)}
                  placeholder="Usado por 500+ empresas en España y LATAM"
                />
                <p className="text-xs text-slate-400">Aparece debajo de los botones junto a los avatares</p>
              </div>
```

- [ ] **Step 5: Añadir tab "Cómo funciona" a TabsList**

Localizar:
```jsx
        <TabsList className="grid w-full grid-cols-6 lg:w-[720px]">
```

Reemplazar con:
```jsx
        <TabsList className="grid w-full grid-cols-7 lg:w-[840px]">
```

Añadir el nuevo trigger después del trigger de `features`:
```jsx
          <TabsTrigger value="how_it_works">
            <Layout className="w-4 h-4 mr-2" />
            Cómo funciona
          </TabsTrigger>
```

- [ ] **Step 6: Añadir TabsContent para how_it_works**

Añadir después del cierre de `</TabsContent>` de `features` (antes del de `testimonials`):
```jsx
        {/* How It Works Section */}
        <TabsContent value="how_it_works">
          <Card>
            <CardHeader>
              <CardTitle>Cómo funciona</CardTitle>
              <CardDescription>Los pasos que explican cómo usar SyncStock (máximo 3)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.how_it_works || []).map((step, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700 flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                      Paso {idx + 1}
                    </span>
                    <Button variant="ghost" size="sm" onClick={() => removeHowItWorksStep(idx)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Título del paso</Label>
                    <Input
                      value={step.title}
                      onChange={(e) => updateHowItWorksStep(idx, "title", e.target.value)}
                      placeholder="Conecta un proveedor"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Descripción</Label>
                    <Textarea
                      value={step.description}
                      onChange={(e) => updateHowItWorksStep(idx, "description", e.target.value)}
                      placeholder="Añade la URL, FTP o sube el archivo CSV..."
                      rows={2}
                    />
                  </div>
                </div>
              ))}
              {(content.how_it_works || []).length < 3 && (
                <Button variant="outline" onClick={addHowItWorksStep}>
                  <Plus className="w-4 h-4 mr-2" />
                  Añadir Paso
                </Button>
              )}
              {(content.how_it_works || []).length >= 3 && (
                <p className="text-xs text-slate-400">Máximo 3 pasos recomendado para buena UX</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
```

- [ ] **Step 7: Verificar en el frontend (panel admin)**

```bash
cd frontend && yarn start
```

Navegar a SuperAdmin → Landing. Verificar:
- Tab "Cómo funciona" aparece en TabsList
- Los 2 nuevos campos de Hero (badge, social_proof_text) se muestran en el Tab Hero
- Se pueden añadir hasta 3 pasos con título y descripción
- El botón "Guardar Cambios" envía todos los campos correctamente (verificar en Network → `PUT /admin/landing/content` → request body incluye `hero.badge`, `hero.social_proof_text`, `how_it_works`)

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/AdminLanding.jsx
git commit -m "feat(admin): add hero badge/social-proof fields and How It Works tab to AdminLanding editor"
```

---

## Self-Review

### Spec coverage

| Requisito | Task |
|---|---|
| Clean Enterprise visual | Task 4 (Hero), 6 (Features), 8 (Stats), 9 (Pricing), 13 (Navbar), 14 (Footer) |
| Animaciones flotantes + contadores | Task 2 (useCountUp), 3 (useReveal), 4 (badges float), 8 (StatsSection counters) |
| Hero split texto + dashboard | Task 4 |
| Logos marquee infinito | Task 5 |
| Bento grid features | Task 6 |
| HowItWorks 3 pasos | Task 7 |
| StatsSection contadores animados | Task 8 |
| Pricing planes + toggle | Task 9 |
| Testimonials grid | Task 10 |
| FAQ acordeón Radix | Task 11 |
| CTA final | Task 12 |
| Navbar glassmorphism permanente | Task 13 |
| Footer oscuro + badges | Task 14 |
| Home.js orquestador | Task 15 |
| AdminLanding: badge + social_proof + how_it_works | Task 16 |
| Manrope font | Task 1 |
| CSS keyframes nuevos | Task 1 |

**Sin gaps detectados.**

### Placeholders scan
- Sin TBD, sin TODO, sin "similar a Task N"
- Todos los steps de código tienen el código completo
- Todos los commands de verificación son específicos

### Type consistency
- `useCountUp(rawTarget, duration, trigger)` — consistente en Task 2 y uso en Task 8
- `useReveal(threshold)` — consistente en Task 3 y uso en Tasks 6, 7, 10
- `content.how_it_works[]` — consistente entre Task 7 (read) y Task 16 (write)
- `content.hero.badge` — consistente entre Task 4 (read con fallback) y Task 16 (write)
- `content.benefits.items` — consistente entre Task 8 (read) y AdminLanding existente (write)
