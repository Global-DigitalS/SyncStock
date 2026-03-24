import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Package, Mail, Lock, ArrowRight, Eye, EyeOff, AlertCircle, UserPlus, KeyRound } from "lucide-react";
import { sanitizeEmail } from "../utils/sanitizer";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorType, setErrorType] = useState(null);
  const [brandingLoaded, setBrandingLoaded] = useState(false);
  const [branding, setBranding] = useState({
    app_name: "StockHub",
    app_slogan: "Gestión de Catálogos",
    logo_url: null,
    primary_color: "#4f46e5",
    hero_image_url: null,
    hero_title: "Gestiona tu inventario de forma inteligente",
    hero_subtitle: "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos.",
    page_title: "StockHub - Gestión de Catálogos"
  });
  const { login, user } = useAuth();
  const navigate = useNavigate();

  // Load branding on mount
  useEffect(() => {
    const loadBranding = async () => {
      try {
        const res = await api.get("/branding/public");
        if (res.data) {
          setBranding(prev => ({ ...prev, ...res.data }));
          // Update page title
          if (res.data.page_title) {
            document.title = res.data.page_title;
          }
        }
      } catch (error) {
        // use default branding if load fails
      }
    };
    loadBranding();
  }, []);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate("/");
    }
  }, [user, navigate]);

  if (user) {
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorType(null);
    
    if (!email || !password) {
      toast.error("Por favor complete todos los campos");
      return;
    }

    // Sanitize email before sending
    const sanitizedEmail = sanitizeEmail(email);

    setLoading(true);
    try {
      await login(sanitizedEmail, password);
      toast.success("Bienvenido de vuelta");
      navigate("/");
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail === "USER_NOT_FOUND") {
        setErrorType("USER_NOT_FOUND");
      } else if (detail === "INVALID_PASSWORD") {
        setErrorType("INVALID_PASSWORD");
      } else if (detail === "ACCOUNT_DISABLED") {
        toast.error("Tu cuenta ha sido desactivada. Contacta al administrador.");
      } else {
        toast.error("Error al iniciar sesión");
      }
    } finally {
      setLoading(false);
    }
  };

  // Determine hero image URL
  const heroImageUrl = branding.hero_image_url 
    ? (branding.hero_image_url.startsWith('/') ? `${BACKEND_URL}${branding.hero_image_url}` : branding.hero_image_url)
    : 'https://images.unsplash.com/photo-1557447733-6db6888dd2d2?crop=entropy&cs=srgb&fm=jpg&q=85';

  // Render with default branding while loading from server
  // No need to wait — defaults are already set in state

  return (
    <div className="auth-container">
      {/* Left Side - Form */}
      <div className="auth-left">
        <div className="w-full max-w-md animate-fade-in">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            {branding.logo_url ? (
              <img 
                src={branding.logo_url.startsWith('/') ? `${BACKEND_URL}${branding.logo_url}` : branding.logo_url}
                alt={branding.app_name}
                className="h-12 object-contain"
              />
            ) : (
              <div 
                className="w-12 h-12 rounded-sm flex items-center justify-center"
                style={{ backgroundColor: branding.primary_color }}
              >
                <Package className="w-7 h-7 text-white" strokeWidth={1.5} />
              </div>
            )}
            <div>
              <h1 className="font-bold text-2xl text-slate-900 tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {branding.app_name}
              </h1>
              <p className="text-sm text-slate-500">{branding.app_slogan}</p>
            </div>
          </div>

          {/* Form */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Iniciar Sesión
            </h2>
            <p className="text-slate-500">
              Ingresa tus credenciales para acceder a tu cuenta
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-700 font-medium">
                Correo electrónico
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
                  className="pl-10 h-12 input-base"
                  data-testid="login-email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-slate-700 font-medium">
                  Contraseña
                </Label>
                <Link to="/forgot-password" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 pr-10 h-12 input-base"
                  data-testid="login-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  data-testid="toggle-password"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" strokeWidth={1.5} />
                  ) : (
                    <Eye className="w-5 h-5" strokeWidth={1.5} />
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 btn-primary text-base"
              data-testid="login-submit"
            >
              {loading ? (
                <div className="spinner w-5 h-5 border-2 border-white/30 border-t-white" />
              ) : (
                <>
                  Iniciar Sesión
                  <ArrowRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
                </>
              )}
            </Button>

            {/* Error Messages with Suggestions */}
            {errorType === "USER_NOT_FOUND" && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg animate-fade-in" data-testid="user-not-found-error">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-amber-800">No encontramos una cuenta con este correo</p>
                    <p className="text-sm text-amber-700 mt-1">¿Qué deseas hacer?</p>
                    <div className="flex flex-col sm:flex-row gap-2 mt-3">
                      <Link 
                        to="/register" 
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
                      >
                        <UserPlus className="w-4 h-4" />
                        Crear una cuenta
                      </Link>
                      <button 
                        type="button"
                        onClick={() => setErrorType(null)}
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors"
                      >
                        Verificar el correo
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {errorType === "INVALID_PASSWORD" && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg animate-fade-in" data-testid="invalid-password-error">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-rose-800">Contraseña incorrecta</p>
                    <p className="text-sm text-rose-700 mt-1">La contraseña que ingresaste no es correcta.</p>
                    <div className="flex flex-col sm:flex-row gap-2 mt-3">
                      <Link 
                        to="/forgot-password" 
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
                      >
                        <KeyRound className="w-4 h-4" />
                        Recuperar contraseña
                      </Link>
                      <button 
                        type="button"
                        onClick={() => setErrorType(null)}
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors"
                      >
                        Intentar de nuevo
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </form>

          <p className="mt-8 text-center text-slate-500">
            ¿No tienes cuenta?{" "}
            <Link to="/register" className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors">
              Regístrate
            </Link>
          </p>
        </div>
      </div>

      {/* Right Side - Image */}
      <div 
        className="auth-right"
        style={{ backgroundImage: `url('${heroImageUrl}')` }}
      >
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="text-center text-white max-w-lg animate-slide-up">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {branding.hero_title}
            </h2>
            <p className="text-lg text-white/80">
              {branding.hero_subtitle}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
