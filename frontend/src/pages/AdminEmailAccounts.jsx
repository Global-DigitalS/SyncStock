import { useState, useEffect } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Mail,
  Server,
  Lock,
  User,
  Send,
  CheckCircle,
  XCircle,
  RefreshCw,
  Eye,
  EyeOff,
  UserPlus,
  HeadphonesIcon,
  Receipt,
  Settings,
  TestTube
} from "lucide-react";

// Email account types configuration
const EMAIL_TYPES = {
  transactional: {
    id: "transactional",
    name: "Transaccional",
    description: "Registro, cambio de contraseña, notificaciones del sistema",
    icon: UserPlus,
    color: "indigo",
    examples: ["Bienvenida", "Reset de contraseña", "Verificación de email"]
  },
  support: {
    id: "support",
    name: "Soporte",
    description: "Comunicación con usuarios, tickets de soporte",
    icon: HeadphonesIcon,
    color: "emerald",
    examples: ["Respuesta a tickets", "Seguimiento de incidencias"]
  },
  billing: {
    id: "billing",
    name: "Facturación",
    description: "Facturas, suscripciones, pagos",
    icon: Receipt,
    color: "amber",
    examples: ["Facturas", "Confirmación de pago", "Cambio de plan"]
  }
};

const defaultConfig = {
  smtp_host: "",
  smtp_port: 587,
  smtp_user: "",
  smtp_password: "",
  smtp_from_email: "",
  smtp_from_name: "",
  smtp_use_tls: true,
  smtp_use_ssl: false,
  enabled: false
};

const AdminEmailAccounts = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("transactional");
  const [configs, setConfigs] = useState({
    transactional: { ...defaultConfig, smtp_from_name: "SyncStock" },
    support: { ...defaultConfig, smtp_from_name: "Soporte SyncStock" },
    billing: { ...defaultConfig, smtp_from_name: "Facturación SyncStock" }
  });
  const [showPasswords, setShowPasswords] = useState({});
  const [saving, setSaving] = useState({});
  const [testing, setTesting] = useState({});
  const [connectionStatus, setConnectionStatus] = useState({});
  const [testEmails, setTestEmails] = useState({});

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const res = await api.get("/email/accounts");
      if (res.data) {
        setConfigs(prev => ({
          ...prev,
          ...res.data
        }));
      }
    } catch (error) {
      console.error("Error loading email configs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (accountType) => {
    setSaving(prev => ({ ...prev, [accountType]: true }));
    try {
      await api.put(`/email/accounts/${accountType}`, configs[accountType]);
      toast.success(`Configuración de ${EMAIL_TYPES[accountType].name} guardada`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(prev => ({ ...prev, [accountType]: false }));
    }
  };

  const handleTestConnection = async (accountType) => {
    setTesting(prev => ({ ...prev, [accountType]: true }));
    try {
      const res = await api.post(`/email/accounts/${accountType}/test-connection`);
      setConnectionStatus(prev => ({ ...prev, [accountType]: res.data }));
      if (res.data.success) {
        toast.success("Conexión exitosa");
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      setConnectionStatus(prev => ({
        ...prev,
        [accountType]: { success: false, message: error.response?.data?.detail || "Error de conexión" }
      }));
      toast.error("Error al probar conexión");
    } finally {
      setTesting(prev => ({ ...prev, [accountType]: false }));
    }
  };

  const handleSendTestEmail = async (accountType) => {
    if (!testEmails[accountType]) {
      toast.error("Introduce un email de prueba");
      return;
    }
    setTesting(prev => ({ ...prev, [`${accountType}_send`]: true }));
    try {
      await api.post(`/email/accounts/${accountType}/send-test`, {
        to_email: testEmails[accountType]
      });
      toast.success("Email de prueba enviado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al enviar");
    } finally {
      setTesting(prev => ({ ...prev, [`${accountType}_send`]: false }));
    }
  };

  const updateConfig = (accountType, field, value) => {
    setConfigs(prev => ({
      ...prev,
      [accountType]: {
        ...prev[accountType],
        [field]: value
      }
    }));
  };

  const renderAccountConfig = (accountType) => {
    const typeInfo = EMAIL_TYPES[accountType];
    const config = configs[accountType];
    const Icon = typeInfo.icon;
    const isEnabled = config.enabled;
    const status = connectionStatus[accountType];

    return (
      <div className="space-y-6">
        {/* Header with enable toggle */}
        <div className={`p-4 rounded-lg border-2 ${isEnabled ? `border-${typeInfo.color}-200 bg-${typeInfo.color}-50/50` : 'border-slate-200 bg-slate-50/50'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isEnabled ? `bg-${typeInfo.color}-100` : 'bg-slate-200'}`}>
                <Icon className={`w-5 h-5 ${isEnabled ? `text-${typeInfo.color}-600` : 'text-slate-500'}`} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">{typeInfo.name}</h3>
                <p className="text-sm text-slate-500">{typeInfo.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {status && (
                <Badge className={status.success ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}>
                  {status.success ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                  {status.success ? 'Conectado' : 'Error'}
                </Badge>
              )}
              <Switch
                checked={isEnabled}
                onCheckedChange={(checked) => updateConfig(accountType, 'enabled', checked)}
                data-testid={`enable-${accountType}`}
              />
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {typeInfo.examples.map((ex, i) => (
              <Badge key={i} variant="outline" className="text-xs">{ex}</Badge>
            ))}
          </div>
        </div>

        {/* Configuration Form */}
        <div className={`space-y-4 ${!isEnabled ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* SMTP Host */}
            <div className="space-y-2">
              <Label className="text-slate-700">Servidor SMTP</Label>
              <div className="relative">
                <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={config.smtp_host}
                  onChange={(e) => updateConfig(accountType, 'smtp_host', e.target.value)}
                  placeholder="smtp.ejemplo.com"
                  className="pl-10 input-base"
                  data-testid={`${accountType}-smtp-host`}
                />
              </div>
            </div>

            {/* SMTP Port */}
            <div className="space-y-2">
              <Label className="text-slate-700">Puerto</Label>
              <Input
                type="number"
                value={config.smtp_port}
                onChange={(e) => updateConfig(accountType, 'smtp_port', parseInt(e.target.value) || 587)}
                placeholder="587"
                className="input-base"
                data-testid={`${accountType}-smtp-port`}
              />
            </div>

            {/* SMTP User */}
            <div className="space-y-2">
              <Label className="text-slate-700">Usuario SMTP</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={config.smtp_user}
                  onChange={(e) => updateConfig(accountType, 'smtp_user', e.target.value)}
                  placeholder="usuario@ejemplo.com"
                  className="pl-10 input-base"
                  data-testid={`${accountType}-smtp-user`}
                />
              </div>
            </div>

            {/* SMTP Password */}
            <div className="space-y-2">
              <Label className="text-slate-700">Contraseña SMTP</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  type={showPasswords[accountType] ? "text" : "password"}
                  value={config.smtp_password}
                  onChange={(e) => updateConfig(accountType, 'smtp_password', e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 pr-10 input-base"
                  data-testid={`${accountType}-smtp-password`}
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords(prev => ({ ...prev, [accountType]: !prev[accountType] }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPasswords[accountType] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* From Email */}
            <div className="space-y-2">
              <Label className="text-slate-700">Email remitente</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  type="email"
                  value={config.smtp_from_email}
                  onChange={(e) => updateConfig(accountType, 'smtp_from_email', e.target.value)}
                  placeholder="noreply@ejemplo.com"
                  className="pl-10 input-base"
                  data-testid={`${accountType}-from-email`}
                />
              </div>
            </div>

            {/* From Name */}
            <div className="space-y-2">
              <Label className="text-slate-700">Nombre remitente</Label>
              <Input
                value={config.smtp_from_name}
                onChange={(e) => updateConfig(accountType, 'smtp_from_name', e.target.value)}
                placeholder="Mi Empresa"
                className="input-base"
                data-testid={`${accountType}-from-name`}
              />
            </div>
          </div>

          {/* TLS/SSL Options */}
          <div className="flex items-center gap-6 p-4 bg-slate-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Switch
                checked={config.smtp_use_tls}
                onCheckedChange={(checked) => {
                  updateConfig(accountType, 'smtp_use_tls', checked);
                  if (checked) updateConfig(accountType, 'smtp_use_ssl', false);
                }}
              />
              <Label className="text-sm">Usar TLS (STARTTLS)</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={config.smtp_use_ssl}
                onCheckedChange={(checked) => {
                  updateConfig(accountType, 'smtp_use_ssl', checked);
                  if (checked) updateConfig(accountType, 'smtp_use_tls', false);
                }}
              />
              <Label className="text-sm">Usar SSL directo</Label>
            </div>
          </div>

          {/* Test Section */}
          <div className="p-4 border border-slate-200 rounded-lg space-y-4">
            <h4 className="font-medium text-slate-700 flex items-center gap-2">
              <TestTube className="w-4 h-4" />
              Probar configuración
            </h4>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => handleTestConnection(accountType)}
                disabled={testing[accountType] || !config.smtp_host}
                className="btn-secondary"
              >
                {testing[accountType] ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Settings className="w-4 h-4 mr-2" />
                )}
                Probar conexión
              </Button>
            </div>
            <div className="flex gap-3">
              <Input
                type="email"
                value={testEmails[accountType] || ""}
                onChange={(e) => setTestEmails(prev => ({ ...prev, [accountType]: e.target.value }))}
                placeholder="email@prueba.com"
                className="input-base flex-1"
              />
              <Button
                variant="outline"
                onClick={() => handleSendTestEmail(accountType)}
                disabled={testing[`${accountType}_send`] || !config.smtp_host}
                className="btn-secondary"
              >
                {testing[`${accountType}_send`] ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Enviar prueba
              </Button>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={() => handleSave(accountType)}
              disabled={saving[accountType]}
              className="btn-primary"
              data-testid={`save-${accountType}`}
            >
              {saving[accountType] ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Guardar configuración
            </Button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
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
          Cuentas de Email
        </h1>
        <p className="text-slate-500">
          Configura diferentes cuentas de email para cada tipo de comunicación
        </p>
      </div>

      {/* Tabs for different email types */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-6">
          {Object.values(EMAIL_TYPES).map((type) => {
            const Icon = type.icon;
            const isEnabled = configs[type.id]?.enabled;
            return (
              <TabsTrigger
                key={type.id}
                value={type.id}
                className="flex items-center gap-2 data-[state=active]:bg-white"
                data-testid={`tab-${type.id}`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{type.name}</span>
                {isEnabled && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </TabsTrigger>
            );
          })}
        </TabsList>

        {Object.keys(EMAIL_TYPES).map((type) => (
          <TabsContent key={type} value={type}>
            <Card className="border-slate-200">
              <CardContent className="pt-6">
                {renderAccountConfig(type)}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Quick Info */}
      <Card className="mt-6 border-slate-200 bg-slate-50/50">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-slate-700 mb-3">Información importante</h3>
          <ul className="text-sm text-slate-600 space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-indigo-500">•</span>
              <span><strong>Transaccional:</strong> Se usa para emails automáticos del sistema (registro, contraseñas).</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500">•</span>
              <span><strong>Soporte:</strong> Para comunicación con usuarios y gestión de tickets.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500">•</span>
              <span><strong>Facturación:</strong> Para envío de facturas y notificaciones de pago.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-slate-400">•</span>
              <span>Si una cuenta no está habilitada, se usará la cuenta <strong>Transaccional</strong> como fallback.</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminEmailAccounts;
