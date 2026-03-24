import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { sanitizeString, sanitizeEmail, sanitizeFormData } from "../utils/sanitizer";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  User, Mail, Building2, Shield, Crown, Edit3, Eye, Save,
  Truck, BookOpen, Package, ShoppingCart, CreditCard, History,
  TrendingUp, Calendar, RefreshCw, CheckCircle, XCircle, Clock,
  DollarSign, AlertTriangle, Globe
} from "lucide-react";

const ROLE_CONFIG = {
  superadmin: { label: "SuperAdmin", color: "bg-purple-100 text-purple-700", icon: Crown },
  admin: { label: "Administrador", color: "bg-indigo-100 text-indigo-700", icon: Shield },
  user: { label: "Usuario", color: "bg-emerald-100 text-emerald-700", icon: Edit3 },
  viewer: { label: "Visor", color: "bg-slate-100 text-slate-600", icon: Eye }
};

const UserDetailDialog = ({ userId, open, onClose, onUpdate }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("info");
  const [userData, setUserData] = useState(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    role: "user",
    is_active: true,
    max_suppliers: 10,
    max_catalogs: 5,
    max_products: 1000,
    max_woocommerce_stores: 2,
    max_marketplaces: 0,
    subscription_plan_id: "",
    subscription_status: "none"
  });

  const loadUserData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/users/${userId}/stats`);
      setUserData(res.data);
      
      // Populate form
      const user = res.data.user;
      setFormData({
        name: user.name || "",
        email: user.email || "",
        company: user.company || "",
        role: user.role || "user",
        is_active: user.is_active !== false,
        max_suppliers: res.data.limits.max_suppliers,
        max_catalogs: res.data.limits.max_catalogs,
        max_products: res.data.limits.max_products,
        max_woocommerce_stores: res.data.limits.max_stores,
        max_marketplaces: res.data.limits.max_marketplaces || 0,
        subscription_plan_id: user.subscription_plan_id || "",
        subscription_status: user.subscription_status || "none"
      });
    } catch (error) {
      toast.error("Error al cargar datos del usuario");
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const loadSubscriptionPlans = useCallback(async () => {
    try {
      const res = await api.get("/subscriptions/plans");
      setSubscriptionPlans(res.data);
    } catch (error) {
      // handled silently
    }
  }, []);

  // Load user data
  useEffect(() => {
    if (open && userId) {
      loadUserData();
      loadSubscriptionPlans();
    }
  }, [open, userId, loadUserData, loadSubscriptionPlans]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Sanitize form data before sending
      const { max_marketplaces, ...rest } = formData;
      const sanitizedData = {
        ...rest,
        name: sanitizeString(formData.name),
        email: sanitizeEmail(formData.email),
        company: formData.company ? sanitizeString(formData.company) : "",
        max_marketplace_connections: max_marketplaces
      };
      await api.put(`/users/${userId}/full`, sanitizedData);
      toast.success("Usuario actualizado correctamente");
      onUpdate?.();
      loadUserData(); // Reload to get fresh data
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handlePlanChange = async (planId) => {
    // Find plan details
    const plan = subscriptionPlans.find(p => p.id === planId);
    if (plan) {
      setFormData(prev => ({
        ...prev,
        subscription_plan_id: planId,
        subscription_plan_name: plan.name,
        max_suppliers: plan.max_suppliers,
        max_catalogs: plan.max_catalogs,
        max_products: plan.max_products || 1000,
        max_woocommerce_stores: plan.max_stores || plan.max_woocommerce_stores || 2,
        max_marketplaces: plan.max_marketplace_connections || plan.max_marketplaces || 0
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        subscription_plan_id: "",
        subscription_plan_name: ""
      }));
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
      case "active":
      case "paid":
        return <Badge className="bg-emerald-100 text-emerald-700"><CheckCircle className="w-3 h-3 mr-1" />Completado</Badge>;
      case "pending":
      case "initiated":
        return <Badge className="bg-amber-100 text-amber-700"><Clock className="w-3 h-3 mr-1" />Pendiente</Badge>;
      case "failed":
      case "expired":
        return <Badge className="bg-rose-100 text-rose-700"><XCircle className="w-3 h-3 mr-1" />Fallido</Badge>;
      default:
        return <Badge className="bg-slate-100 text-slate-600">{status || "N/A"}</Badge>;
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <User className="w-6 h-6 text-indigo-600" />
            Ficha de Usuario
          </DialogTitle>
          <DialogDescription>
            Gestiona todos los datos y permisos del usuario
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
            <TabsList className="grid grid-cols-4 gap-2 bg-slate-100 p-1">
              <TabsTrigger value="info" className="data-[state=active]:bg-white">
                <User className="w-4 h-4 mr-2" />
                Información
              </TabsTrigger>
              <TabsTrigger value="subscription" className="data-[state=active]:bg-white">
                <CreditCard className="w-4 h-4 mr-2" />
                Suscripción
              </TabsTrigger>
              <TabsTrigger value="limits" className="data-[state=active]:bg-white">
                <TrendingUp className="w-4 h-4 mr-2" />
                Límites y Uso
              </TabsTrigger>
              <TabsTrigger value="activity" className="data-[state=active]:bg-white">
                <History className="w-4 h-4 mr-2" />
                Actividad
              </TabsTrigger>
            </TabsList>

            {/* Tab: Información General */}
            <TabsContent value="info" className="space-y-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Datos Personales</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Nombre</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input-base"
                        data-testid="user-name-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="input-base"
                        data-testid="user-email-input"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="company">Empresa</Label>
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                        className="input-base"
                        placeholder="Opcional"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Rol</Label>
                      <Select
                        value={formData.role}
                        onValueChange={(v) => setFormData({ ...formData, role: v })}
                      >
                        <SelectTrigger className="input-base" data-testid="user-role-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(ROLE_CONFIG).map(([role, config]) => (
                            <SelectItem key={role} value={role}>
                              <div className="flex items-center gap-2">
                                <config.icon className="w-4 h-4" />
                                {config.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${formData.is_active ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                      <div>
                        <p className="font-medium text-slate-900">Estado de la Cuenta</p>
                        <p className="text-sm text-slate-500">
                          {formData.is_active ? "El usuario puede acceder al sistema" : "El usuario no puede iniciar sesión"}
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={formData.is_active}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                      data-testid="user-active-switch"
                    />
                  </div>

                  <div className="pt-4 border-t">
                    <p className="text-sm text-slate-500">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Registrado el {formatDate(userData?.user?.created_at)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab: Suscripción */}
            <TabsContent value="subscription" className="space-y-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-indigo-600" />
                    Plan de Suscripción
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Plan Actual</Label>
                      <Select
                        value={formData.subscription_plan_id || "none"}
                        onValueChange={handlePlanChange}
                      >
                        <SelectTrigger className="input-base" data-testid="user-plan-select">
                          <SelectValue placeholder="Sin plan" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Sin plan asignado</SelectItem>
                          {subscriptionPlans.map((plan) => (
                            <SelectItem key={plan.id} value={plan.id}>
                              {plan.name} - €{plan.price_monthly}/mes
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Estado de Suscripción</Label>
                      <Select
                        value={formData.subscription_status}
                        onValueChange={(v) => setFormData({ ...formData, subscription_status: v })}
                      >
                        <SelectTrigger className="input-base" data-testid="user-sub-status-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Sin suscripción</SelectItem>
                          <SelectItem value="active">Activa</SelectItem>
                          <SelectItem value="pending">Pendiente</SelectItem>
                          <SelectItem value="cancelled">Cancelada</SelectItem>
                          <SelectItem value="expired">Expirada</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {userData?.subscription?.plan_details && (
                    <div className="p-4 bg-indigo-50 rounded-lg">
                      <h4 className="font-medium text-indigo-900 mb-2">Detalles del Plan</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <p className="text-indigo-700">
                          <Truck className="w-4 h-4 inline mr-1" />
                          {userData.subscription.plan_details.max_suppliers} proveedores
                        </p>
                        <p className="text-indigo-700">
                          <BookOpen className="w-4 h-4 inline mr-1" />
                          {userData.subscription.plan_details.max_catalogs} catálogos
                        </p>
                        <p className="text-indigo-700">
                          <Package className="w-4 h-4 inline mr-1" />
                          {userData.subscription.plan_details.max_products || "Ilimitados"} productos
                        </p>
                        <p className="text-indigo-700">
                          <ShoppingCart className="w-4 h-4 inline mr-1" />
                          {userData.subscription.plan_details.max_stores || userData.subscription.plan_details.max_woocommerce_stores} tiendas
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Payment History */}
                  {userData?.payment_history?.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-medium text-slate-900 mb-3 flex items-center gap-2">
                        <DollarSign className="w-4 h-4" />
                        Historial de Pagos
                      </h4>
                      <div className="space-y-2">
                        {userData.payment_history.map((payment, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                              <p className="font-medium text-slate-900">{payment.plan_name}</p>
                              <p className="text-sm text-slate-500">{formatDate(payment.created_at)}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-medium">€{payment.amount}</p>
                              {getStatusBadge(payment.payment_status)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab: Límites y Uso */}
            <TabsContent value="limits" className="space-y-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Configuración de Límites</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <Truck className="w-4 h-4 text-slate-500" />
                        Máx. Proveedores
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.max_suppliers}
                        onChange={(e) => setFormData({ ...formData, max_suppliers: parseInt(e.target.value) || 0 })}
                        className="input-base"
                      />
                      <p className="text-xs text-slate-500">
                        Usando: {userData?.usage?.suppliers || 0} de {formData.max_suppliers}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-slate-500" />
                        Máx. Catálogos
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.max_catalogs}
                        onChange={(e) => setFormData({ ...formData, max_catalogs: parseInt(e.target.value) || 0 })}
                        className="input-base"
                      />
                      <p className="text-xs text-slate-500">
                        Usando: {userData?.usage?.catalogs || 0} de {formData.max_catalogs}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-slate-500" />
                        Máx. Productos
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.max_products}
                        onChange={(e) => setFormData({ ...formData, max_products: parseInt(e.target.value) || 0 })}
                        className="input-base"
                      />
                      <p className="text-xs text-slate-500">
                        Usando: {userData?.usage?.products || 0} de {formData.max_products}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <ShoppingCart className="w-4 h-4 text-slate-500" />
                        Máx. Tiendas
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.max_woocommerce_stores}
                        onChange={(e) => setFormData({ ...formData, max_woocommerce_stores: parseInt(e.target.value) || 0 })}
                        className="input-base"
                      />
                      <p className="text-xs text-slate-500">
                        Usando: {userData?.usage?.stores || 0} de {formData.max_woocommerce_stores}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-slate-500" />
                        Máx. Marketplaces
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.max_marketplaces}
                        onChange={(e) => setFormData({ ...formData, max_marketplaces: parseInt(e.target.value) || 0 })}
                        className="input-base"
                      />
                      <p className="text-xs text-slate-500">
                        Usando: {userData?.usage?.marketplaces || 0} de {formData.max_marketplaces}
                      </p>
                    </div>
                  </div>

                  {/* Usage Bar Charts */}
                  <div className="mt-6 space-y-3">
                    <h4 className="font-medium text-slate-900">Uso de Recursos</h4>
                    {[
                      { label: "Proveedores", used: userData?.usage?.suppliers || 0, max: formData.max_suppliers, icon: Truck },
                      { label: "Catálogos", used: userData?.usage?.catalogs || 0, max: formData.max_catalogs, icon: BookOpen },
                      { label: "Productos", used: userData?.usage?.products || 0, max: formData.max_products, icon: Package },
                      { label: "Tiendas", used: userData?.usage?.stores || 0, max: formData.max_woocommerce_stores, icon: ShoppingCart },
                      { label: "Marketplaces", used: userData?.usage?.marketplaces || 0, max: formData.max_marketplaces, icon: Globe }
                    ].map((item, idx) => {
                      const percentage = item.max > 0 ? Math.min((item.used / item.max) * 100, 100) : 0;
                      const isOverLimit = item.used >= item.max;
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="flex items-center gap-2 text-slate-600">
                              <item.icon className="w-4 h-4" />
                              {item.label}
                            </span>
                            <span className={isOverLimit ? "text-rose-600 font-medium" : "text-slate-600"}>
                              {item.used} / {item.max}
                              {isOverLimit && <AlertTriangle className="w-4 h-4 inline ml-1" />}
                            </span>
                          </div>
                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full transition-all ${isOverLimit ? 'bg-rose-500' : percentage > 80 ? 'bg-amber-500' : 'bg-indigo-500'}`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab: Actividad */}
            <TabsContent value="activity" className="space-y-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <History className="w-5 h-5 text-indigo-600" />
                    Sincronizaciones Recientes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {userData?.recent_syncs?.length > 0 ? (
                    <div className="space-y-3">
                      {userData.recent_syncs.map((sync, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div>
                            <p className="font-medium text-slate-900">{sync.supplier_name || "Sincronización"}</p>
                            <p className="text-sm text-slate-500">{formatDate(sync.started_at)}</p>
                          </div>
                          <div className="text-right">
                            {getStatusBadge(sync.status)}
                            {sync.products_updated > 0 && (
                              <p className="text-xs text-slate-500 mt-1">
                                {sync.products_updated} productos actualizados
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <History className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No hay actividad reciente</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}

        {/* Save Button */}
        {!loading && (
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={saving} className="btn-primary" data-testid="save-user-btn">
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Guardar Cambios
                </>
              )}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default UserDetailDialog;
