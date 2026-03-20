import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import {
  Database,
  Server,
  User,
  Lock,
  Building2,
  Mail,
  CheckCircle,
  XCircle,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  Shield,
  Zap,
  HelpCircle,
  Key,
  Globe,
  Settings,
  Eye,
  EyeOff,
  Copy,
  Check,
  Send
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Setup = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showJwtSecret, setShowJwtSecret] = useState(false);
  const [useCustomJwt, setUseCustomJwt] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const [formData, setFormData] = useState({
    // Paso 1: Configuración de la aplicación
    mongo_url: "",
    db_name: "syncstock_db",
    jwt_secret: "",
    cors_origins: "*",
    // Paso 2: SuperAdmin
    admin_email: "",
    admin_password: "",
    admin_password_confirm: "",
    admin_name: "",
    company: "",
    // Paso 3: SMTP (Opcional)
    smtp_host: "",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
    smtp_from_email: "",
    smtp_from_name: "SyncStock",
    smtp_use_tls: true,
    smtp_use_ssl: false
  });
  
  const [smtpTestResult, setSmtpTestResult] = useState(null);
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [skipSmtp, setSkipSmtp] = useState(false);

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const res = await axios.get(`${API}/setup/status`);
      if (res.data.is_configured) {
        navigate("/login");
      } else if (res.data.has_database && !res.data.has_superadmin) {
        setStep(2);
      }
      // Pre-fill CORS if available
      if (res.data.current_cors) {
        setFormData(prev => ({ ...prev, cors_origins: res.data.current_cors }));
      }
    } catch (error) {
      // setup status check failed
    } finally {
      setLoading(false);
    }
  };

  const generateJwtSecret = () => {
    // Generar un JWT secret seguro en el cliente
    const array = new Uint8Array(48);
    crypto.getRandomValues(array);
    const secret = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    setFormData({ ...formData, jwt_secret: secret });
    setUseCustomJwt(true);
    toast.success("JWT Secret generado");
  };

  const copyJwtSecret = () => {
    navigator.clipboard.writeText(formData.jwt_secret);
    setCopied(true);
    toast.success("Copiado al portapapeles");
    setTimeout(() => setCopied(false), 2000);
  };

  const testConnection = async () => {
    if (!formData.mongo_url) {
      toast.error("Introduce la URL de MongoDB");
      return;
    }

    setTesting(true);
    setConnectionStatus(null);

    try {
      const res = await axios.post(`${API}/setup/test-connection`, {
        mongo_url: formData.mongo_url,
        db_name: formData.db_name
      });

      if (res.data.success) {
        setConnectionStatus({
          success: true,
          message: res.data.message,
          database: res.data.database,
          hasData: res.data.has_data
        });
        toast.success("Conexión exitosa");
      } else {
        setConnectionStatus({
          success: false,
          message: res.data.message
        });
        toast.error(res.data.message);
      }
    } catch (error) {
      setConnectionStatus({
        success: false,
        message: error.response?.data?.message || "Error de conexión"
      });
      toast.error("Error al probar la conexión");
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (step === 1) {
      if (!connectionStatus?.success) {
        toast.error("Primero prueba la conexión a MongoDB");
        return;
      }
      setStep(2);
      return;
    }

    if (step === 2) {
      // Validaciones del paso 2
      if (!formData.admin_name.trim()) {
        toast.error("El nombre es obligatorio");
        return;
      }
      if (!formData.admin_email.trim()) {
        toast.error("El email es obligatorio");
        return;
      }
      if (formData.admin_password.length < 6) {
        toast.error("La contraseña debe tener al menos 6 caracteres");
        return;
      }
      if (formData.admin_password !== formData.admin_password_confirm) {
        toast.error("Las contraseñas no coinciden");
        return;
      }
      setStep(3);
      return;
    }

    // Paso 3: Configuración final
    setSubmitting(true);

    try {
      const payload = {
        mongo_url: formData.mongo_url,
        db_name: formData.db_name,
        jwt_secret: formData.jwt_secret,
        cors_origins: formData.cors_origins,
        admin_email: formData.admin_email,
        admin_password: formData.admin_password,
        admin_name: formData.admin_name,
        company: formData.company
      };
      
      // Incluir SMTP solo si no se salta
      if (!skipSmtp && formData.smtp_host) {
        payload.smtp_host = formData.smtp_host;
        payload.smtp_port = formData.smtp_port;
        payload.smtp_user = formData.smtp_user;
        payload.smtp_password = formData.smtp_password;
        payload.smtp_from_email = formData.smtp_from_email || formData.smtp_user;
        payload.smtp_from_name = formData.smtp_from_name;
        payload.smtp_use_tls = formData.smtp_use_tls;
        payload.smtp_use_ssl = formData.smtp_use_ssl;
      }
      
      const res = await axios.post(`${API}/setup/configure`, payload);

      if (res.data.success) {
        toast.success("¡Configuración completada!");
        
        // Guardar token y usuario
        localStorage.setItem("token", res.data.token);
        localStorage.setItem("user", JSON.stringify(res.data.user));
        
        // Si requiere reinicio, mostrar mensaje y esperar
        if (res.data.requires_restart) {
          toast.info("El servidor se está reiniciando. Espera unos segundos...", { duration: 5000 });
          
          // Esperar a que el servidor se reinicie y luego redirigir
          setTimeout(async () => {
            // Intentar verificar que el servidor está listo
            let attempts = 0;
            const maxAttempts = 10;
            
            const checkServer = async () => {
              try {
                await axios.get(`${API}/health`, { timeout: 2000 });
                window.location.href = "/#/";
              } catch (e) {
                attempts++;
                if (attempts < maxAttempts) {
                  setTimeout(checkServer, 1000);
                } else {
                  // Redirigir de todos modos después de varios intentos
                  window.location.href = "/#/";
                }
              }
            };
            
            checkServer();
          }, 3000);
        } else {
          // Redirigir al dashboard
          setTimeout(() => {
            window.location.href = "/#/";
          }, 1000);
        }
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.message || "Error en la configuración");
    } finally {
      setSubmitting(false);
    }
  };
  
  const testSmtpConnection = async () => {
    if (!formData.smtp_host || !formData.smtp_user || !formData.smtp_password) {
      toast.error("Completa los campos obligatorios de SMTP");
      return;
    }
    
    setTestingSmtp(true);
    setSmtpTestResult(null);
    
    try {
      const res = await axios.post(`${API}/email/test-connection`, {
        smtp_host: formData.smtp_host,
        smtp_port: formData.smtp_port,
        smtp_user: formData.smtp_user,
        smtp_password: formData.smtp_password,
        smtp_use_tls: formData.smtp_use_tls,
        smtp_use_ssl: formData.smtp_use_ssl
      });
      
      setSmtpTestResult(res.data);
      
      if (res.data.success) {
        toast.success("Conexión SMTP exitosa");
      } else {
        toast.error(res.data.message || "Error de conexión");
      }
    } catch (error) {
      setSmtpTestResult({ success: false, message: error.response?.data?.message || "Error de conexión" });
      toast.error("Error al probar la conexión SMTP");
    } finally {
      setTestingSmtp(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Logo y título */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            SyncStock
          </h1>
          <p className="text-slate-400">Configuración inicial de la aplicación</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 ${step >= 1 ? "text-indigo-400" : "text-slate-600"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step >= 1 ? "bg-indigo-600 text-white" : "bg-slate-700 text-slate-400"
              }`}>
                1
              </div>
              <span className="text-sm font-medium hidden sm:inline">Configuración</span>
            </div>
            <div className={`w-8 sm:w-12 h-0.5 ${step >= 2 ? "bg-indigo-500" : "bg-slate-700"}`} />
            <div className={`flex items-center gap-2 ${step >= 2 ? "text-indigo-400" : "text-slate-600"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step >= 2 ? "bg-indigo-600 text-white" : "bg-slate-700 text-slate-400"
              }`}>
                2
              </div>
              <span className="text-sm font-medium hidden sm:inline">SuperAdmin</span>
            </div>
            <div className={`w-8 sm:w-12 h-0.5 ${step >= 3 ? "bg-indigo-500" : "bg-slate-700"}`} />
            <div className={`flex items-center gap-2 ${step >= 3 ? "text-indigo-400" : "text-slate-600"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step >= 3 ? "bg-indigo-600 text-white" : "bg-slate-700 text-slate-400"
              }`}>
                3
              </div>
              <span className="text-sm font-medium hidden sm:inline">Email</span>
            </div>
          </div>
        </div>

        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {step === 1 ? (
                <>
                  <Settings className="w-5 h-5 text-indigo-400" />
                  Configuración del Sistema
                </>
              ) : step === 2 ? (
                <>
                  <Shield className="w-5 h-5 text-indigo-400" />
                  Crear SuperAdmin
                </>
              ) : (
                <>
                  <Mail className="w-5 h-5 text-indigo-400" />
                  Configuración de Email
                </>
              )}
            </CardTitle>
            <CardDescription className="text-slate-400">
              {step === 1 
                ? "Configura la base de datos y seguridad de la aplicación" 
                : step === 2
                  ? "Crea el usuario administrador principal"
                  : "Configura el envío de emails (opcional)"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {step === 1 ? (
                <>
                  {/* MongoDB URL */}
                  <div className="space-y-2">
                    <Label className="text-slate-300">URL de MongoDB *</Label>
                    <div className="relative">
                      <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="text"
                        value={formData.mongo_url}
                        onChange={(e) => setFormData({ ...formData, mongo_url: e.target.value })}
                        placeholder="mongodb://usuario:contraseña@host:27017"
                        className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 font-mono text-sm"
                        data-testid="mongo-url-input"
                      />
                    </div>
                    <p className="text-xs text-slate-500">
                      Formato: mongodb://[usuario:contraseña@]host:puerto o mongodb+srv://...
                    </p>
                  </div>

                  {/* Database Name */}
                  <div className="space-y-2">
                    <Label className="text-slate-300">Nombre de la base de datos</Label>
                    <div className="relative">
                      <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="text"
                        value={formData.db_name}
                        onChange={(e) => setFormData({ ...formData, db_name: e.target.value })}
                        placeholder="syncstock_db"
                        className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                        data-testid="db-name-input"
                      />
                    </div>
                  </div>

                  {/* Test Connection Button */}
                  <Button
                    type="button"
                    onClick={testConnection}
                    disabled={testing || !formData.mongo_url}
                    className="w-full bg-slate-700 hover:bg-slate-600 text-white"
                    data-testid="test-connection-btn"
                  >
                    {testing ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Database className="w-4 h-4 mr-2" />
                    )}
                    Probar Conexión
                  </Button>

                  {/* Connection Status */}
                  {connectionStatus && (
                    <div className={`p-4 rounded-lg border ${
                      connectionStatus.success 
                        ? "bg-emerald-900/20 border-emerald-700" 
                        : "bg-rose-900/20 border-rose-700"
                    }`}>
                      <div className="flex items-start gap-3">
                        {connectionStatus.success ? (
                          <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                          <p className={`font-medium ${connectionStatus.success ? "text-emerald-300" : "text-rose-300"}`}>
                            {connectionStatus.success ? "Conexión exitosa" : "Error de conexión"}
                          </p>
                          <p className="text-sm text-slate-400 mt-1">{connectionStatus.message}</p>
                          {connectionStatus.success && connectionStatus.database && (
                            <p className="text-xs text-slate-500 mt-2">
                              Base de datos: {connectionStatus.database}
                              {connectionStatus.hasData && " (contiene datos existentes)"}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Divider */}
                  {connectionStatus?.success && (
                    <>
                      <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                          <div className="w-full border-t border-slate-700"></div>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                          <span className="bg-slate-800 px-2 text-slate-500">Seguridad (Opcional)</span>
                        </div>
                      </div>

                      {/* JWT Secret */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label className="text-slate-300">JWT Secret</Label>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">Personalizado</span>
                            <Switch
                              checked={useCustomJwt}
                              onCheckedChange={setUseCustomJwt}
                            />
                          </div>
                        </div>
                        {useCustomJwt ? (
                          <div className="space-y-2">
                            <div className="relative">
                              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                              <Input
                                type={showJwtSecret ? "text" : "password"}
                                value={formData.jwt_secret}
                                onChange={(e) => setFormData({ ...formData, jwt_secret: e.target.value })}
                                placeholder="Tu JWT secret personalizado"
                                className="pl-10 pr-20 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 font-mono text-sm"
                                data-testid="jwt-secret-input"
                              />
                              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                                  onClick={() => setShowJwtSecret(!showJwtSecret)}
                                >
                                  {showJwtSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </Button>
                                {formData.jwt_secret && (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                                    onClick={copyJwtSecret}
                                  >
                                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                                  </Button>
                                )}
                              </div>
                            </div>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={generateJwtSecret}
                              className="border-slate-600 text-slate-300 hover:bg-slate-700"
                            >
                              <Key className="w-3.5 h-3.5 mr-1.5" />
                              Generar Secret Seguro
                            </Button>
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500 bg-slate-900/30 p-3 rounded-lg">
                            Se generará automáticamente un JWT secret seguro. Activa "Personalizado" si prefieres usar uno propio.
                          </p>
                        )}
                      </div>

                      {/* CORS Origins */}
                      <div className="space-y-2">
                        <Label className="text-slate-300">Orígenes CORS permitidos</Label>
                        <div className="relative">
                          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                          <Input
                            type="text"
                            value={formData.cors_origins}
                            onChange={(e) => setFormData({ ...formData, cors_origins: e.target.value })}
                            placeholder="https://tudominio.com"
                            className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                            data-testid="cors-input"
                          />
                        </div>
                        <p className="text-xs text-slate-500">
                          Usa * para permitir todos los orígenes (solo desarrollo) o especifica tu dominio para producción
                        </p>
                      </div>
                    </>
                  )}

                  {/* Help Section */}
                  <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700">
                    <div className="flex items-start gap-3">
                      <HelpCircle className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-slate-400">
                        <p className="font-medium text-slate-300 mb-2">¿Cómo obtener la URL de MongoDB?</p>
                        <ul className="space-y-1 text-xs">
                          <li>• <strong>MongoDB Atlas:</strong> Ve a Database → Connect → Drivers</li>
                          <li>• <strong>Local:</strong> mongodb://localhost:27017</li>
                          <li>• <strong>Con auth:</strong> mongodb://usuario:pass@host:27017</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Admin Name */}
                  <div className="space-y-2">
                    <Label className="text-slate-300">Nombre completo *</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="text"
                        value={formData.admin_name}
                        onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                        placeholder="Tu nombre"
                        className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                        data-testid="admin-name-input"
                      />
                    </div>
                  </div>

                  {/* Admin Email */}
                  <div className="space-y-2">
                    <Label className="text-slate-300">Email *</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="email"
                        value={formData.admin_email}
                        onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                        placeholder="admin@empresa.com"
                        className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                        data-testid="admin-email-input"
                      />
                    </div>
                  </div>

                  {/* Company */}
                  <div className="space-y-2">
                    <Label className="text-slate-300">Empresa (opcional)</Label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="text"
                        value={formData.company}
                        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                        placeholder="Nombre de tu empresa"
                        className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                        data-testid="admin-company-input"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Contraseña *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          type={showPassword ? "text" : "password"}
                          value={formData.admin_password}
                          onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                          placeholder="••••••••"
                          className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                          data-testid="admin-password-input"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Confirmar *</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          type={showPassword ? "text" : "password"}
                          value={formData.admin_password_confirm}
                          onChange={(e) => setFormData({ ...formData, admin_password_confirm: e.target.value })}
                          placeholder="••••••••"
                          className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                          data-testid="admin-password-confirm-input"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-slate-500">Mínimo 6 caracteres</p>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-xs text-indigo-400 hover:text-indigo-300"
                    >
                      {showPassword ? "Ocultar" : "Mostrar"} contraseñas
                    </button>
                  </div>

                  {/* Info Box */}
                  <div className="p-4 bg-indigo-900/20 rounded-lg border border-indigo-700">
                    <div className="flex items-start gap-3">
                      <Shield className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-slate-400">
                        <p className="font-medium text-indigo-300 mb-1">Cuenta SuperAdmin</p>
                        <p className="text-xs">
                          Esta cuenta tendrá acceso completo a todas las funcionalidades de la aplicación,
                          incluyendo la gestión de usuarios, planes y configuración del sistema.
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Step 3: SMTP Configuration */}
              {step === 3 && (
                <>
                  {/* Skip SMTP Option */}
                  <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-start gap-3">
                        <Mail className="w-5 h-5 text-slate-400 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-slate-300">Configuración de Email</p>
                          <p className="text-xs text-slate-500 mt-1">
                            Configura SMTP para enviar emails de bienvenida, recuperación de contraseña y notificaciones.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">Saltar</span>
                        <Switch
                          checked={skipSmtp}
                          onCheckedChange={setSkipSmtp}
                        />
                      </div>
                    </div>
                  </div>

                  {!skipSmtp && (
                    <>
                      {/* SMTP Host & Port */}
                      <div className="grid grid-cols-3 gap-4">
                        <div className="col-span-2 space-y-2">
                          <Label className="text-slate-300">Servidor SMTP *</Label>
                          <div className="relative">
                            <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <Input
                              type="text"
                              value={formData.smtp_host}
                              onChange={(e) => setFormData({ ...formData, smtp_host: e.target.value })}
                              placeholder="smtp.gmail.com"
                              className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 font-mono text-sm"
                              data-testid="smtp-host-input"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Puerto</Label>
                          <Input
                            type="number"
                            value={formData.smtp_port}
                            onChange={(e) => setFormData({ ...formData, smtp_port: parseInt(e.target.value) || 587 })}
                            placeholder="587"
                            className="bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 font-mono"
                            data-testid="smtp-port-input"
                          />
                        </div>
                      </div>

                      {/* SMTP Credentials */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Usuario SMTP *</Label>
                          <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <Input
                              type="text"
                              value={formData.smtp_user}
                              onChange={(e) => setFormData({ ...formData, smtp_user: e.target.value })}
                              placeholder="tu@email.com"
                              className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                              data-testid="smtp-user-input"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Contraseña SMTP *</Label>
                          <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <Input
                              type="password"
                              value={formData.smtp_password}
                              onChange={(e) => setFormData({ ...formData, smtp_password: e.target.value })}
                              placeholder="••••••••"
                              className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                              data-testid="smtp-password-input"
                            />
                          </div>
                        </div>
                      </div>

                      {/* From Email & Name */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-slate-300">Email remitente</Label>
                          <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <Input
                              type="email"
                              value={formData.smtp_from_email}
                              onChange={(e) => setFormData({ ...formData, smtp_from_email: e.target.value })}
                              placeholder="noreply@empresa.com"
                              className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                              data-testid="smtp-from-email-input"
                            />
                          </div>
                          <p className="text-xs text-slate-500">Dejar vacío para usar el usuario SMTP</p>
                        </div>
                        <div className="space-y-2">
                          <Label className="text-slate-300">Nombre remitente</Label>
                          <Input
                            type="text"
                            value={formData.smtp_from_name}
                            onChange={(e) => setFormData({ ...formData, smtp_from_name: e.target.value })}
                            placeholder="SyncStock"
                            className="bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                            data-testid="smtp-from-name-input"
                          />
                        </div>
                      </div>

                      {/* TLS/SSL Options */}
                      <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={formData.smtp_use_tls}
                            onCheckedChange={(checked) => setFormData({ 
                              ...formData, 
                              smtp_use_tls: checked,
                              smtp_use_ssl: checked ? false : formData.smtp_use_ssl
                            })}
                          />
                          <span className="text-sm text-slate-400">Usar TLS (STARTTLS)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={formData.smtp_use_ssl}
                            onCheckedChange={(checked) => setFormData({ 
                              ...formData, 
                              smtp_use_ssl: checked,
                              smtp_use_tls: checked ? false : formData.smtp_use_tls
                            })}
                          />
                          <span className="text-sm text-slate-400">Usar SSL</span>
                        </div>
                      </div>

                      {/* Test Connection Button */}
                      <Button
                        type="button"
                        variant="outline"
                        onClick={testSmtpConnection}
                        disabled={testingSmtp || !formData.smtp_host || !formData.smtp_user || !formData.smtp_password}
                        className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
                        data-testid="smtp-test-btn"
                      >
                        {testingSmtp ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4 mr-2" />
                        )}
                        Probar Conexión SMTP
                      </Button>

                      {/* SMTP Test Result */}
                      {smtpTestResult && (
                        <div className={`p-4 rounded-lg border ${
                          smtpTestResult.success 
                            ? "bg-emerald-900/20 border-emerald-700" 
                            : "bg-rose-900/20 border-rose-700"
                        }`}>
                          <div className="flex items-start gap-3">
                            {smtpTestResult.success ? (
                              <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <p className={`font-medium ${smtpTestResult.success ? "text-emerald-300" : "text-rose-300"}`}>
                                {smtpTestResult.success ? "Conexión SMTP exitosa" : "Error de conexión"}
                              </p>
                              <p className="text-sm text-slate-400 mt-1">{smtpTestResult.message}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* SMTP Help */}
                      <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700">
                        <div className="flex items-start gap-3">
                          <HelpCircle className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                          <div className="text-sm text-slate-400">
                            <p className="font-medium text-slate-300 mb-2">Configuraciones comunes</p>
                            <ul className="space-y-1 text-xs">
                              <li>• <strong>Gmail:</strong> smtp.gmail.com:587 (TLS) - Requiere "App Password"</li>
                              <li>• <strong>Outlook:</strong> smtp.office365.com:587 (TLS)</li>
                              <li>• <strong>Yahoo:</strong> smtp.mail.yahoo.com:465 (SSL)</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {skipSmtp && (
                    <div className="p-4 bg-amber-900/20 rounded-lg border border-amber-700">
                      <div className="flex items-start gap-3">
                        <Mail className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-slate-400">
                          <p className="font-medium text-amber-300 mb-1">Email desactivado</p>
                          <p className="text-xs">
                            No se enviarán emails de bienvenida ni de recuperación de contraseña.
                            Puedes configurar esto más tarde desde el panel de SuperAdmin.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Navigation Buttons */}
              <div className="flex items-center gap-3 pt-4">
                {(step === 2 || step === 3) && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(step - 1)}
                    className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Volver
                  </Button>
                )}
                <Button
                  type="submit"
                  disabled={submitting || (step === 1 && !connectionStatus?.success)}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white"
                  data-testid="setup-submit-btn"
                >
                  {submitting ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <ArrowRight className="w-4 h-4 mr-2" />
                  )}
                  {step === 1 ? "Continuar" : step === 2 ? "Continuar" : "Completar Configuración"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-6">
          SyncStock © 2026 - Gestión inteligente de proveedores
        </p>
      </div>
    </div>
  );
};

export default Setup;
