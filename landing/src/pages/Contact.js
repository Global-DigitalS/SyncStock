import { useState } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, SectionLabel, SectionTitle, SectionSubtitle } from "../components/ui";
import { useSEO } from "../hooks/useSEO";
import axios from "axios";

export default function Contact() {
  const { branding, theme, API_URL } = useApp();
  const dark = theme === "dark";

  useSEO({
    title: "Contacto",
    description: "¿Tienes dudas sobre SyncStock? Contacta con nuestro equipo. Respondemos en menos de 24 horas laborables.",
    canonical: "/contacto",
    structuredData: {
      "@context": "https://schema.org",
      "@type": "ContactPage",
      "name": "Contacto — SyncStock",
      "description": "Página de contacto de SyncStock. Formulario de contacto para soporte y consultas."
    }
  });

  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [status, setStatus] = useState(null); // null | "loading" | "success" | "error"

  const handleChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) return;
    setStatus("loading");
    try {
      // Try to send via backend email endpoint, fallback gracefully
      await axios.post(`${API_URL}/api/contact`, form, { timeout: 8000 });
      setStatus("success");
      setForm({ name: "", email: "", subject: "", message: "" });
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className={cn("min-h-screen pt-20", dark ? "bg-slate-950" : "bg-white")}>

      {/* Hero */}
      <section className={cn("py-16 lg:py-24", dark ? "bg-slate-950" : "bg-gradient-to-b from-slate-50 to-white")}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <SectionLabel>Contacto</SectionLabel>
          <SectionTitle className={cn("mt-4", dark ? "text-white" : "")}>
            Estamos aquí para <span className="text-indigo-600">ayudarte</span>
          </SectionTitle>
          <SectionSubtitle className="mt-4">
            ¿Tienes dudas, necesitas soporte o quieres conocer más sobre {branding.app_name}? Escríbenos.
          </SectionSubtitle>
        </div>
      </section>

      {/* Content */}
      <section className={cn("pb-20 lg:pb-28", dark ? "bg-slate-950" : "bg-white")}>
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">

            {/* Form */}
            <div>
              <div className={cn(
                "rounded-2xl border p-8",
                dark ? "bg-slate-800 border-slate-700" : "bg-white border-slate-100 shadow-sm"
              )}>
                <h2 className={cn("text-xl font-bold mb-6", dark ? "text-white" : "text-slate-900")}>
                  Envíanos un mensaje
                </h2>

                {status === "success" ? (
                  <div className={cn("rounded-xl p-6 text-center", dark ? "bg-emerald-950 border border-emerald-800" : "bg-emerald-50 border border-emerald-100")}>
                    <CheckCircle2 size={40} className="text-emerald-500 mx-auto mb-4" />
                    <p className={cn("font-semibold text-lg mb-2", dark ? "text-emerald-300" : "text-emerald-800")}>
                      ¡Mensaje enviado!
                    </p>
                    <p className={cn("text-sm", dark ? "text-emerald-400" : "text-emerald-600")}>
                      Te responderemos en menos de 24 horas laborables.
                    </p>
                    <button
                      onClick={() => setStatus(null)}
                      className="mt-4 text-sm text-indigo-500 hover:text-indigo-600 font-medium"
                    >
                      Enviar otro mensaje
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid sm:grid-cols-2 gap-5">
                      <div>
                        <label className={cn("block text-sm font-medium mb-2", dark ? "text-slate-300" : "text-slate-700")}>
                          Nombre *
                        </label>
                        <input
                          name="name"
                          value={form.name}
                          onChange={handleChange}
                          required
                          placeholder="Tu nombre"
                          className={cn(
                            "w-full px-4 py-3 rounded-xl border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500",
                            dark
                              ? "bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-indigo-500"
                              : "bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-300"
                          )}
                        />
                      </div>
                      <div>
                        <label className={cn("block text-sm font-medium mb-2", dark ? "text-slate-300" : "text-slate-700")}>
                          Email *
                        </label>
                        <input
                          name="email"
                          type="email"
                          value={form.email}
                          onChange={handleChange}
                          required
                          placeholder="tu@empresa.com"
                          className={cn(
                            "w-full px-4 py-3 rounded-xl border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500",
                            dark
                              ? "bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-indigo-500"
                              : "bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-300"
                          )}
                        />
                      </div>
                    </div>

                    <div>
                      <label className={cn("block text-sm font-medium mb-2", dark ? "text-slate-300" : "text-slate-700")}>
                        Asunto
                      </label>
                      <input
                        name="subject"
                        value={form.subject}
                        onChange={handleChange}
                        placeholder="¿En qué podemos ayudarte?"
                        className={cn(
                          "w-full px-4 py-3 rounded-xl border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500",
                          dark
                            ? "bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-indigo-500"
                            : "bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-300"
                        )}
                      />
                    </div>

                    <div>
                      <label className={cn("block text-sm font-medium mb-2", dark ? "text-slate-300" : "text-slate-700")}>
                        Mensaje *
                      </label>
                      <textarea
                        name="message"
                        value={form.message}
                        onChange={handleChange}
                        required
                        rows={6}
                        placeholder="Cuéntanos tu consulta o necesidad..."
                        className={cn(
                          "w-full px-4 py-3 rounded-xl border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none",
                          dark
                            ? "bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-indigo-500"
                            : "bg-white border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-300"
                        )}
                      />
                    </div>

                    {status === "error" && (
                      <div className={cn("flex items-center gap-2 p-3 rounded-xl text-sm", dark ? "bg-red-950 text-red-300 border border-red-800" : "bg-red-50 text-red-700 border border-red-100")}>
                        <AlertCircle size={16} />
                        Error al enviar. Por favor inténtalo de nuevo.
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={status === "loading"}
                      className={cn(
                        "w-full px-6 py-3.5 bg-indigo-600 text-white font-semibold rounded-xl transition-all",
                        status === "loading"
                          ? "opacity-70 cursor-not-allowed"
                          : "hover:bg-indigo-700 hover:shadow-lg hover:-translate-y-0.5"
                      )}
                    >
                      {status === "loading" ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full spinner" />
                          Enviando...
                        </span>
                      ) : "Enviar mensaje"}
                    </button>

                    <p className={cn("text-xs text-center", dark ? "text-slate-500" : "text-slate-400")}>
                      Al enviar, aceptas nuestra{" "}
                      <a href="/privacidad" className="text-indigo-500 hover:underline">política de privacidad</a>.
                    </p>
                  </form>
                )}
              </div>
            </div>

        </div>
      </section>
    </div>
  );
}
