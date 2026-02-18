import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Package, Mail, Lock, ArrowRight } from "lucide-react";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  if (user) {
    navigate("/");
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Por favor complete todos los campos");
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      toast.success("Bienvenido de vuelta");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Left Side - Form */}
      <div className="auth-left">
        <div className="w-full max-w-md animate-fade-in">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-12 h-12 bg-indigo-600 rounded-sm flex items-center justify-center">
              <Package className="w-7 h-7 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <h1 className="font-bold text-2xl text-slate-900 tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
                StockHub
              </h1>
              <p className="text-sm text-slate-500">Gestión de Catálogos</p>
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
              <Label htmlFor="password" className="text-slate-700 font-medium">
                Contraseña
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 h-12 input-base"
                  data-testid="login-password"
                />
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
        style={{ backgroundImage: `url('https://images.unsplash.com/photo-1557447733-6db6888dd2d2?crop=entropy&cs=srgb&fm=jpg&q=85')` }}
      >
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="text-center text-white max-w-lg animate-slide-up">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Gestiona tu inventario de forma inteligente
            </h2>
            <p className="text-lg text-white/80">
              Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
