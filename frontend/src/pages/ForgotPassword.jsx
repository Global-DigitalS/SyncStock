import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Package, Mail, Lock, ArrowLeft, Send, CheckCircle, Eye, EyeOff } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ForgotPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  
  // State for forgot password form
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  
  // State for reset password form
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [resetting, setResetting] = useState(false);

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    
    if (!email) {
      toast.error("Introduce tu email");
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setEmailSent(true);
      toast.success("Si el email existe, recibirás un enlace");
    } catch (error) {
      toast.error("Error al procesar la solicitud");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    
    setResetting(true);
    
    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: newPassword
      });
      toast.success("Contraseña actualizada correctamente");
      navigate("/login");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Token inválido o expirado");
    } finally {
      setResetting(false);
    }
  };

  // Reset password form (when token is present)
  if (token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-3">
              <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center">
                <Package className="w-7 h-7 text-white" strokeWidth={1.5} />
              </div>
              <span className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
                SupplierSync
              </span>
            </Link>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Nueva contraseña
            </h2>
            <p className="text-slate-500 mb-6">
              Introduce tu nueva contraseña
            </p>

            <form onSubmit={handleResetPassword} className="space-y-5">
              <div className="space-y-2">
                <Label className="text-slate-700 font-medium">Nueva contraseña</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className="pl-10 pr-10 h-12 input-base"
                    data-testid="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-700 font-medium">Confirmar contraseña</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="pl-10 h-12 input-base"
                    data-testid="confirm-password"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={resetting}
                className="w-full h-12 btn-primary"
                data-testid="reset-password-btn"
              >
                {resetting ? "Actualizando..." : "Actualizar contraseña"}
              </Button>
            </form>
          </div>

          <p className="text-center mt-6 text-slate-500">
            <Link to="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
              <ArrowLeft className="w-4 h-4 inline mr-1" />
              Volver al login
            </Link>
          </p>
        </div>
      </div>
    );
  }

  // Forgot password form (request email)
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3">
            <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Package className="w-7 h-7 text-white" strokeWidth={1.5} />
            </div>
            <span className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
              SupplierSync
            </span>
          </Link>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
          {emailSent ? (
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Email enviado
              </h2>
              <p className="text-slate-500 mb-6">
                Si el email está registrado, recibirás un enlace para restablecer tu contraseña.
                Revisa también la carpeta de spam.
              </p>
              <Button
                onClick={() => { setEmailSent(false); setEmail(""); }}
                variant="outline"
                className="w-full"
              >
                Enviar a otro email
              </Button>
            </div>
          ) : (
            <>
              <h2 className="text-2xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                ¿Olvidaste tu contraseña?
              </h2>
              <p className="text-slate-500 mb-6">
                Introduce tu email y te enviaremos un enlace para restablecerla
              </p>

              <form onSubmit={handleForgotPassword} className="space-y-5">
                <div className="space-y-2">
                  <Label className="text-slate-700 font-medium">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="tu@email.com"
                      className="pl-10 h-12 input-base"
                      data-testid="forgot-email"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 btn-primary"
                  data-testid="send-reset-btn"
                >
                  {loading ? (
                    "Enviando..."
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Enviar enlace
                    </>
                  )}
                </Button>
              </form>
            </>
          )}
        </div>

        <p className="text-center mt-6 text-slate-500">
          <Link to="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
            <ArrowLeft className="w-4 h-4 inline mr-1" />
            Volver al login
          </Link>
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;
