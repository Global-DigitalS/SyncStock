import { useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import {
  ArrowRight, Zap, Globe, BarChart3, Lock, Webhook,
  Check, Star, TrendingUp, Code2, Database, Shield
} from 'lucide-react';
import { useSEO } from '../hooks/useSEO';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.8, ease: 'easeOut' },
  },
};

const featureCard = {
  hidden: { opacity: 0, y: 30 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      delay: i * 0.1,
      ease: 'easeOut',
    },
  }),
};

function ScrollReveal({ children, className = '' }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function FeatureCard({ icon: Icon, title, description, index }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      custom={index}
      variants={featureCard}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-50px' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative p-8 rounded-2xl border border-slate-200 bg-white/50 backdrop-blur-sm hover:border-blue-400 transition-all duration-300 shadow-sm hover:shadow-lg"
    >
      <motion.div
        animate={isHovered ? { scale: 1.1, rotateZ: 5 } : { scale: 1, rotateZ: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 10 }}
        className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center mb-6 group-hover:from-blue-100 group-hover:to-cyan-100 transition-all"
      >
        <Icon className="w-6 h-6 text-blue-600" />
      </motion.div>

      <h3 className="text-lg font-semibold text-slate-900 mb-3">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed">{description}</p>

      {isHovered && (
        <motion.div
          layoutId={`underline-${index}`}
          className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: '100%' }}
          transition={{ duration: 0.3 }}
        />
      )}
    </motion.div>
  );
}

function TestimonialCard({ name, company, quote, index }) {
  return (
    <motion.div
      variants={featureCard}
      custom={index}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="p-6 rounded-xl border border-slate-200 bg-white/30 backdrop-blur-sm hover:bg-white/50 transition-all"
    >
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
        ))}
      </div>
      <p className="text-slate-700 text-sm leading-relaxed mb-4">"{quote}"</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-cyan-400 flex items-center justify-center text-white font-bold text-xs">
          {name.charAt(0)}
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{name}</p>
          <p className="text-xs text-slate-600">{company}</p>
        </div>
      </div>
    </motion.div>
  );
}

export default function Home() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useSEO({
    description:
      'SyncStock: Plataforma SaaS para gestión y sincronización inteligente de catálogos de proveedores. Conecta múltiples proveedores, publica en tiendas online y automatiza tu operación de e-commerce.',
    canonical: '/',
    structuredData: {
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      name: 'SyncStock',
      description: 'Plataforma SaaS para gestión y sincronización inteligente de catálogos de proveedores',
      url: 'https://sync-stock.com',
      applicationCategory: 'BusinessApplication',
      operatingSystem: 'Web',
      offers: { '@type': 'Offer', price: '49', priceCurrency: 'EUR' },
      aggregateRating: { '@type': 'AggregateRating', ratingValue: '4.8', ratingCount: '150' },
    },
  });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const features = [
    {
      icon: Webhook,
      title: 'Sincronización Multi-Proveedor',
      description: 'Conecta proveedores ilimitados via FTP, SFTP, HTTP o URLs. Sincronización automática con intervalos configurables.'
    },
    {
      icon: Globe,
      title: 'Multi-Tienda',
      description: 'Publica catálogos en WooCommerce, Shopify, PrestaShop y más. Control centralizado de todas tus tiendas.'
    },
    {
      icon: Database,
      title: 'Integración CRM/ERP',
      description: 'Conecta Dolibarr, Odoo y otros sistemas. Sincronización automática de productos, órdenes y clientes.'
    },
    {
      icon: BarChart3,
      title: 'Catálogos Personalizados',
      description: 'Crea múltiples catálogos con reglas de margen, filtrado y precios personalizados por canal.'
    },
    {
      icon: TrendingUp,
      title: 'Analítica en Tiempo Real',
      description: 'Dashboard completo con métricas de productos, stock, ingresos y alertas configurables.'
    },
    {
      icon: Shield,
      title: 'Seguridad Empresarial',
      description: 'JWT, RBAC, rate limiting, encriptación de credenciales. Cumple normativas de seguridad B2B.'
    },
  ];

  const testimonials = [
    {
      name: 'Carlos Martín',
      company: 'TechStore Spain',
      quote: 'SyncStock redujo nuestro tiempo de gestión de catálogos en un 80%. Increíble herramienta para empresas con múltiples proveedores.'
    },
    {
      name: 'María López',
      company: 'eCommerce Plus',
      quote: 'La sincronización con Odoo y WooCommerce es transparente. Nuestro equipo ya no pierde horas en tareas manuales.'
    },
    {
      name: 'Juan García',
      company: 'Distribuidora Online',
      quote: 'El mejor ROI que hemos visto. Gestionar 10 proveedores en una sola plataforma cambió nuestra operación.'
    },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none">
        <motion.div
          animate={{
            background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, rgba(59, 130, 246, 0.05) 0%, transparent 50%)`
          }}
          className="w-full h-full"
          transition={{ type: 'tween', ease: 'easeOut' }}
        />
      </div>

      {/* Hero Section */}
      <section className="relative pt-24 pb-32 px-6 max-w-7xl mx-auto">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
        >
          <motion.div variants={itemVariants} className="space-y-8">
            <div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="inline-block mb-4 px-4 py-2 rounded-full bg-blue-50 border border-blue-200"
              >
                <span className="text-sm font-medium text-blue-700">✨ La solución #1 para catálogos multi-proveedor</span>
              </motion.div>
              <h1 className="text-5xl lg:text-6xl font-bold text-slate-900 leading-tight">
                Gestiona tus catálogos de proveedores sin esfuerzo
              </h1>
            </div>

            <p className="text-xl text-slate-600 leading-relaxed max-w-lg">
              Sincroniza productos de múltiples proveedores, publica en varias tiendas y automatiza tu operación de e-commerce. Ahorra 80% del tiempo en gestión de catálogos.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group px-8 py-4 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
              >
                Prueba Gratis
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 rounded-lg border border-slate-300 text-slate-900 font-semibold hover:bg-slate-50 transition"
              >
                Ver Demo
              </motion.button>
            </div>

            <motion.div variants={itemVariants} className="flex items-center gap-8 pt-4">
              <div>
                <p className="text-sm font-semibold text-slate-900">Empresas confiando en SyncStock</p>
                <div className="flex gap-2 mt-2">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-cyan-400 flex items-center justify-center text-white text-xs font-bold"
                    >
                      +
                    </div>
                  ))}
                </div>
              </div>
              <div className="h-12 w-px bg-slate-200" />
              <div>
                <p className="text-2xl font-bold text-slate-900">150+</p>
                <p className="text-sm text-slate-600">Empresas activas</p>
              </div>
            </motion.div>
          </motion.div>

          <motion.div variants={itemVariants} className="relative h-96 lg:h-full min-h-96">
            <motion.div
              animate={{
                y: [-20, 20, -20],
                rotateZ: [0, 2, 0]
              }}
              transition={{
                duration: 6,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
              className="absolute inset-0 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl opacity-20 blur-2xl"
            />
            <motion.div
              animate={{
                y: [20, -20, 20],
                rotateZ: [0, -2, 0]
              }}
              transition={{
                duration: 7,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
              className="absolute top-12 right-12 w-72 h-72 bg-gradient-to-br from-blue-200/40 to-transparent rounded-3xl"
            />

            <div className="relative z-10 h-full flex items-end justify-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5, type: 'spring' }}
                className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white/80 backdrop-blur-sm p-6 shadow-xl"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-900">Dashboard SyncStock</h3>
                    <Zap className="w-5 h-5 text-blue-600" />
                  </div>
                  {[...Array(3)].map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + i * 0.1 }}
                      className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200"
                    >
                      <Check className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-slate-700">
                        {['Sincronización activa', 'Productos: 12,450', 'Últimas 2h'][i]}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">
              Funciones que transforman tu operación
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Todo lo que necesitas para gestionar catálogos complejos en una sola plataforma
            </p>
          </div>
        </ScrollReveal>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          {features.map((feature, index) => (
            <FeatureCard key={index} {...feature} index={index} />
          ))}
        </motion.div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-24 px-6 max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">
              Lo que dicen nuestros clientes
            </h2>
          </div>
        </ScrollReveal>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} {...testimonial} index={index} />
          ))}
        </motion.div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6 max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">
              Planes flexibles para cualquier empresa
            </h2>
            <p className="text-lg text-slate-600">
              Elige el plan que mejor se adapte a tus necesidades
            </p>
          </div>
        </ScrollReveal>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {[
            { name: 'Starter', price: '49', features: ['Hasta 3 proveedores', '1 tienda', 'Soporte email'] },
            { name: 'Professional', price: '149', popular: true, features: ['Proveedores ilimitados', 'Tiendas ilimitadas', 'CRM integrado', 'Soporte 24/7'] },
            { name: 'Enterprise', price: 'Personalizado', features: ['Solución personalizada', 'API custom', 'SLA garantizado', 'Manager dedicado'] },
          ].map((plan, index) => (
            <motion.div
              key={index}
              custom={index}
              variants={featureCard}
              className={`relative rounded-2xl p-8 ${
                plan.popular
                  ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white border-0 scale-105'
                  : 'bg-white border border-slate-200 text-slate-900'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-yellow-400 text-xs font-semibold text-slate-900">
                  Más popular
                </div>
              )}
              <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">{plan.price}</span>
                {plan.price !== 'Personalizado' && <span className={`text-sm ml-2 ${plan.popular ? 'text-blue-100' : 'text-slate-600'}`}>/mes</span>}
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <Check className="w-5 h-5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`w-full py-3 rounded-lg font-semibold transition ${
                  plan.popular
                    ? 'bg-white text-blue-600 hover:bg-blue-50'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                Comenzar
              </motion.button>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 max-w-7xl mx-auto">
        <ScrollReveal>
          <motion.div className="relative rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-600 p-16 text-center text-white overflow-hidden">
            <motion.div
              animate={{
                opacity: [0.1, 0.3, 0.1],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-10"
            />

            <motion.div className="relative z-10 space-y-6">
              <h2 className="text-4xl lg:text-5xl font-bold">
                ¿Listo para automatizar tus catálogos?
              </h2>
              <p className="text-xl text-blue-100 max-w-2xl mx-auto">
                Únete a 150+ empresas que ya están transformando su operación con SyncStock
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="mx-auto block px-8 py-4 rounded-lg bg-white text-blue-600 font-semibold hover:bg-blue-50 transition"
              >
                Prueba gratis por 14 días
              </motion.button>
            </motion.div>
          </motion.div>
        </ScrollReveal>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50/50 backdrop-blur-sm mt-24">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            <div>
              <h3 className="font-bold text-slate-900 mb-4">SyncStock</h3>
              <p className="text-sm text-slate-600">Gestión inteligente de catálogos para e-commerce</p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 mb-4">Producto</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><a href="#" className="hover:text-slate-900 transition">Características</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Precios</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Documentación</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 mb-4">Empresa</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><a href="#" className="hover:text-slate-900 transition">Sobre nosotros</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Blog</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Contacto</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li><a href="#" className="hover:text-slate-900 transition">Privacidad</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Términos</a></li>
                <li><a href="#" className="hover:text-slate-900 transition">Cookies</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-8 flex flex-col md:flex-row items-center justify-between">
            <p className="text-sm text-slate-600">
              © 2026 Global-DigitalS. Todos los derechos reservados.
            </p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <a href="#" className="text-slate-600 hover:text-slate-900 transition">Twitter</a>
              <a href="#" className="text-slate-600 hover:text-slate-900 transition">LinkedIn</a>
              <a href="#" className="text-slate-600 hover:text-slate-900 transition">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
