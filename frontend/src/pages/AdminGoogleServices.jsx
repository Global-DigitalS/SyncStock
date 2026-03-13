import { useState, useEffect } from "react";
import { api, useAuth } from "../App";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  BarChart3, Search, Tags, Megaphone, RefreshCw, CheckCircle,
  ExternalLink, Eye, EyeOff, Save, Info
} from "lucide-react";

const SERVICE_CARDS = [
  {
    key: "analytics",
    title: "Google Analytics",
    description: "Seguimiento de visitas, comportamiento de usuarios y conversiones en tu plataforma.",
    icon: BarChart3,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    docsUrl: "https://analytics.google.com/",
    fields: [
      {
        key: "analytics_measurement_id",
        label: "Measurement ID",
        placeholder: "G-XXXXXXXXXX",
        hint: "Formato: G-XXXXXXXXXX. Encuéntralo en Admin > Flujos de datos.",
      },
      {
        key: "analytics_api_secret",
        label: "API Secret (opcional)",
        placeholder: "Tu API Secret",
        hint: "Solo necesario para enviar eventos desde el servidor.",
        secret: true,
      },
    ],
    enabledKey: "analytics_enabled",
  },
  {
    key: "search_console",
    title: "Google Search Console",
    description: "Monitorea el rendimiento de búsqueda, indexación y problemas de SEO.",
    icon: Search,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    docsUrl: "https://search.google.com/search-console",
    fields: [
      {
        key: "search_console_property_url",
        label: "URL de la Propiedad",
        placeholder: "https://tudominio.com",
        hint: "La URL del sitio registrado en Search Console.",
      },
      {
        key: "search_console_verification_code",
        label: "Código de Verificación",
        placeholder: "google-site-verification=XXXXXXXXXXXX",
        hint: "Meta tag de verificación proporcionado por Google.",
      },
    ],
    enabledKey: "search_console_enabled",
  },
  {
    key: "tag_manager",
    title: "Google Tag Manager",
    description: "Gestiona etiquetas de marketing y análisis sin modificar el código.",
    icon: Tags,
    color: "text-cyan-600",
    bgColor: "bg-cyan-50",
    borderColor: "border-cyan-200",
    docsUrl: "https://tagmanager.google.com/",
    fields: [
      {
        key: "tag_manager_container_id",
        label: "Container ID",
        placeholder: "GTM-XXXXXXX",
        hint: "Formato: GTM-XXXXXXX. Encuéntralo en la parte superior de tu contenedor.",
      },
    ],
    enabledKey: "tag_manager_enabled",
  },
  {
    key: "google_ads",
    title: "Google Ads",
    description: "Seguimiento de conversiones y remarketing para tus campañas publicitarias.",
    icon: Megaphone,
    color: "text-green-600",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    docsUrl: "https://ads.google.com/",
    fields: [
      {
        key: "google_ads_conversion_id",
        label: "Conversion ID",
        placeholder: "AW-XXXXXXXXX",
        hint: "Formato: AW-XXXXXXXXX. Encuéntralo en Herramientas > Conversiones.",
      },
      {
        key: "google_ads_conversion_label",
        label: "Conversion Label (opcional)",
        placeholder: "XXXXXXXXXXXXXXXXXXX",
        hint: "Etiqueta de conversión específica para el seguimiento.",
      },
    ],
    enabledKey: "google_ads_enabled",
  },
];

const AdminGoogleServices = () => {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSecrets, setShowSecrets] = useState({});
  const [config, setConfig] = useState({
    analytics_enabled: false,
    analytics_measurement_id: "",
    analytics_api_secret: "",
    search_console_enabled: false,
    search_console_property_url: "",
    search_console_verification_code: "",
    tag_manager_enabled: false,
    tag_manager_container_id: "",
    google_ads_enabled: false,
    google_ads_conversion_id: "",
    google_ads_conversion_label: "",
  });

  useEffect(() => {
    if (authLoading) return;
    if (!user || user.role !== "superadmin") {
      navigate("/");
      return;
    }
    fetchConfig();
  }, [user, authLoading, navigate]);

  const fetchConfig = async () => {
    try {
      const res = await api.get("/admin/google-services");
      setConfig((prev) => ({ ...prev, ...res.data }));
    } catch (error) {
      if (error.response?.status !== 404) {
        toast.error("Error al cargar configuración de Google");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/admin/google-services", config);
      toast.success("Configuración de Google guardada correctamente");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const updateField = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const toggleSecret = (key) => {
    setShowSecrets((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const getEnabledCount = () => {
    return SERVICE_CARDS.filter((s) => config[s.enabledKey]).length;
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: "Manrope, sans-serif" }}>
          Servicios de Google
        </h1>
        <p className="text-slate-500">
          Conecta tu plataforma con los servicios de Google para análisis, SEO, etiquetas y publicidad
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {SERVICE_CARDS.map((service) => {
          const Icon = service.icon;
          const enabled = config[service.enabledKey];
          return (
            <div
              key={service.key}
              className={`p-4 rounded-xl border-2 transition-all ${
                enabled ? `${service.borderColor} ${service.bgColor}` : "border-slate-100 bg-slate-50"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-5 h-5 ${enabled ? service.color : "text-slate-400"}`} />
                <span className="text-xs font-medium text-slate-600">
                  {service.title.replace("Google ", "")}
                </span>
              </div>
              <Badge className={enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}>
                {enabled ? "Activo" : "Inactivo"}
              </Badge>
            </div>
          );
        })}
      </div>

      {/* Service Cards */}
      <div className="space-y-6">
        {SERVICE_CARDS.map((service) => {
          const Icon = service.icon;
          const enabled = config[service.enabledKey];

          return (
            <Card
              key={service.key}
              className={`border-2 transition-all ${enabled ? service.borderColor : "border-slate-200"}`}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${service.bgColor}`}>
                      <Icon className={`w-6 h-6 ${service.color}`} />
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2" style={{ fontFamily: "Manrope, sans-serif" }}>
                        {service.title}
                        <a
                          href={service.docsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-400 hover:text-indigo-600 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </CardTitle>
                      <CardDescription className="mt-1">{service.description}</CardDescription>
                    </div>
                  </div>
                  <Switch
                    checked={enabled}
                    onCheckedChange={(checked) => updateField(service.enabledKey, checked)}
                  />
                </div>
              </CardHeader>

              {enabled && (
                <CardContent className="space-y-4 pt-0">
                  <div className="border-t border-slate-100 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {service.fields.map((field) => (
                        <div key={field.key} className="space-y-2">
                          <Label htmlFor={field.key}>{field.label}</Label>
                          <div className="relative">
                            <Input
                              id={field.key}
                              type={field.secret && !showSecrets[field.key] ? "password" : "text"}
                              value={config[field.key] || ""}
                              onChange={(e) => updateField(field.key, e.target.value)}
                              placeholder={field.placeholder}
                              className="input-base font-mono text-sm pr-10"
                            />
                            {field.secret && (
                              <button
                                type="button"
                                onClick={() => toggleSecret(field.key)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                              >
                                {showSecrets[field.key] ? (
                                  <EyeOff className="w-4 h-4" />
                                ) : (
                                  <Eye className="w-4 h-4" />
                                )}
                              </button>
                            )}
                          </div>
                          {field.hint && (
                            <p className="text-xs text-slate-500 flex items-start gap-1">
                              <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                              {field.hint}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>

      {/* Save Button */}
      <div className="flex justify-between items-center mt-8 pt-6 border-t border-slate-200">
        <p className="text-sm text-slate-500">
          {getEnabledCount()} de {SERVICE_CARDS.length} servicios activos
        </p>
        <Button onClick={handleSave} disabled={saving} className="btn-primary">
          {saving ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Guardar Configuración
        </Button>
      </div>

      {/* Info Card */}
      <Card className="mt-6 border-slate-200 bg-slate-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-slate-600 space-y-1">
              <p className="font-medium">Notas importantes:</p>
              <ul className="list-disc list-inside space-y-1 text-slate-500">
                <li>Los scripts de tracking se inyectarán automáticamente en las páginas públicas cuando estén habilitados.</li>
                <li>Google Tag Manager puede gestionar Analytics y Ads, evita duplicar configuraciones.</li>
                <li>Los cambios se aplican inmediatamente tras guardar.</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminGoogleServices;
