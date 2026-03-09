import { useState, useEffect, useContext, useCallback } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import {
  Check, Zap, Crown, Building2, Rocket, CreditCard, 
  Truck, BookOpen, ShoppingCart, Sparkles, Settings, Plus, Trash2, X,
  Loader2, ExternalLink, AlertCircle, CalendarDays
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";
import {
  Alert, AlertDescription, AlertTitle
} from "../components/ui/alert";

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
  const [searchParams, setSearchParams] = useSearchParams();
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [yearlyBilling, setYearlyBilling] = useState(false);
  const [subscribing, setSubscribing] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(null);
  
  // Stripe status
  const [stripeEnabled, setStripeEnabled] = useState(false);
  const [stripeConfigured, setStripeConfigured] = useState(false);
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  
  // SuperAdmin edit state
  const [editMode, setEditMode] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [planForm, setPlanForm] = useState({});
  const [savingPlan, setSavingPlan] = useState(false);
  const [newFeature, setNewFeature] = useState("");

  const isSuperAdmin = user?.role === "superadmin";

  // Poll payment status
  const pollPaymentStatus = useCallback(async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setCheckingPayment(false);
      toast.error("Tiempo agotado verificando el pago. Por favor, recarga la página.");
      return;
    }

    try {
      const res = await api.get(`/stripe/checkout-status/${sessionId}`);
      const { payment_status, subscription_applied } = res.data;

      if (payment_status === "paid") {
        setCheckingPayment(false);
        setPaymentSuccess(true);
        toast.success("¡Pago completado! Tu suscripción está activa.");
        // Clear URL params
        setSearchParams({});
        // Refresh data
        fetchData();
        // Reload after a moment to update user context
        setTimeout(() => window.location.reload(), 2000);
        return;
      } else if (payment_status === "expired") {
        setCheckingPayment(false);
        toast.error("La sesión de pago ha expirado. Por favor, intenta de nuevo.");
        setSearchParams({});
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error("Error checking payment status:", error);
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
      } else {
        setCheckingPayment(false);
        toast.error("Error verificando el pago.");
      }
    }
  }, [setSearchParams]);

  // Check for return from Stripe
  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    const success = searchParams.get("success");
    const canceled = searchParams.get("canceled");

    if (canceled) {
      toast.info("Pago cancelado");
      setSearchParams({});
    } else if (sessionId && success) {
      setCheckingPayment(true);
      pollPaymentStatus(sessionId);
    }
  }, [searchParams, pollPaymentStatus, setSearchParams]);

  useEffect(() => {
    fetchData();
    checkStripeStatus();
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

  const checkStripeStatus = async () => {
    try {
      const res = await api.get("/stripe/config/status");
      setStripeEnabled(res.data.enabled);
      setStripeConfigured(res.data.configured);
    } catch (error) {
      // Stripe not configured - that's fine, we'll use demo mode
      setStripeEnabled(false);
      setStripeConfigured(false);
    }
  };

  const handleSubscribe = async (plan, startTrial = false) => {
    if (currentSubscription?.plan?.name === plan.name && !currentSubscription?.is_free) {
      toast.info("Ya estás suscrito a este plan");
      return;
    }
    setConfirmDialog({ ...plan, startTrial });
  };

  const confirmSubscription = async () => {
    if (!confirmDialog) return;
    setSubscribing(true);
    
    try {
      const planPrice = yearlyBilling ? confirmDialog.price_yearly : confirmDialog.price_monthly;
      const startTrial = confirmDialog.startTrial;
      
      // If starting a trial, use direct subscription flow (no payment)
      if (startTrial && confirmDialog.trial_days > 0) {
        const billingCycle = yearlyBilling ? "yearly" : "monthly";
        const res = await api.post(`/subscriptions/subscribe/${confirmDialog.id}`, {
          billing_cycle: billingCycle,
          start_trial: true
        });
        
        toast.success(res.data.message || `¡Periodo de prueba activado!`);
        setConfirmDialog(null);
        fetchData();
        setTimeout(() => window.location.reload(), 1500);
        return;
      }
      
      // If Stripe is enabled and plan has a price, use Stripe checkout
      if (stripeEnabled && planPrice > 0) {
        // Create Stripe checkout session
        const billingCycle = yearlyBilling ? "yearly" : "monthly";
        const res = await api.post("/stripe/create-checkout", {
          plan_id: confirmDialog.id,
          origin_url: window.location.origin,
          billing_cycle: billingCycle
        });
        
        // Redirect to Stripe checkout
        if (res.data.checkout_url) {
          window.location.href = res.data.checkout_url;
          return;
        }
      } else {
        // Demo mode - use the existing subscription flow
        const billingCycle = yearlyBilling ? "yearly" : "monthly";
        await api.post(`/subscriptions/subscribe/${confirmDialog.id}`, {
          billing_cycle: billingCycle
        });
        toast.success(`¡Suscrito al plan ${confirmDialog.name} exitosamente!`);
        setConfirmDialog(null);
        fetchData();
        window.location.reload();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar la suscripción");
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

  // SuperAdmin: Edit Plan
  const openEditDialog = (plan) => {
    setEditingPlan(plan);
    setPlanForm({
      name: plan.name,
      description: plan.description || "",
      max_suppliers: plan.max_suppliers,
      max_catalogs: plan.max_catalogs,
      max_woocommerce_stores: plan.max_woocommerce_stores,
      price_monthly: plan.price_monthly,
      price_yearly: plan.price_yearly,
      features: [...(plan.features || [])]
    });
  };

  const handleSavePlan = async () => {
    if (!editingPlan) return;
    setSavingPlan(true);
    try {
      await api.put(`/subscriptions/plans/${editingPlan.id}`, planForm);
      toast.success(`Plan "${planForm.name}" actualizado correctamente`);
      setEditingPlan(null);
      setPlanForm({});
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar plan");
    } finally {
      setSavingPlan(false);
    }
  };

  const addFeature = () => {
    if (newFeature.trim()) {
      setPlanForm({
        ...planForm,
        features: [...(planForm.features || []), newFeature.trim()]
      });
      setNewFeature("");
    }
  };

  const removeFeature = (index) => {
    const newFeatures = [...planForm.features];
    newFeatures.splice(index, 1);
    setPlanForm({ ...planForm, features: newFeatures });
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

  if (loading || checkingPayment) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        {checkingPayment && (
          <p className="text-slate-600">Verificando estado del pago...</p>
        )}
      </div>
    );
  }

  if (paymentSuccess) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6">
        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
          <Check className="w-8 h-8 text-emerald-600" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">¡Pago completado!</h2>
        <p className="text-slate-600">Tu suscripción ha sido activada correctamente.</p>
        <p className="text-sm text-slate-500">Redirigiendo...</p>
      </div>
    );
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

      {/* SuperAdmin: Edit Mode Toggle */}
      {isSuperAdmin && (
        <div className="mb-6 flex justify-center">
          <Button
            variant={editMode ? "default" : "outline"}
            onClick={() => setEditMode(!editMode)}
            className={editMode ? "bg-indigo-600 hover:bg-indigo-700" : ""}
            data-testid="toggle-edit-mode"
          >
            <Settings className="w-4 h-4 mr-2" />
            {editMode ? "Modo Edición Activo" : "Editar Planes (SuperAdmin)"}
          </Button>
        </div>
      )}

      {/* Current Plan Badge */}
      {currentSubscription && !currentSubscription.is_free && (
        <div className="mb-6 flex justify-center">
          <Badge className="bg-indigo-100 text-indigo-700 px-4 py-2 text-sm">
            <Crown className="w-4 h-4 mr-2" />
            Plan actual: {currentPlanName}
          </Badge>
        </div>
      )}

      {/* Trial Period Banner */}
      {currentSubscription?.is_in_trial && (
        <Alert className="mb-6 max-w-2xl mx-auto border-emerald-200 bg-emerald-50">
          <CalendarDays className="h-4 w-4 text-emerald-600" />
          <AlertTitle className="text-emerald-800">Periodo de prueba activo</AlertTitle>
          <AlertDescription className="text-emerald-700">
            Estás disfrutando de {currentSubscription.trial_days_left} días restantes de prueba del plan {currentPlanName}.
            {currentSubscription.trial_end && (
              <span className="block mt-1 text-sm">
                Tu prueba termina el {new Date(currentSubscription.trial_end).toLocaleDateString('es-ES', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* SuperAdmin: Plans Table View (Edit Mode) */}
      {editMode && isSuperAdmin ? (
        <Card className="max-w-5xl mx-auto border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Settings className="w-5 h-5 text-indigo-600" />
              Administrar Planes de Suscripción
            </CardTitle>
            <CardDescription>
              Modifica precios, límites y características de cada plan
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Plan</TableHead>
                  <TableHead>Precio Mensual</TableHead>
                  <TableHead>Precio Anual</TableHead>
                  <TableHead>Proveedores</TableHead>
                  <TableHead>Catálogos</TableHead>
                  <TableHead>Tiendas</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {plans.map((plan) => (
                  <TableRow key={plan.id} data-testid={`plan-row-${plan.name.toLowerCase()}`}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{plan.name}</span>
                        {plan.name === "Professional" && (
                          <Badge className="bg-indigo-100 text-indigo-700 text-xs">Popular</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>€{plan.price_monthly.toFixed(2)}</TableCell>
                    <TableCell>€{plan.price_yearly.toFixed(2)}</TableCell>
                    <TableCell>{plan.max_suppliers >= 999999 ? "∞" : plan.max_suppliers}</TableCell>
                    <TableCell>{plan.max_catalogs >= 999999 ? "∞" : plan.max_catalogs}</TableCell>
                    <TableCell>{plan.max_woocommerce_stores >= 999999 ? "∞" : plan.max_woocommerce_stores}</TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(plan)}
                        data-testid={`edit-plan-${plan.name.toLowerCase()}`}
                      >
                        <Settings className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <>
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
                      {plan.trial_days > 0 && plan.price_monthly > 0 && (
                        <div className="mt-2">
                          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                            <CalendarDays className="w-3 h-3 mr-1" />
                            {plan.trial_days} días de prueba
                          </Badge>
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
                          Tiendas
                        </div>
                        <span className="font-semibold text-slate-900">
                          {plan.max_woocommerce_stores >= 999999 ? "∞" : plan.max_woocommerce_stores}
                        </span>
                      </div>
                    </div>

                    {/* Features */}
                    <div className="space-y-2 text-left mb-4">
                      {(plan.features || []).slice(0, 4).map((feature, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-slate-600">
                          <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                          {feature}
                        </div>
                      ))}
                    </div>
                  </CardContent>

                  <CardFooter className="flex flex-col gap-2">
                    {/* Trial Button - Show if plan has trial and user can use it */}
                    {plan.trial_days > 0 && plan.price_monthly > 0 && !isCurrentPlan && (
                      <Button
                        variant="outline"
                        className="w-full border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                        onClick={() => handleSubscribe(plan, true)}
                        data-testid={`trial-${plan.name.toLowerCase()}`}
                      >
                        <CalendarDays className="w-4 h-4 mr-2" />
                        Probar {plan.trial_days} días gratis
                      </Button>
                    )}
                    
                    {/* Main Subscribe Button */}
                    <Button
                      className={`w-full ${
                        isCurrentPlan 
                          ? "bg-slate-200 text-slate-600 hover:bg-slate-300" 
                          : plan.name === "Professional" 
                            ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                            : "btn-primary"
                      }`}
                      onClick={() => handleSubscribe(plan, false)}
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
        </>
      )}

      {/* Cancel Subscription */}
      {currentSubscription && !currentSubscription.is_free && !editMode && (
        <div className="mt-8 text-center">
          <Button variant="ghost" className="text-slate-500 hover:text-rose-600" onClick={handleCancel}>
            Cancelar suscripción
          </Button>
        </div>
      )}

      {/* Edit Plan Dialog (SuperAdmin) */}
      <Dialog open={!!editingPlan} onOpenChange={() => { setEditingPlan(null); setPlanForm({}); }}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Settings className="w-5 h-5 text-indigo-600" />
              Editar Plan: {editingPlan?.name}
            </DialogTitle>
            <DialogDescription>
              Modifica los detalles del plan de suscripción
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nombre del Plan</Label>
                <Input
                  value={planForm.name || ""}
                  onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                  data-testid="edit-plan-name"
                />
              </div>
              <div className="space-y-2 col-span-2">
                <Label>Descripción</Label>
                <Input
                  value={planForm.description || ""}
                  onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                  placeholder="Descripción corta del plan"
                  data-testid="edit-plan-description"
                />
              </div>
            </div>

            {/* Pricing */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Precio Mensual (€)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={planForm.price_monthly ?? ""}
                  onChange={(e) => setPlanForm({ ...planForm, price_monthly: parseFloat(e.target.value) || 0 })}
                  data-testid="edit-plan-price-monthly"
                />
              </div>
              <div className="space-y-2">
                <Label>Precio Anual (€)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={planForm.price_yearly ?? ""}
                  onChange={(e) => setPlanForm({ ...planForm, price_yearly: parseFloat(e.target.value) || 0 })}
                  data-testid="edit-plan-price-yearly"
                />
              </div>
            </div>

            {/* Limits */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Truck className="w-3 h-3" /> Proveedores
                </Label>
                <Input
                  type="number"
                  min="0"
                  value={planForm.max_suppliers ?? ""}
                  onChange={(e) => setPlanForm({ ...planForm, max_suppliers: parseInt(e.target.value) || 0 })}
                  placeholder="999999 = ilimitado"
                  data-testid="edit-plan-max-suppliers"
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <BookOpen className="w-3 h-3" /> Catálogos
                </Label>
                <Input
                  type="number"
                  min="0"
                  value={planForm.max_catalogs ?? ""}
                  onChange={(e) => setPlanForm({ ...planForm, max_catalogs: parseInt(e.target.value) || 0 })}
                  placeholder="999999 = ilimitado"
                  data-testid="edit-plan-max-catalogs"
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <ShoppingCart className="w-3 h-3" /> Tiendas
                </Label>
                <Input
                  type="number"
                  min="0"
                  value={planForm.max_woocommerce_stores ?? ""}
                  onChange={(e) => setPlanForm({ ...planForm, max_woocommerce_stores: parseInt(e.target.value) || 0 })}
                  placeholder="999999 = ilimitado"
                  data-testid="edit-plan-max-stores"
                />
              </div>
            </div>

            {/* Features */}
            <div className="space-y-2">
              <Label>Características del Plan</Label>
              <div className="space-y-2">
                {(planForm.features || []).map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="flex-1 px-3 py-2 bg-slate-50 rounded-lg text-sm flex items-center gap-2">
                      <Check className="w-4 h-4 text-emerald-500" />
                      {feature}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-rose-500 hover:text-rose-700"
                      onClick={() => removeFeature(idx)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2 mt-2">
                <Input
                  placeholder="Nueva característica..."
                  value={newFeature}
                  onChange={(e) => setNewFeature(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addFeature()}
                  data-testid="new-feature-input"
                />
                <Button variant="outline" size="sm" onClick={addFeature}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditingPlan(null); setPlanForm({}); }}>
              Cancelar
            </Button>
            <Button 
              className="btn-primary" 
              onClick={handleSavePlan}
              disabled={savingPlan}
              data-testid="save-plan-btn"
            >
              {savingPlan ? "Guardando..." : "Guardar Cambios"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subscribe Confirmation Dialog */}
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
              
              {/* Stripe payment info */}
              {stripeEnabled && (yearlyBilling ? confirmDialog.price_yearly : confirmDialog.price_monthly) > 0 ? (
                <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <div className="flex items-center gap-2 text-indigo-700 font-medium text-sm">
                    <CreditCard className="w-4 h-4" />
                    Pago seguro con Stripe
                  </div>
                  <p className="text-xs text-indigo-600 mt-1">
                    Serás redirigido a Stripe para completar el pago de forma segura.
                  </p>
                </div>
              ) : (
                <Alert className="mt-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Modo Demo</AlertTitle>
                  <AlertDescription>
                    {!stripeEnabled 
                      ? "Los pagos con Stripe no están habilitados. La suscripción se activará sin pago real."
                      : "Este plan es gratuito."}
                  </AlertDescription>
                </Alert>
              )}
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
              data-testid="confirm-subscribe-btn"
            >
              {subscribing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : stripeEnabled && (yearlyBilling ? confirmDialog?.price_yearly : confirmDialog?.price_monthly) > 0 ? (
                <>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Ir a Pagar
                </>
              ) : (
                "Confirmar Suscripción"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Subscriptions;
