import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
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
  Shield,
  Zap,
  HelpCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Setup = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  
  const [formData, setFormData] = useState({
    mongo_url: "",
    db_name: "supplier_sync_db",
    admin_email: "",
    admin_password: "",
    admin_password_confirm: "",
    admin_name: "",
    company: ""
  });

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
    } catch (error) {
      console.log("Setup status check failed:", error);
    } finally {
      setLoading(false);
    }
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

    setSubmitting(true);

    try {
      const res = await axios.post(`${API}/setup/configure`, {
        mongo_url: formData.mongo_url,
        db_name: formData.db_name,
        admin_email: formData.admin_email,
        admin_password: formData.admin_password,
        admin_name: formData.admin_name,
        company: formData.company
      });

      if (res.data.success) {
        toast.success("Configuración completada");
        
        // Guardar token y redirigir
        localStorage.setItem("token", res.data.token);
        localStorage.setItem("user", JSON.stringify(res.data.user));
        
        // Pequeño delay para que se guarde el token
        setTimeout(() => {
          window.location.href = "/";
        }, 500);
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.message || "Error en la configuración");
    } finally {
      setSubmitting(false);
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
            SupplierSync Pro
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
              <span className="text-sm font-medium">Base de datos</span>
            </div>
            <div className={`w-12 h-0.5 ${step >= 2 ? "bg-indigo-500" : "bg-slate-700"}`} />
            <div className={`flex items-center gap-2 ${step >= 2 ? "text-indigo-400" : "text-slate-600"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                step >= 2 ? "bg-indigo-600 text-white" : "bg-slate-700 text-slate-400"
              }`}>
                2
              </div>
              <span className="text-sm font-medium">SuperAdmin</span>
            </div>
          </div>
        </div>

        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {step === 1 ? (
                <>
                  <Database className="w-5 h-5 text-indigo-400" />
                  Conexión a MongoDB
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5 text-indigo-400" />
                  Crear SuperAdmin
                </>
              )}
            </CardTitle>
            <CardDescription className="text-slate-400">
              {step === 1 
                ? "Configura la conexión a tu base de datos MongoDB" 
                : "Crea el usuario administrador principal"
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
                      <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
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
                      <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <Input
                        type="text"
                        value={formData.db_name}
                        onChange={(e) => setFormData({ ...formData, db_name: e.target.value })}
                        placeholder="supplier_sync_db"
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
                      <Server className="w-4 h-4 mr-2" />
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
                          type="password"
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
                          type="password"
                          value={formData.admin_password_confirm}
                          onChange={(e) => setFormData({ ...formData, admin_password_confirm: e.target.value })}
                          placeholder="••••••••"
                          className="pl-10 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500"
                          data-testid="admin-password-confirm-input"
                        />
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">Mínimo 6 caracteres</p>

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

              {/* Navigation Buttons */}
              <div className="flex items-center gap-3 pt-4">
                {step === 2 && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(1)}
                    className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
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
                  {step === 1 ? "Continuar" : "Completar Configuración"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-6">
          SupplierSync Pro © 2026 - Gestión inteligente de proveedores
        </p>
      </div>
    </div>
  );
};

export default Setup;
