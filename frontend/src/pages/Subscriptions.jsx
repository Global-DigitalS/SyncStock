import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import {
  Check, Zap, Crown, Building2, Rocket, CreditCard, 
  Truck, BookOpen, ShoppingCart, Sparkles
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";

const PLAN_ICONS = {
  "Free": Zap,
  "Starter": Rocket,
  "Professional": Crown,
  "Enterprise": Building2
};

const PLAN_COLORS = {
  "Free": "border-slate-200 bg-slate-50",
  "Starter": "border-blue-200 bg-blue-50",
  "Professional": "border-indigo-300 bg-indigo-50 ring-2 ring-indigo-500",
  "Enterprise": "border-purple-200 bg-purple-50"
};

const Subscriptions = () => {
  const { user } = useContext(AuthContext);
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [yearlyBilling, setYearlyBilling] = useState(false);
  const [subscribing, setSubscribing] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [plansRes, subRes] = await Promise.all([
        api.get("/subscriptions/plans"),
        api.get("/subscriptions/my")
      ]);
      setPlans(plansRes.data);
      setCurrentSubscription(subRes.data);
    } catch (error) {
      toast.error("Error al cargar planes");
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan) => {
    if (currentSubscription?.plan?.name === plan.name && !currentSubscription?.is_free) {
      toast.info("Ya estás suscrito a este plan");
      return;
    }
    setConfirmDialog(plan);
  };

  const confirmSubscription = async () => {
    if (!confirmDialog) return;
    setSubscribing(true);
    try {
      const billingCycle = yearlyBilling ? "yearly" : "monthly";
      await api.post(`/subscriptions/subscribe/${confirmDialog.id}?billing_cycle=${billingCycle}`);
      toast.success(`¡Suscrito al plan ${confirmDialog.name} exitosamente!`);
      setConfirmDialog(null);
      fetchData();
      // Refresh page to update user limits
      window.location.reload();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al suscribirse");
    } finally {
      setSubscribing(false);
    }
  };

  const handleCancel = async () => {
    try {
      await api.post("/subscriptions/cancel");
      toast.success("Suscripción cancelada");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cancelar");
    }
  };

  const formatPrice = (plan) => {
    const price = yearlyBilling ? plan.price_yearly : plan.price_monthly;
    if (price === 0) return "Gratis";
    return `€${price.toFixed(2)}/${yearlyBilling ? "año" : "mes"}`;
  };

  const getSavings = (plan) => {
    if (plan.price_monthly === 0) return null;
    const yearlySavings = (plan.price_monthly * 12) - plan.price_yearly;
    if (yearlySavings <= 0) return null;
    return Math.round((yearlySavings / (plan.price_monthly * 12)) * 100);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  const currentPlanName = currentSubscription?.plan?.name || "Free";

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="subscriptions-title">
          Planes de Suscripción
        </h1>
        <p className="text-slate-500 max-w-2xl mx-auto">
          Elige el plan que mejor se adapte a tu negocio. Actualiza o cancela cuando quieras.
        </p>
      </div>

      {/* Current Plan Badge */}
      {currentSubscription && !currentSubscription.is_free && (
        <div className="mb-6 flex justify-center">
          <Badge className="bg-indigo-100 text-indigo-700 px-4 py-2 text-sm">
            <Crown className="w-4 h-4 mr-2" />
            Plan actual: {currentPlanName}
          </Badge>
        </div>
      )}

      {/* Billing Toggle */}
      <div className="flex items-center justify-center gap-3 mb-8">
        <Label htmlFor="billing-toggle" className={`text-sm ${!yearlyBilling ? "font-semibold text-slate-900" : "text-slate-500"}`}>
          Mensual
        </Label>
        <Switch
          id="billing-toggle"
          checked={yearlyBilling}
          onCheckedChange={setYearlyBilling}
          data-testid="billing-toggle"
        />
        <Label htmlFor="billing-toggle" className={`text-sm ${yearlyBilling ? "font-semibold text-slate-900" : "text-slate-500"}`}>
          Anual
        </Label>
        {yearlyBilling && (
          <Badge className="bg-emerald-100 text-emerald-700 ml-2">
            <Sparkles className="w-3 h-3 mr-1" />
            Ahorra hasta 17%
          </Badge>
        )}
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {plans.map((plan) => {
          const Icon = PLAN_ICONS[plan.name] || Zap;
          const isCurrentPlan = currentPlanName === plan.name;
          const savings = getSavings(plan);
          const colorClass = PLAN_COLORS[plan.name] || "border-slate-200";
          const isPopular = plan.name === "Professional";

          return (
            <Card 
              key={plan.id} 
              className={`relative ${colorClass} transition-all duration-300 hover:shadow-lg ${isPopular ? "scale-105 shadow-lg" : ""}`}
              data-testid={`plan-${plan.name.toLowerCase()}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-indigo-600 text-white px-3 py-1">
                    Más Popular
                  </Badge>
                </div>
              )}
              
              <CardHeader className="text-center pb-2">
                <div className={`w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center ${
                  plan.name === "Free" ? "bg-slate-200" :
                  plan.name === "Starter" ? "bg-blue-200" :
                  plan.name === "Professional" ? "bg-indigo-200" :
                  "bg-purple-200"
                }`}>
                  <Icon className={`w-6 h-6 ${
                    plan.name === "Free" ? "text-slate-600" :
                    plan.name === "Starter" ? "text-blue-600" :
                    plan.name === "Professional" ? "text-indigo-600" :
                    "text-purple-600"
                  }`} />
                </div>
                <CardTitle className="text-xl" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  {plan.name}
                </CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="text-center">
                <div className="mb-4">
                  <span className="text-3xl font-bold text-slate-900">{formatPrice(plan)}</span>
                  {yearlyBilling && savings && (
                    <div className="text-sm text-emerald-600 font-medium mt-1">
                      Ahorras {savings}%
                    </div>
                  )}
                </div>

                {/* Limits */}
                <div className="space-y-2 mb-4 text-sm">
                  <div className="flex items-center justify-between px-3 py-2 bg-white/50 rounded-lg">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Truck className="w-4 h-4" />
                      Proveedores
                    </div>
                    <span className="font-semibold text-slate-900">
                      {plan.max_suppliers >= 999999 ? "∞" : plan.max_suppliers}
                    </span>
                  </div>
                  <div className="flex items-center justify-between px-3 py-2 bg-white/50 rounded-lg">
                    <div className="flex items-center gap-2 text-slate-600">
                      <BookOpen className="w-4 h-4" />
                      Catálogos
                    </div>
                    <span className="font-semibold text-slate-900">
                      {plan.max_catalogs >= 999999 ? "∞" : plan.max_catalogs}
                    </span>
                  </div>
                  <div className="flex items-center justify-between px-3 py-2 bg-white/50 rounded-lg">
                    <div className="flex items-center gap-2 text-slate-600">
                      <ShoppingCart className="w-4 h-4" />
                      Tiendas WC
                    </div>
                    <span className="font-semibold text-slate-900">
                      {plan.max_woocommerce_stores >= 999999 ? "∞" : plan.max_woocommerce_stores}
                    </span>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-2 text-left mb-4">
                  {plan.features.slice(0, 4).map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-slate-600">
                      <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      {feature}
                    </div>
                  ))}
                </div>
              </CardContent>

              <CardFooter>
                <Button
                  className={`w-full ${
                    isCurrentPlan 
                      ? "bg-slate-200 text-slate-600 hover:bg-slate-300" 
                      : plan.name === "Professional" 
                        ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                        : "btn-primary"
                  }`}
                  onClick={() => handleSubscribe(plan)}
                  disabled={isCurrentPlan}
                  data-testid={`subscribe-${plan.name.toLowerCase()}`}
                >
                  {isCurrentPlan ? (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Plan Actual
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-4 h-4 mr-2" />
                      {plan.price_monthly === 0 ? "Comenzar Gratis" : "Suscribirse"}
                    </>
                  )}
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* Cancel Subscription */}
      {currentSubscription && !currentSubscription.is_free && (
        <div className="mt-8 text-center">
          <Button variant="ghost" className="text-slate-500 hover:text-rose-600" onClick={handleCancel}>
            Cancelar suscripción
          </Button>
        </div>
      )}

      {/* Confirmation Dialog */}
      <Dialog open={!!confirmDialog} onOpenChange={() => setConfirmDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Confirmar Suscripción
            </DialogTitle>
            <DialogDescription>
              ¿Deseas suscribirte al plan {confirmDialog?.name}?
            </DialogDescription>
          </DialogHeader>
          
          {confirmDialog && (
            <div className="py-4">
              <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-600">Plan:</span>
                  <span className="font-semibold">{confirmDialog.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Ciclo:</span>
                  <span className="font-semibold">{yearlyBilling ? "Anual" : "Mensual"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Precio:</span>
                  <span className="font-semibold text-indigo-600">
                    €{(yearlyBilling ? confirmDialog.price_yearly : confirmDialog.price_monthly).toFixed(2)}
                  </span>
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-3">
                Nota: Esta es una demostración. En producción, se integraría con Stripe para procesar pagos reales.
              </p>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDialog(null)}>
              Cancelar
            </Button>
            <Button 
              className="btn-primary" 
              onClick={confirmSubscription}
              disabled={subscribing}
            >
              {subscribing ? "Procesando..." : "Confirmar Suscripción"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Subscriptions;
