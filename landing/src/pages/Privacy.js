import { useApp } from "../context/AppContext";
import { cn, SectionLabel } from "../components/ui";

const SECTIONS = [
  {
    title: "1. Responsable del tratamiento",
    content: `El responsable del tratamiento de los datos personales es la empresa titular de la plataforma {app_name}. Para cualquier consulta relacionada con la privacidad, puedes contactarnos en la dirección de correo indicada en el apartado de contacto.`
  },
  {
    title: "2. Datos que recopilamos",
    content: `Recopilamos los siguientes tipos de datos:

• **Datos de registro**: nombre, dirección de email, empresa y contraseña (almacenada con hash bcrypt).
• **Datos de uso**: logs de sincronización, estadísticas de uso de la plataforma, preferencias de configuración.
• **Datos de pago**: procesados directamente por Stripe. No almacenamos datos de tarjetas de crédito en nuestros servidores.
• **Datos técnicos**: dirección IP, tipo de navegador, sistema operativo (recogidos en logs del servidor).
• **Datos de proveedores**: catálogos, precios y stock que importas en la plataforma. Estos datos son exclusivamente tuyos.`
  },
  {
    title: "3. Finalidad del tratamiento",
    content: `Utilizamos tus datos para:

• Proporcionar y mejorar los servicios de la plataforma {app_name}.
• Gestionar tu cuenta y suscripción.
• Enviarte comunicaciones transaccionales (confirmaciones, alertas, facturas).
• Enviarte comunicaciones comerciales, solo con tu consentimiento expreso.
• Cumplir con obligaciones legales y fiscales.
• Prevenir fraudes y garantizar la seguridad de la plataforma.`
  },
  {
    title: "4. Base legal del tratamiento",
    content: `El tratamiento de tus datos se basa en:

• **Ejecución del contrato**: necesario para prestarte el servicio contratado.
• **Interés legítimo**: para mejorar la plataforma y prevenir fraudes.
• **Consentimiento**: para el envío de comunicaciones comerciales (puedes retirarlo en cualquier momento).
• **Obligación legal**: cuando es requerido por la normativa aplicable.`
  },
  {
    title: "5. Conservación de datos",
    content: `Conservamos tus datos mientras mantengas una cuenta activa en {app_name}. Tras la cancelación de tu cuenta:

• Los datos de la cuenta se eliminan transcurridos 30 días.
• Los datos de facturación se conservan durante 7 años por obligación legal fiscal.
• Los logs técnicos se eliminan automáticamente tras 90 días.

Puedes solicitar la eliminación inmediata de tus datos contactándonos, salvo las obligaciones de conservación legales.`
  },
  {
    title: "6. Compartición de datos",
    content: `No vendemos ni alquilamos tus datos a terceros. Compartimos información solo con:

• **Proveedores de infraestructura** (servidores cloud en la UE): para alojar la plataforma.
• **Stripe**: para el procesamiento seguro de pagos.
• **Proveedores de email transaccional**: para envío de notificaciones y alertas.
• **Autoridades competentes**: cuando sea legalmente requerido.

Todos los proveedores están sujetos a acuerdos de procesamiento de datos conforme al RGPD.`
  },
  {
    title: "7. Transferencias internacionales",
    content: `Los datos se almacenan preferentemente en servidores ubicados en la Unión Europea. En caso de transferencia a terceros países, garantizamos el cumplimiento mediante cláusulas contractuales tipo aprobadas por la Comisión Europea.`
  },
  {
    title: "8. Tus derechos",
    content: `En virtud del RGPD, tienes derecho a:

• **Acceso**: obtener confirmación sobre si tratamos tus datos y acceder a ellos.
• **Rectificación**: corregir datos inexactos o incompletos.
• **Supresión**: solicitar la eliminación de tus datos ("derecho al olvido").
• **Limitación**: restringir el tratamiento en determinadas circunstancias.
• **Portabilidad**: recibir tus datos en formato estructurado y legible por máquina.
• **Oposición**: oponerte al tratamiento basado en interés legítimo.
• **Revocación del consentimiento**: retirar el consentimiento en cualquier momento.

Para ejercer estos derechos, contáctanos a través del formulario de contacto o directamente por email.`
  },
  {
    title: "9. Seguridad de los datos",
    content: `Implementamos medidas técnicas y organizativas apropiadas para proteger tus datos, incluyendo:

• Cifrado TLS 1.3 para todas las comunicaciones.
• Almacenamiento con cifrado en reposo.
• Acceso con autenticación JWT y control por roles (RBAC).
• Copias de seguridad automáticas diarias.
• Monitorización continua de seguridad.
• Equipo con acceso mínimo necesario a los datos.`
  },
  {
    title: "10. Cookies",
    content: `Utilizamos las siguientes cookies:

• **Cookies esenciales**: necesarias para el funcionamiento de la plataforma (autenticación, sesión).
• **Cookies analíticas**: para entender cómo se usa la plataforma y mejorarla (requieren consentimiento).

Puedes gestionar las preferencias de cookies en la configuración de tu navegador.`
  },
  {
    title: "11. Cambios en esta política",
    content: `Podemos actualizar esta política de privacidad periódicamente. Te notificaremos por email sobre cambios significativos. La fecha de última actualización siempre estará indicada al inicio del documento.`
  },
  {
    title: "12. Contacto y reclamaciones",
    content: `Para cualquier consulta sobre privacidad, contacta con nosotros a través del formulario de contacto de la web.

Si no estás satisfecho con nuestra respuesta, tienes derecho a presentar una reclamación ante la Agencia Española de Protección de Datos (AEPD) en www.aepd.es.`
  },
];

export default function Privacy() {
  const { branding, theme } = useApp();
  const dark = theme === "dark";
  const appName = branding.app_name || "SyncStock";
  const today = new Date().toLocaleDateString("es-ES", { year: "numeric", month: "long", day: "numeric" });

  const render = (text) => text.replace(/{app_name}/g, appName);

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <SectionLabel>Legal</SectionLabel>
          <h1 className={cn("mt-4 text-4xl lg:text-5xl font-bold mb-4", dark ? "text-white" : "text-slate-900")}>
            Política de Privacidad
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
              En <strong>{appName}</strong> nos comprometemos a proteger tu privacidad y a gestionar tus datos personales de forma transparente y conforme al Reglamento General de Protección de Datos (RGPD/GDPR) y la normativa española aplicable.
            </p>

            {SECTIONS.map((section, i) => (
              <div key={i} className="space-y-4">
                <h2 className={cn("text-xl font-bold", dark ? "text-white" : "text-slate-900")}>
                  {section.title}
                </h2>
                <div className={cn("text-sm leading-relaxed space-y-2 whitespace-pre-line", dark ? "text-slate-300" : "text-slate-600")}>
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
                    if (line.startsWith('• ')) {
                      return <p key={j} className="flex gap-2"><span>•</span><span>{line.slice(2)}</span></p>;
                    }
                    if (line === '') return <br key={j} />;
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
