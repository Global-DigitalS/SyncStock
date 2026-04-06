import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import {
  DollarSign, Key, Eye, EyeOff, RefreshCw, CheckCircle, XCircle,
  CreditCard, AlertTriangle, ExternalLink, Shield
} from "lucide-react";
import { api, useAuth } from "../App";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";

const AdminStripe = () => {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showSecretKey, setShowSecretKey] = useState(false);
  const [config, setConfig] = useState({
    stripe_public_key: "",
    stripe_secret_key: "",
    stripe_webhook_secret: "",
    is_live_mode: false,
    enabled: false
  });
  // Track whether secret fields already have a saved value in DB
  const [hasSecretKey, setHasSecretKey] = useState(false);
  const [hasWebhookSecret, setHasWebhookSecret] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  const fetchConfig = async () => {
    try {
      const res = await api.get("/admin/stripe/config");
      const data = res.data;
      // Track if secret fields have saved values, but don't put masked values in inputs
      setHasSecretKey(!!data.stripe_secret_key);
      setHasWebhookSecret(!!data.stripe_webhook_secret);
      setConfig({
        ...data,
        // Clear masked values so the user sees empty inputs with placeholder
        stripe_secret_key: "",
        stripe_webhook_secret: ""
      });
      if (data.stripe_secret_key) {
        testConnection();
      }
    } catch (error) {
      if (error.response?.status !== 404) {
        toast.error("Error al cargar configuración de Stripe");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading) return;

    // If no user or not superadmin, redirect
    if (!user || user.role !== "superadmin") {
      navigate("/");
      return;
    }

    fetchConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, navigate]);

  const testConnection = async () => {
    setTesting(true);
    try {
      const res = await api.post("/admin/stripe/test-connection");
      setConnectionStatus(res.data);
    } catch (error) {
      setConnectionStatus({ 
        success: false, 
        message: error.response?.data?.detail || "Error al conectar con Stripe" 
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!config.stripe_secret_key && !hasSecretKey) {
      toast.error("La clave secreta de Stripe es obligatoria");
      return;
    }

    setSaving(true);
    try {
      // Only send secret fields if user entered a new value
      const payload = { ...config };
      if (!payload.stripe_secret_key) delete payload.stripe_secret_key;
      if (!payload.stripe_webhook_secret) delete payload.stripe_webhook_secret;

      await api.put("/admin/stripe/config", payload);
      toast.success("Configuración de Stripe guardada");
      // Update saved-state flags if user provided new values
      if (config.stripe_secret_key) setHasSecretKey(true);
      if (config.stripe_webhook_secret) setHasWebhookSecret(true);
      // Clear inputs again after save
      setConfig(prev => ({ ...prev, stripe_secret_key: "", stripe_webhook_secret: "" }));
      testConnection();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  // Show loading while auth is being verified
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
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Configuración de Stripe
        </h1>
        <p className="text-slate-500">
          Configura tu cuenta de Stripe para procesar pagos de suscripciones
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Config */}
        <div className="lg:col-span-2 space-y-6">
          {/* API Keys */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <Key className="w-5 h-5 text-indigo-600" />
                Claves de API
              </CardTitle>
              <CardDescription>
                Obtén tus claves desde el{" "}
                <a 
                  href="https://dashboard.stripe.com/apikeys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-indigo-600 hover:underline inline-flex items-center gap-1"
                >
                  Dashboard de Stripe <ExternalLink className="w-3 h-3" />
                </a>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Public Key */}
              <div className="space-y-2">
                <Label htmlFor="public-key">Clave Pública (Publishable Key)</Label>
                <Input
                  id="public-key"
                  value={config.stripe_public_key}
                  onChange={(e) => setConfig({ ...config, stripe_public_key: e.target.value })}
                  placeholder="pk_test_..."
                  className="input-base font-mono text-sm"
                  data-testid="stripe-public-key"
                />
                <p className="text-xs text-slate-500">Comienza con pk_test_ o pk_live_</p>
              </div>

              {/* Secret Key */}
              <div className="space-y-2">
                <Label htmlFor="secret-key">Clave Secreta (Secret Key)</Label>
                <div className="relative">
                  <Input
                    id="secret-key"
                    type={showSecretKey ? "text" : "password"}
                    value={config.stripe_secret_key}
                    onChange={(e) => setConfig({ ...config, stripe_secret_key: e.target.value })}
                    placeholder={hasSecretKey ? "••••  (guardada — dejar vacío para mantener)" : "sk_test_..."}
                    className="input-base font-mono text-sm pr-10"
                    data-testid="stripe-secret-key"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecretKey(!showSecretKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showSecretKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-slate-500">Comienza con sk_test_ o sk_live_</p>
              </div>

              {/* Webhook Secret */}
              <div className="space-y-2">
                <Label htmlFor="webhook-secret">Webhook Secret (opcional)</Label>
                <Input
                  id="webhook-secret"
                  type="password"
                  value={config.stripe_webhook_secret}
                  onChange={(e) => setConfig({ ...config, stripe_webhook_secret: e.target.value })}
                  placeholder={hasWebhookSecret ? "••••  (guardado — dejar vacío para mantener)" : "whsec_..."}
                  className="input-base font-mono text-sm"
                  data-testid="stripe-webhook-secret"
                />
                <p className="text-xs text-slate-500">Necesario para recibir eventos de Stripe</p>
              </div>
            </CardContent>
          </Card>

          {/* Settings */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <Shield className="w-5 h-5 text-indigo-600" />
                Configuración
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Enable/Disable */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-medium text-slate-900">Habilitar pagos con Stripe</p>
                  <p className="text-sm text-slate-500">Activa o desactiva los pagos en la plataforma</p>
                </div>
                <Switch
                  checked={config.enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
                  data-testid="stripe-enabled-switch"
                />
              </div>

              {/* Live Mode Warning */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-medium text-slate-900">Modo Producción</p>
                  <p className="text-sm text-slate-500">Usar claves de producción (pagos reales)</p>
                </div>
                <Switch
                  checked={config.is_live_mode}
                  onCheckedChange={(checked) => setConfig({ ...config, is_live_mode: checked })}
                  data-testid="stripe-live-mode-switch"
                />
              </div>

              {config.is_live_mode && (
                <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-800">Modo Producción Activado</p>
                    <p className="text-sm text-amber-700">
                      Los pagos serán reales. Asegúrate de usar las claves de producción (pk_live_, sk_live_)
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => testConnection()}
              disabled={testing || (!config.stripe_secret_key && !hasSecretKey)}
              className="btn-secondary"
            >
              {testing ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
              Probar Conexión
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving}
              className="btn-primary"
              data-testid="save-stripe-config"
            >
              {saving ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <DollarSign className="w-4 h-4 mr-2" />}
              Guardar Configuración
            </Button>
          </div>
        </div>

        {/* Status Panel */}
        <div className="space-y-6">
          {/* Connection Status */}
          <Card className={`border-2 ${
            connectionStatus?.success ? 'border-emerald-200 bg-emerald-50/50' : 
            connectionStatus === null ? 'border-slate-200' : 'border-rose-200 bg-rose-50/50'
          }`}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {connectionStatus?.success ? (
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                ) : connectionStatus === null ? (
                  <CreditCard className="w-5 h-5 text-slate-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-600" />
                )}
                Estado de Conexión
              </CardTitle>
            </CardHeader>
            <CardContent>
              {connectionStatus === null ? (
                <p className="text-slate-500 text-sm">Configura tus claves y prueba la conexión</p>
              ) : connectionStatus.success ? (
                <div className="space-y-2">
                  <Badge className="bg-emerald-100 text-emerald-700">Conectado</Badge>
                  <p className="text-sm text-emerald-700">{connectionStatus.message}</p>
                  {connectionStatus.account_name && (
                    <p className="text-xs text-slate-500">Cuenta: {connectionStatus.account_name}</p>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <Badge className="bg-rose-100 text-rose-700">Error</Badge>
                  <p className="text-sm text-rose-700">{connectionStatus.message}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Info */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Información
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="font-medium text-slate-700">Webhook URL</p>
                <code className="text-xs bg-slate-100 px-2 py-1 rounded block mt-1 break-all">
                  {window.location.origin}/api/stripe/webhook
                </code>
              </div>
              <div>
                <p className="font-medium text-slate-700">Eventos requeridos</p>
                <ul className="text-xs text-slate-500 mt-1 space-y-1">
                  <li>• checkout.session.completed</li>
                  <li>• customer.subscription.updated</li>
                  <li>• customer.subscription.deleted</li>
                  <li>• invoice.paid</li>
                  <li>• invoice.payment_failed</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminStripe;
