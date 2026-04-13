// landing/src/sections/FaqSection.js
import * as Accordion from '@radix-ui/react-accordion';
import { ChevronDown } from 'lucide-react';
import { useApp } from '../context/AppContext';

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
              key={item.question || i}
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
