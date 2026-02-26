import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Package, Mail, Lock, User, Building2, ArrowRight, Eye, EyeOff } from "lucide-react";

const Register = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    company: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register, user } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  if (user) {
    navigate("/");
    return null;
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.password) {
      toast.error("Por favor complete los campos obligatorios");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }

    if (formData.password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }

    setLoading(true);
    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        company: formData.company || null
      });
      toast.success("Cuenta creada exitosamente");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear la cuenta");
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
              Crear Cuenta
            </h2>
            <p className="text-slate-500">
              Completa el formulario para comenzar
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-700 font-medium">
                Nombre completo *
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Tu nombre"
                  className="pl-10 h-12 input-base"
                  data-testid="register-name"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-700 font-medium">
                Correo electrónico *
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="tu@email.com"
                  className="pl-10 h-12 input-base"
                  data-testid="register-email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="company" className="text-slate-700 font-medium">
                Empresa (opcional)
              </Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                <Input
                  id="company"
                  name="company"
                  type="text"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="Nombre de tu empresa"
                  className="pl-10 h-12 input-base"
                  data-testid="register-company"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700 font-medium">
                  Contraseña *
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="pl-10 h-12 input-base"
                    data-testid="register-password"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-slate-700 font-medium">
                  Confirmar *
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="pl-10 h-12 input-base"
                    data-testid="register-confirm-password"
                  />
                </div>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 btn-primary text-base"
              data-testid="register-submit"
            >
              {loading ? (
                <div className="spinner w-5 h-5 border-2 border-white/30 border-t-white" />
              ) : (
                <>
                  Crear Cuenta
                  <ArrowRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
                </>
              )}
            </Button>
          </form>

          <p className="mt-8 text-center text-slate-500">
            ¿Ya tienes cuenta?{" "}
            <Link to="/login" className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors">
              Inicia Sesión
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
              Comienza a optimizar tu negocio
            </h2>
            <p className="text-lg text-white/80">
              Únete a cientos de tiendas que ya gestionan sus catálogos de forma eficiente.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
