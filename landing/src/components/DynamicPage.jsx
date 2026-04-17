import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Loader2 } from 'lucide-react';
import Navbar from './Navbar';
import Footer from './Footer';

/**
 * Componente DynamicPage
 * Renderiza páginas editables fetched desde la API
 *
 * @param {Object} props - Props del componente
 * @param {Object} props.page - Objeto de página con estructura { hero_title, hero_subtitle, hero_image, content, ... }
 * @param {Object} props.branding - Configuración de branding { primary_color, secondary_color, accent_color, ... }
 * @param {boolean} props.loading - Indica si hay carga en progreso
 * @param {Object} props.error - Objeto de error { currentPageError }
 * @returns {React.ReactElement}
 */
function DynamicPage({ page, branding, loading, error }) {
  // Estados de carga y error
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
        <Navbar branding={branding} />
        <div className="flex-1 flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="flex flex-col items-center gap-4"
          >
            <Loader2 size={48} className="text-indigo-600" />
            <p className="text-slate-600 font-medium">Cargando página...</p>
          </motion.div>
        </div>
        <Footer branding={branding} />
      </div>
    );
  }

  if (error?.currentPageError || !page) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
        <Navbar branding={branding} />
        <div className="flex-1 flex items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center"
          >
            <AlertCircle
              size={48}
              className="text-red-500 mx-auto mb-4"
            />
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Página no encontrada
            </h2>
            <p className="text-slate-600">
              Lo sentimos, la página que buscas no está disponible.
            </p>
          </motion.div>
        </div>
        <Footer branding={branding} />
      </div>
    );
  }

  // Renderizar página
  return (
    <div className="min-h-screen bg-white">
      <Navbar branding={branding} />

      <main>
        {/* Hero Section */}
        {page.hero_title && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            style={{
              background: `linear-gradient(135deg, ${branding?.primary_color || '#4f46e5'} 0%, ${branding?.secondary_color || '#0f172a'} 100%)`,
            }}
            className="relative py-20 px-4 sm:py-24 sm:px-6 lg:px-8 text-white overflow-hidden"
          >
            {/* Decorative elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl" />
              <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-white/5 rounded-full blur-3xl" />
            </div>

            <div className="relative max-w-7xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.8 }}
              >
                {page.hero_title && (
                  <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 leading-tight">
                    {page.hero_title}
                  </h1>
                )}

                {page.hero_subtitle && (
                  <p className="text-lg sm:text-xl text-white/90 max-w-2xl">
                    {page.hero_subtitle}
                  </p>
                )}

                {page.hero_image && (
                  <motion.img
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4, duration: 0.8 }}
                    src={page.hero_image}
                    alt={page.hero_title || 'Hero image'}
                    className="mt-8 rounded-lg shadow-2xl max-w-full h-auto"
                  />
                )}
              </motion.div>
            </div>
          </motion.section>
        )}

        {/* Dynamic Content Blocks */}
        {page.content && Array.isArray(page.content) && (
          <section className="py-12 sm:py-16 lg:py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto space-y-12">
              {page.content.map((block, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-100px' }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  {renderContentBlock(block, branding, index)}
                </motion.div>
              ))}
            </div>
          </section>
        )}

        {/* Fallback content if page.content is string */}
        {page.content && typeof page.content === 'string' && (
          <section className="py-12 sm:py-16 lg:py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto prose prose-lg max-w-none">
              <p className="text-slate-700 leading-relaxed">
                {page.content}
              </p>
            </div>
          </section>
        )}
      </main>

      <Footer branding={branding} />
    </div>
  );
}

/**
 * Renderiza un bloque de contenido dinámico según su tipo
 * Soporta: paragraph, heading, blockquote, image, cta, list, etc.
 */
function renderContentBlock(block, branding, index) {
  if (!block || typeof block !== 'object') {
    return null;
  }

  const { type, content, level, image, alignment = 'left', backgroundColor } = block;

  switch (type) {
    case 'heading':
      const headingTag = `h${Math.min(Math.max(level || 2, 1), 6)}`;
      const HeadingComponent = headingTag;
      const headingSizes = {
        1: 'text-4xl',
        2: 'text-3xl',
        3: 'text-2xl',
        4: 'text-xl',
        5: 'text-lg',
        6: 'text-base',
      };
      return (
        <HeadingComponent
          className={`${headingSizes[level || 2]} font-bold text-slate-900 mb-4`}
        >
          {content}
        </HeadingComponent>
      );

    case 'paragraph':
      return (
        <p className="text-slate-700 text-lg leading-relaxed mb-4">
          {content}
        </p>
      );

    case 'blockquote':
      return (
        <blockquote
          style={{
            borderLeftColor: branding?.accent_color || '#10b981',
          }}
          className="border-l-4 pl-4 py-2 my-6 italic text-slate-600 bg-slate-50 p-4 rounded"
        >
          {content}
        </blockquote>
      );

    case 'image':
      return (
        <motion.figure
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="my-8"
        >
          <img
            src={image || content}
            alt={block.alt || 'Content image'}
            className="rounded-lg shadow-lg w-full h-auto"
          />
          {block.caption && (
            <figcaption className="text-center text-slate-600 text-sm mt-2">
              {block.caption}
            </figcaption>
          )}
        </motion.figure>
      );

    case 'cta':
      return (
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="my-8 text-center"
        >
          <a
            href={block.url || '#'}
            style={{
              backgroundColor: branding?.primary_color || '#4f46e5',
            }}
            className="inline-block px-8 py-3 text-white font-semibold rounded-lg hover:shadow-lg transition-shadow"
          >
            {content}
          </a>
        </motion.div>
      );

    case 'list':
      return (
        <ul className="space-y-2 my-4 text-slate-700">
          {Array.isArray(block.items) &&
            block.items.map((item, idx) => (
              <li
                key={idx}
                className="flex items-start gap-3"
              >
                <span
                  style={{ color: branding?.accent_color || '#10b981' }}
                  className="font-bold text-lg mt-0.5"
                >
                  •
                </span>
                <span>{item}</span>
              </li>
            ))}
        </ul>
      );

    case 'divider':
      return (
        <hr
          style={{
            borderColor: branding?.primary_color || '#4f46e5',
          }}
          className="my-8 border-1 opacity-30"
        />
      );

    case 'html':
      // Renderizar HTML puro (solo si es confiable)
      return (
        <div
          className="my-8 prose prose-lg max-w-none"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      );

    default:
      // Fallback: renderizar como párrafo
      return (
        <p className="text-slate-700 text-lg leading-relaxed mb-4">
          {content}
        </p>
      );
  }
}

export default DynamicPage;
