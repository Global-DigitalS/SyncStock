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
