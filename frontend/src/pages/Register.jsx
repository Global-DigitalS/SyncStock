import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Package, Mail, Lock, User, Building2, ArrowRight, Eye, EyeOff, Check, Crown, Sparkles } from "lucide-react";
import axios from "axios";
import { sanitizeEmail, sanitizeString } from "../utils/sanitizer";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Register = () => {
  const [step, setStep] = useState(1); // 1: Select plan, 2: Register form
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    company: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [brandingLoaded, setBrandingLoaded] = useState(false);
  const [branding, setBranding] = useState({
    app_name: "StockHub",
    app_slogan: "Gestión de Catálogos",
    logo_url: null,
    primary_color: "#4f46e5",
    hero_image_url: null,
    hero_title: "Comienza a optimizar tu negocio",
    hero_subtitle: "Únete a cientos de tiendas que ya gestionan sus catálogos de forma eficiente.",
    page_title: "StockHub - Gestión de Catálogos"
  });
  const { register, user } = useAuth();
  const navigate = useNavigate();

  // Load branding and plans on mount
  useEffect(() => {
    const loadBranding = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/branding/public`);
        if (res.data) {
          setBranding(prev => ({ ...prev, ...res.data }));
          if (res.data.page_title) {
            document.title = res.data.page_title;
          }
        }
      } catch (error) {
        console.log("Using default branding");
      } finally {
        setBrandingLoaded(true);
      }
    };
    
    const loadPlans = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/subscriptions/plans/public`);
        setPlans(res.data || []);
        // Auto-select free plan
        const freePlan = res.data?.find(p => p.price_monthly === 0);
        if (freePlan) {
          setSelectedPlan(freePlan);
        }
      } catch (error) {
        console.error("Error loading plans:", error);
      } finally {
        setLoadingPlans(false);
      }
    };
    
    loadBranding();
    loadPlans();
  }, []);

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
        name: sanitizeString(formData.name),
        email: sanitizeEmail(formData.email),
        password: formData.password,
        company: formData.company ? sanitizeString(formData.company) : null,
        plan_id: selectedPlan?.id || null
      });
      
      if (selectedPlan?.trial_days > 0) {
        toast.success(`¡Cuenta creada! Disfruta de ${selectedPlan.trial_days} días de prueba premium`);
      } else {
        toast.success("Cuenta creada exitosamente");
      }
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear la cuenta");
    } finally {
      setLoading(false);
    }
  };

  const heroImageUrl = branding.hero_image_url 
    ? (branding.hero_image_url.startsWith('/') ? `${BACKEND_URL}${branding.hero_image_url}` : branding.hero_image_url)
    : 'https://images.unsplash.com/photo-1557447733-6db6888dd2d2?crop=entropy&cs=srgb&fm=jpg&q=85';

  if (!brandingLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  // Step 1: Plan Selection
  const renderPlanSelection = () => (
    <div className="w-full max-w-4xl animate-fade-in">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
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

      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Elige tu plan
        </h2>
        <p className="text-slate-500">
          Selecciona el plan que mejor se adapte a tus necesidades
        </p>
      </div>

      {loadingPlans ? (
        <div className="flex justify-center py-12">
          <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {plans.map((plan) => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlan(plan)}
              className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all ${
                selectedPlan?.id === plan.id
                  ? 'border-indigo-500 bg-indigo-50 shadow-lg'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
              data-testid={`plan-${plan.name.toLowerCase()}`}
            >
              {plan.trial_days > 0 && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-amber-500 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    {plan.trial_days} días gratis
                  </span>
                </div>
              )}
              
              {plan.name === "Professional" && (
                <div className="absolute -top-3 right-3">
                  <span className="bg-indigo-600 text-white text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1">
                    <Crown className="w-3 h-3" />
                    Popular
                  </span>
                </div>
              )}

              <div className="mb-4">
                <h3 className="font-bold text-lg text-slate-900">{plan.name}</h3>
                <p className="text-sm text-slate-500">{plan.description}</p>
              </div>

              <div className="mb-4">
                <span className="text-3xl font-bold text-slate-900">
                  {plan.price_monthly === 0 ? 'Gratis' : `€${plan.price_monthly}`}
                </span>
                {plan.price_monthly > 0 && (
                  <span className="text-slate-500 text-sm">/mes</span>
                )}
              </div>

              <ul className="space-y-2 mb-4">
                {plan.features?.slice(0, 4).map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm text-slate-600">
                    <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              {selectedPlan?.id === plan.id && (
                <div className="absolute top-3 right-3">
                  <div className="w-6 h-6 bg-indigo-500 rounded-full flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center">
        <p className="text-slate-500">
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors">
            Inicia Sesión
          </Link>
        </p>
        <Button
          onClick={() => setStep(2)}
          disabled={!selectedPlan}
          className="btn-primary px-8"
          data-testid="continue-to-register"
        >
          Continuar
          <ArrowRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
        </Button>
      </div>
    </div>
  );

  // Step 2: Registration Form
  const renderRegistrationForm = () => (
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

      {/* Selected Plan Badge */}
      {selectedPlan && (
        <div className="mb-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-indigo-600 font-medium">Plan seleccionado</p>
              <p className="text-lg font-bold text-slate-900">{selectedPlan.name}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setStep(1)}
              className="text-indigo-600 hover:text-indigo-700"
            >
              Cambiar
            </Button>
          </div>
          {selectedPlan.trial_days > 0 && (
            <p className="text-sm text-amber-600 mt-2 flex items-center gap-1">
              <Sparkles className="w-4 h-4" />
              Incluye {selectedPlan.trial_days} días de prueba premium
            </p>
          )}
        </div>
      )}

      {/* Form */}
      <div className="mb-6">
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
                type={showPassword ? "text" : "password"}
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="pl-10 pr-10 h-12 input-base"
                data-testid="register-password"
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

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-slate-700 font-medium">
              Confirmar *
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" strokeWidth={1.5} />
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type={showPassword ? "text" : "password"}
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
  );

  return (
    <div className="auth-container">
      {/* Left Side - Form */}
      <div className={`auth-left ${step === 1 ? 'lg:w-3/4' : ''}`}>
        {step === 1 ? renderPlanSelection() : renderRegistrationForm()}
      </div>

      {/* Right Side - Image (only show on step 2) */}
      {step === 2 && (
        <div 
          className="auth-right"
          style={{ backgroundImage: `url('${heroImageUrl}')` }}
        >
          <div className="absolute inset-0 flex items-center justify-center p-12">
            <div className="text-center text-white max-w-lg animate-slide-up">
              <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {branding.hero_title || "Comienza a optimizar tu negocio"}
              </h2>
              <p className="text-lg text-white/80">
                {branding.hero_subtitle || "Únete a cientos de tiendas que ya gestionan sus catálogos de forma eficiente."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Register;
