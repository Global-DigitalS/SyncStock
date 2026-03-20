import { useState, useEffect } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
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
  Settings,
  TestTube,
  Inbox
} from "lucide-react";

const EmailConfig = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  
  const [config, setConfig] = useState({
    smtp_host: "",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
    smtp_from_email: "",
    smtp_from_name: "SyncStock",
    smtp_use_tls: true,
    smtp_use_ssl: false
  });
  
  const [testEmail, setTestEmail] = useState("");
  const [testTemplate, setTestTemplate] = useState("welcome");

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get("/email/config");
      setConfig({
        smtp_host: res.data.smtp_host || "",
        smtp_port: res.data.smtp_port || 587,
        smtp_user: res.data.smtp_user || "",
        smtp_password: "",
        smtp_from_email: res.data.smtp_from_email || "",
        smtp_from_name: res.data.smtp_from_name || "SyncStock",
        smtp_use_tls: res.data.smtp_use_tls ?? true,
        smtp_use_ssl: res.data.smtp_use_ssl ?? false
      });
      
      if (res.data.smtp_configured) {
        setConnectionStatus({ success: true, message: "Configuración guardada" });
      }
    } catch (error) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.smtp_host || !config.smtp_user || !config.smtp_password) {
      toast.error("Completa los campos obligatorios");
      return;
    }
    
    setTesting(true);
    setConnectionStatus(null);
    
    try {
      const res = await api.post("/email/test-connection", {
        smtp_host: config.smtp_host,
        smtp_port: config.smtp_port,
        smtp_user: config.smtp_user,
        smtp_password: config.smtp_password,
        smtp_use_tls: config.smtp_use_tls,
        smtp_use_ssl: config.smtp_use_ssl
      });
      
      setConnectionStatus(res.data);
      
      if (res.data.success) {
        toast.success(res.data.message);
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      setConnectionStatus({ success: false, message: "Error de conexión" });
      toast.error("Error al probar la conexión");
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!config.smtp_host || !config.smtp_user || !config.smtp_password) {
      toast.error("Completa los campos obligatorios");
      return;
    }
    
    setSaving(true);
    
    try {
      const res = await api.post("/email/config", {
        ...config,
        smtp_from_email: config.smtp_from_email || config.smtp_user
      });
      
      if (res.data.success) {
        toast.success("Configuración guardada correctamente");
        setConnectionStatus({ success: true, message: "Configuración guardada" });
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error("Error al guardar la configuración");
    } finally {
      setSaving(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail) {
      toast.error("Introduce un email de destino");
      return;
    }
    
    setSendingTest(true);
    
    try {
      const res = await api.post("/email/send-test", {
        to_email: testEmail,
        template: testTemplate
      });
      
      if (res.data.success) {
        toast.success("Email de prueba enviado");
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error("Error al enviar el email de prueba");
    } finally {
      setSendingTest(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Configuración de Email
          </h1>
          <p className="text-slate-500">
            Configura el servidor SMTP para enviar correos electrónicos desde la aplicación
          </p>
        </div>

        <div className="grid gap-6">
          {/* SMTP Configuration */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <Server className="w-5 h-5 text-indigo-600" />
                Servidor SMTP
              </CardTitle>
              <CardDescription>
                Configuración del servidor de correo saliente
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Host */}
                <div className="space-y-2">
                  <Label>Host SMTP *</Label>
                  <Input
                    value={config.smtp_host}
                    onChange={(e) => setConfig({ ...config, smtp_host: e.target.value })}
                    placeholder="smtp.gmail.com"
                    className="input-base"
                    data-testid="smtp-host"
                  />
                </div>
                
                {/* Port */}
                <div className="space-y-2">
                  <Label>Puerto *</Label>
                  <Input
                    type="number"
                    value={config.smtp_port}
                    onChange={(e) => setConfig({ ...config, smtp_port: parseInt(e.target.value) || 587 })}
                    placeholder="587"
                    className="input-base"
                    data-testid="smtp-port"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* User */}
                <div className="space-y-2">
                  <Label>Usuario *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      value={config.smtp_user}
                      onChange={(e) => setConfig({ ...config, smtp_user: e.target.value })}
                      placeholder="tu-email@gmail.com"
                      className="pl-10 input-base"
                      data-testid="smtp-user"
                    />
                  </div>
                </div>
                
                {/* Password */}
                <div className="space-y-2">
                  <Label>Contraseña *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      type={showPassword ? "text" : "password"}
                      value={config.smtp_password}
                      onChange={(e) => setConfig({ ...config, smtp_password: e.target.value })}
                      placeholder="••••••••"
                      className="pl-10 pr-10 input-base"
                      data-testid="smtp-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-slate-500">
                    Para Gmail, usa una "Contraseña de aplicación"
                  </p>
                </div>
              </div>

              {/* Security Options */}
              <div className="flex flex-wrap gap-6 pt-4 border-t border-slate-100">
                <div className="flex items-center gap-3">
                  <Switch
                    checked={config.smtp_use_tls}
                    onCheckedChange={(checked) => setConfig({ ...config, smtp_use_tls: checked, smtp_use_ssl: checked ? false : config.smtp_use_ssl })}
                    data-testid="smtp-tls"
                  />
                  <Label className="cursor-pointer">Usar STARTTLS (puerto 587)</Label>
                </div>
                <div className="flex items-center gap-3">
                  <Switch
                    checked={config.smtp_use_ssl}
                    onCheckedChange={(checked) => setConfig({ ...config, smtp_use_ssl: checked, smtp_use_tls: checked ? false : config.smtp_use_tls })}
                    data-testid="smtp-ssl"
                  />
                  <Label className="cursor-pointer">Usar SSL (puerto 465)</Label>
                </div>
              </div>

              {/* Test Connection */}
              <div className="flex items-center gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={testing || !config.smtp_host || !config.smtp_user || !config.smtp_password}
                  data-testid="test-smtp-btn"
                >
                  {testing ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4 mr-2" />
                  )}
                  Probar Conexión
                </Button>
                
                {connectionStatus && (
                  <div className={`flex items-center gap-2 text-sm ${
                    connectionStatus.success ? "text-emerald-600" : "text-rose-600"
                  }`}>
                    {connectionStatus.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    {connectionStatus.message}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Sender Configuration */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <Mail className="w-5 h-5 text-indigo-600" />
                Remitente
              </CardTitle>
              <CardDescription>
                Información que verán los destinatarios
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email del remitente</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      value={config.smtp_from_email}
                      onChange={(e) => setConfig({ ...config, smtp_from_email: e.target.value })}
                      placeholder={config.smtp_user || "noreply@empresa.com"}
                      className="pl-10 input-base"
                      data-testid="smtp-from-email"
                    />
                  </div>
                  <p className="text-xs text-slate-500">Dejar vacío para usar el usuario SMTP</p>
                </div>
                
                <div className="space-y-2">
                  <Label>Nombre del remitente</Label>
                  <Input
                    value={config.smtp_from_name}
                    onChange={(e) => setConfig({ ...config, smtp_from_name: e.target.value })}
                    placeholder="SyncStock"
                    className="input-base"
                    data-testid="smtp-from-name"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Test Email */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <Send className="w-5 h-5 text-indigo-600" />
                Enviar Email de Prueba
              </CardTitle>
              <CardDescription>
                Verifica que los correos se envían correctamente
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <Label>Email de destino</Label>
                  <div className="relative">
                    <Inbox className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      type="email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      placeholder="tu-email@ejemplo.com"
                      className="pl-10 input-base"
                      data-testid="test-email-input"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Plantilla</Label>
                  <Select value={testTemplate} onValueChange={setTestTemplate}>
                    <SelectTrigger className="input-base" data-testid="test-template-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="welcome">Bienvenida</SelectItem>
                      <SelectItem value="password_reset">Recuperar contraseña</SelectItem>
                      <SelectItem value="subscription_change">Cambio de plan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <Button
                onClick={handleSendTestEmail}
                disabled={sendingTest || !testEmail}
                variant="outline"
                data-testid="send-test-email-btn"
              >
                {sendingTest ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Enviar Email de Prueba
              </Button>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              disabled={saving || !config.smtp_host || !config.smtp_user || !config.smtp_password}
              className="btn-primary"
              data-testid="save-email-config-btn"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Settings className="w-4 h-4 mr-2" />
              )}
              Guardar Configuración
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailConfig;
