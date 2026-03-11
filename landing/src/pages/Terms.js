import { useApp } from "../context/AppContext";
import { cn, SectionLabel } from "../components/ui";

const SECTIONS = [
  {
    title: "1. Objeto y ámbito de aplicación",
    content: `Estos Términos y Condiciones de Uso (en adelante, "Términos") regulan el acceso y uso de la plataforma {app_name} (en adelante, "la Plataforma"), incluidos todos sus servicios, funcionalidades y contenidos.

Al registrarte y utilizar la Plataforma, aceptas expresamente estos Términos. Si no estás de acuerdo, debes abstenerte de usar la Plataforma.`
  },
  {
    title: "2. Descripción del servicio",
    content: `{app_name} es una plataforma SaaS (Software as a Service) B2B que permite:

• Importar y gestionar catálogos de productos de múltiples proveedores (FTP, SFTP, URL, CSV, Excel, XML).
• Sincronizar productos, precios y stock con tiendas online (WooCommerce, Shopify, PrestaShop).
• Integrar sistemas CRM y ERP (Dolibarr, Odoo).
• Crear catálogos personalizados con reglas de margen y precios diferenciados.
• Exportar datos en diferentes formatos.

Los servicios están destinados exclusivamente a empresas y profesionales (uso B2B). No están diseñados para uso por consumidores finales.`
  },
  {
    title: "3. Registro y cuenta de usuario",
    content: `Para acceder a la Plataforma debes registrarte con información veraz y actualizada. Eres responsable de:

• Mantener la confidencialidad de tus credenciales de acceso.
• Notificarnos inmediatamente si detectas un acceso no autorizado a tu cuenta.
• Todas las actividades realizadas con tu cuenta.

Nos reservamos el derecho de cancelar cuentas con información falsa o que incumplan estos Términos.`
  },
  {
    title: "4. Planes de suscripción y facturación",
    content: `{app_name} ofrece diferentes planes de suscripción con distintos límites y funcionalidades. Los precios son los publicados en la página de precios en el momento de la contratación.

**Facturación y pagos**:
• El pago se procesa mediante Stripe al inicio de cada período.
• Los planes anuales se facturan por adelantado por el período completo.
• Los precios incluyen IVA aplicable.

**Período de prueba**:
• Algunos planes incluyen un período de prueba gratuita indicado en la página de precios.
• No se requiere tarjeta de crédito durante el período de prueba (según el plan).

**Cancelación**:
• Puedes cancelar en cualquier momento desde la configuración de tu cuenta.
• La cancelación surte efecto al final del período de facturación en curso.
• No realizamos reembolsos prorrateados por cancelación anticipada, salvo en los casos previstos por la legislación aplicable.`
  },
  {
    title: "5. Límites del servicio",
    content: `Cada plan tiene límites específicos en cuanto a número de proveedores, catálogos, productos y tiendas. Estos límites están publicados en la página de precios.

Si superas los límites de tu plan:
• Recibirás notificaciones de aviso antes de alcanzar el límite.
• Podrás actualizar a un plan superior en cualquier momento.
• No se creará contenido nuevo hasta que actualices o elimines recursos existentes.

Nos reservamos el derecho de limitar temporalmente el acceso en casos de uso abusivo que afecten al servicio de otros usuarios.`
  },
  {
    title: "6. Uso aceptable",
    content: `Queda estrictamente prohibido:

• Usar la Plataforma para actividades ilegales o fraudulentas.
• Intentar acceder a datos de otros usuarios.
• Realizar ingeniería inversa, descompilar o desensamblar la Plataforma.
• Usar bots, scrapers u otras herramientas automatizadas para acceder a la Plataforma salvo mediante la API oficial.
• Sobrecargar intencionalmente los sistemas con peticiones masivas.
• Revender o sublicenciar el acceso a la Plataforma sin autorización expresa.
• Importar o procesar contenidos que infrinjan derechos de terceros.`
  },
  {
    title: "7. Propiedad intelectual",
    content: `**Plataforma**: Todos los derechos de propiedad intelectual sobre la Plataforma, incluyendo código, diseño, marcas y documentación, pertenecen a {app_name} o sus licenciantes.

**Tus datos**: Mantienes todos los derechos sobre los datos que importas en la Plataforma. Nos otorgas una licencia limitada, no exclusiva para procesar y almacenar tus datos exclusivamente para la prestación del servicio.

**Retroalimentación**: Si compartes sugerencias o comentarios sobre la Plataforma, nos otorgas el derecho de implementarlos sin obligación de compensación.`
  },
  {
    title: "8. Disponibilidad y mantenimiento",
    content: `Nos comprometemos a mantener la Plataforma disponible con un objetivo de disponibilidad del 99,9% mensual, excluyendo:

• Mantenimientos programados (comunicados con 24h de antelación).
• Incidencias causadas por terceros (proveedores cloud, internet, etc.).
• Casos de fuerza mayor.

No garantizamos un acceso ininterrumpido y no seremos responsables por daños derivados de interrupciones temporales del servicio.`
  },
  {
    title: "9. Limitación de responsabilidad",
    content: `En la máxima medida permitida por la ley aplicable:

• No somos responsables por pérdidas de datos causadas por el usuario o por terceros.
• No garantizamos la exactitud de los datos sincronizados desde proveedores externos.
• La responsabilidad total por daños directos no superará el importe pagado por los servicios en los 3 meses anteriores al evento causante del daño.
• No somos responsables por daños indirectos, pérdida de beneficios o daños consecuentes.

El usuario es responsable de verificar la exactitud de los datos sincronizados antes de publicarlos en sus tiendas.`
  },
  {
    title: "10. Modificaciones del servicio",
    content: `Nos reservamos el derecho de modificar, suspender o discontinuar cualquier parte del servicio con previo aviso razonable. En caso de cambios sustanciales en los precios o condiciones:

• Te notificaremos con al menos 30 días de antelación.
• Podrás cancelar tu suscripción antes de que entren en vigor los nuevos términos.
• Si continúas usando la Plataforma tras la fecha de vigencia, se entenderá que aceptas los nuevos términos.`
  },
  {
    title: "11. Ley aplicable y jurisdicción",
    content: `Estos Términos se rigen por la legislación española. Para la resolución de disputas, las partes se someten a los juzgados y tribunales de la ciudad de domicilio del proveedor del servicio, con renuncia expresa a cualquier otro fuero.

Para usuarios consumidores (si aplica), se respetarán los derechos reconocidos por la legislación de protección al consumidor de su país de residencia.`
  },
  {
    title: "12. Contacto",
    content: `Para cualquier consulta sobre estos Términos, puedes contactarnos a través del formulario de contacto disponible en la Plataforma o por email. Intentaremos responderte en el plazo más breve posible.`
  },
];

export default function Terms() {
  const { branding, theme } = useApp();
  const dark = theme === "dark";
  const appName = branding.app_name || "StockHUB";
  const today = new Date().toLocaleDateString("es-ES", { year: "numeric", month: "long", day: "numeric" });

  const render = (text) => text.replace(/{app_name}/g, appName);

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <SectionLabel>Legal</SectionLabel>
          <h1 className={cn("mt-4 text-4xl lg:text-5xl font-bold mb-4", dark ? "text-white" : "text-slate-900")}>
            Términos y Condiciones
          </h1>
          <p className={cn("text-sm", dark ? "text-slate-400" : "text-slate-500")}>
            Última actualización: {today}
          </p>
        </div>
      </section>

      <section className={cn("pb-20 lg:pb-28", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={cn(
            "rounded-2xl border p-8 lg:p-12 space-y-10",
            dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100 shadow-sm"
          )}>
            <p className={cn("text-base leading-relaxed", dark ? "text-slate-300" : "text-slate-600")}>
              Por favor, lee estos Términos y Condiciones detenidamente antes de utilizar la plataforma <strong>{appName}</strong>. El uso de la plataforma implica la aceptación plena de estos términos.
            </p>

            {SECTIONS.map((section, i) => (
              <div key={i} className="space-y-4">
                <h2 className={cn("text-xl font-bold", dark ? "text-white" : "text-slate-900")}>
                  {section.title}
                </h2>
                <div className={cn("text-sm leading-relaxed space-y-2", dark ? "text-slate-300" : "text-slate-600")}>
                  {render(section.content).split('\n').map((line, j) => {
                    if (line.startsWith('• **')) {
                      const match = line.match(/^• \*\*(.+?)\*\*: (.+)$/);
                      if (match) {
                        return (
                          <p key={j} className="flex gap-2">
                            <span>•</span>
                            <span><strong className={dark ? "text-white" : "text-slate-800"}>{match[1]}</strong>: {match[2]}</span>
                          </p>
                        );
                      }
                    }
                    if (line.startsWith('**') && line.endsWith('**:')) {
                      return <p key={j} className={cn("font-semibold mt-3", dark ? "text-white" : "text-slate-800")}>{line.replace(/\*\*/g, '').slice(0, -1)}:</p>;
                    }
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <p key={j} className={cn("font-semibold", dark ? "text-white" : "text-slate-800")}>{line.replace(/\*\*/g, '')}</p>;
                    }
                    if (line.startsWith('• ')) {
                      return <p key={j} className="flex gap-2"><span>•</span><span>{line.slice(2)}</span></p>;
                    }
                    if (line === '') return null;
                    return <p key={j}>{line}</p>;
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
