# Rediseño Landing SyncStock — Spec de Diseño

**Fecha:** 2026-04-13  
**Estado:** Aprobado  
**Scope:** Landing completa (`landing/`) — Home, Navbar, Footer, nuevas secciones

---

## Decisiones de Diseño

| Dimensión | Decisión |
|---|---|
| Estilo visual | Clean Enterprise — fondo blanco, acento indigo-600, tipografía Manrope + Inter |
| Animaciones | Flotante + Contadores — badges flotantes, IntersectionObserver counters, barras de progreso animadas, marquee de logos |
| Hero layout | Split — texto izquierda, dashboard mockup derecha con badges flotantes |

---

## Arquitectura de Archivos

### Archivos nuevos
```
landing/src/sections/
  HeroSection.js
  LogosSection.js
  FeaturesSection.js
  HowItWorksSection.js
  StatsSection.js
  PricingSection.js
  TestimonialsSection.js
  FaqSection.js
  CtaSection.js
```

### Archivos actualizados
```
landing/src/pages/Home.js          — orquestador puro, solo importa secciones
landing/src/components/Navbar.js   — nuevo diseño glassmorphism sticky
landing/src/components/Footer.js   — nuevo diseño multi-columna
landing/src/index.css              — keyframes nuevos (float, countUp, marquee, etc.)
```

---

## Navbar

- **Fondo:** `rgba(255,255,255,0.92)` con `backdrop-filter: blur(20px)` — glassmorphism
- **Sticky:** sí, `position: sticky; top: 0; z-index: 50`
- **Border:** `border-bottom: 1px solid #f1f5f9` — aparece al hacer scroll (IntersectionObserver o scroll listener)
- **Logo:** icono indigo 28×28 con gradiente + texto Manrope 800
- **Links:** Funciones · Integraciones · Precios · Blog (datos de `content` del AppContext)
- **Acciones:** "Iniciar sesión" (ghost) + "Empezar gratis →" (botón indigo-600)
- **Responsive:** menú hamburguesa en mobile (<768px)

---

## HeroSection

### Layout
- Grid 2 columnas en desktop (`lg:grid-cols-2`), 1 columna en mobile
- Padding: `pt-24 pb-20 lg:pt-32 lg:pb-28`
- Fondo: `bg-gradient-to-b from-white to-slate-50`

### Columna izquierda (texto)
Elementos con animación `fadeSlide` staggered (delay 0ms, 100ms, 200ms, 300ms, 400ms):
1. **Badge** — pill indigo-50 con punto pulsante + texto dinámico del AppContext (`hero.badge`)
2. **H1** — Manrope 800, ~52px desktop, letra-spacing -2px. Texto de `hero.title`. Word accentuado en indigo-600.
3. **Subtítulo** — Inter 400, 16px, slate-600, `hero.subtitle`
4. **Botones** — "Prueba gratis 14 días →" (indigo) + "▶ Ver demo en vivo" (ghost blanco con borde)
5. **Social proof** — 4 avatares apilados + "Usado por 500+ empresas"

### Columna derecha (dashboard)
- **Badges flotantes:** 2 pills con datos reales (productos sync, uptime), animación `floatY` 3s infinite, delay escalonado
- **Dashboard mockup:** tarjeta blanca con sombra, barra de título estilo macOS, stats grid 4×1, tabla de proveedores, mini gráfico de barras
- Los datos del mockup son estáticos/decorativos (no conectan al backend)

---

## LogosSection

- Fondo blanco, `border-top` y `border-bottom` en slate-100
- Label: "Integra con las plataformas que ya usas" — slate-400, uppercase, tracking-widest
- **Marquee infinito** — CSS animation `marquee` 20s linear infinite
- Logos: WooCommerce, Shopify, PrestaShop, Odoo, Dolibarr, WordPress — íconos con color de marca + nombre
- Track duplicado para loop sin salto

---

## FeaturesSection

- Fondo: `bg-slate-50`
- Header izquierdo: label "Funcionalidades" + H2 + subtítulo
- **Bento grid:** `grid-cols-3`, gap-4
  - Card 1 (span 2): "Sincronización multi-proveedor" — con mini barras de progreso animadas mostrando proveedores y productos
  - Cards 2-6: 1×1, iconos Lucide + título + descripción
  - Features desde `content.features` del AppContext

---

## HowItWorksSection

- Fondo blanco
- Header centrado: label + H2 + subtítulo
- **3 pasos** en grid horizontal con línea conectora SVG/CSS entre ellos
  - Cada paso: número en círculo (el paso 1 en indigo filled, resto en borde indigo), título, descripción
  - Los pasos vienen de `content.how_it_works` del AppContext
- Animación scroll-reveal: `scale(0.94) → scale(1)` con IntersectionObserver

---

## StatsSection

- Fondo: `bg-indigo-600` (gradiente suave a indigo-700)
- Grid 4 columnas, max-width 800px centrado
- **Contadores animados** — IntersectionObserver dispara contador numérico al entrar en viewport
  - 500+ Empresas activas
  - 2M+ Productos gestionados  
  - 99.9% Uptime garantizado
  - 4.9★ Valoración media
- Implementación: hook `useCountUp(target, duration)` con `requestAnimationFrame`

---

## PricingSection

- Fondo: `bg-slate-50`
- Toggle mensual/anual con `useState` — descuento 20% en anual
- Grid 3 columnas: Free · Pro (featured, borde indigo, badge "Más popular") · Enterprise
- Datos de planes desde `plans` del AppContext (filtrados por `is_active`)
- Card "Pro" con `box-shadow` y borde 2px indigo

---

## TestimonialsSection

- Fondo blanco
- Header centrado
- Grid 3 columnas de cards con: estrellas, cita en cursiva, avatar + nombre + rol
- Datos de `content.testimonials` del AppContext

---

## FaqSection

- Fondo: `bg-slate-50`
- Acordeón con `@radix-ui/react-accordion` (ya instalado)
- Datos de `content.faq` del AppContext

---

## CtaSection

- Fondo: `bg-slate-900`
- H2 grande en blanco + subtítulo gris + 2 botones
- Datos de `content.cta_final` del AppContext

---

## Footer

- Fondo: `bg-slate-950`
- Grid 4 columnas: marca (logo + descripción) + 3 columnas de links
- Bottom bar: copyright + badges (🔒 SSL, 🇪🇺 RGPD, 99.9% SLA)
- Links de `content` del AppContext o hardcoded si no existen

---

## Animaciones — Keyframes CSS en `index.css`

```css
@keyframes fadeSlide        { from { opacity:0; transform:translateY(16px) } to { opacity:1; transform:translateY(0) } }
@keyframes floatY           { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-10px) } }
@keyframes marquee          { from { transform:translateX(0) } to { transform:translateX(-50%) } }
@keyframes revealScale      { from { opacity:0; transform:scale(0.94) translateY(12px) } to { opacity:1; transform:scale(1) translateY(0) } }
@keyframes pulse            { 0%,100% { opacity:1; transform:scale(1) } 50% { opacity:0.4; transform:scale(0.8) } }
@keyframes countUp          — implementado en JS con requestAnimationFrame
```

---

## Tipografía

- **Headings:** Manrope 800 (importar de Google Fonts en `public/index.html`)
- **Body:** Inter (ya cargado)
- No añadir nuevas dependencias npm — solo Google Fonts CDN

---

## Paleta de colores (Tailwind existente)

| Uso | Clase |
|---|---|
| Acento principal | `indigo-600` / `indigo-700` |
| Texto principal | `slate-900` |
| Texto secundario | `slate-600` / `slate-400` |
| Fondo secciones alt | `slate-50` |
| Fondo dark | `slate-900` / `slate-950` |
| Éxito | `emerald-500` |
| Advertencia | `amber-500` |

---

## Responsive

- **Mobile-first** — todas las secciones colapsan a 1 columna
- Navbar: hamburguesa en `<md`
- Bento: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- Hero: `grid-cols-1 lg:grid-cols-2` (columna derecha oculta en mobile)
- Stats: `grid-cols-2 lg:grid-cols-4`

---

## Dependencias

No se añaden nuevas dependencias. Se usa:
- `tailwindcss-animate` (ya instalado)
- `@radix-ui/react-accordion` (ya instalado)
- `lucide-react` (ya instalado)
- Google Fonts CDN (Manrope) vía `public/index.html`

---

## Edición de textos desde SuperAdmin — AdminLanding

**La infraestructura ya existe:** el backend tiene `GET/PUT /admin/landing/content`, el AppContext de la landing consume `GET /landing/content` y expone `content` vía `useApp()`. Todas las secciones nuevas deben leer de `content`.

### Mapa: campo editable → sección de la landing

| Campo en `content` | Sección landing | Ya editable en AdminLanding |
|---|---|---|
| `hero.title` | HeroSection — H1 | ✅ sí |
| `hero.subtitle` | HeroSection — subtítulo | ✅ sí |
| `hero.cta_primary` | HeroSection — botón principal | ✅ sí |
| `hero.cta_secondary` | HeroSection — botón secundario | ✅ sí |
| `hero.badge` | HeroSection — pill badge | ❌ **añadir campo** |
| `hero.social_proof_text` | HeroSection — "Usado por X empresas" | ❌ **añadir campo** |
| `features[]` | FeaturesSection — bento grid | ✅ sí |
| `benefits.items[]` | StatsSection — contadores grandes | ✅ sí |
| `how_it_works[]` | HowItWorksSection — pasos 1/2/3 | ❌ **añadir tab** |
| `testimonials[]` | TestimonialsSection | ✅ sí |
| `faq[]` | FaqSection | ✅ sí |
| `cta_final.title` | CtaSection | ✅ sí |
| `cta_final.subtitle` | CtaSection | ✅ sí |
| `cta_final.button_text` | CtaSection | ✅ sí |
| `footer.company_description` | Footer | ✅ sí |

### Cambios requeridos en `AdminLanding.jsx`

1. **Tab "Hero"** — añadir 2 campos:
   - `hero.badge` — Input "Texto del badge" (ej: "Sincronización en tiempo real")
   - `hero.social_proof_text` — Input "Texto social proof" (ej: "Usado por 500+ empresas en España")

2. **Nuevo tab "Cómo funciona"** (entre Features y Testimonios) — gestión de `content.how_it_works[]`:
   - Cada paso tiene: `step_number` (automático), `title` (Input), `description` (Textarea)
   - Botones de añadir / eliminar paso
   - Máximo 3 pasos recomendado (no forzado)

3. Los textos del **LogosSection** (nombres de integraciones) son estáticos — no se editan desde AdminLanding porque son las integraciones reales del producto.

4. Los textos del **Navbar** y **Footer** (links de navegación) son estáticos — provienen de las rutas de React Router, no del content editable.

---

## Qué NO cambia

- Resto de páginas: `About.js`, `Blog.js`, `Contact.js`, `Features.js`, `Pricing.js`, `Privacy.js`, `Terms.js`
- AppContext, hooks, lógica de negocio
- Estructura de rutas en `App.js`
- Backend — ningún cambio
