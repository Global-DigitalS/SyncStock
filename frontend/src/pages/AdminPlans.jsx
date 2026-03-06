import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "../components/ui/alert-dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";
import {
  CreditCard, Plus, Pencil, Trash2, RefreshCw, CheckCircle, 
  Truck, BookOpen, Package, Store, Star, Users, Clock, Building2
} from "lucide-react";
import { Checkbox } from "../components/ui/checkbox";

const AdminPlans = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    max_suppliers: 5,
    max_catalogs: 3,
    max_products: 1000,
    max_stores: 1,
    price_monthly: 0,
    price_yearly: 0,
    features: [],
    is_default: false,
    sort_order: 0,
    crm_sync_enabled: false,
    crm_sync_intervals: []
  });
  const [newFeature, setNewFeature] = useState("");
  
  const SYNC_INTERVAL_OPTIONS = [
    { value: 1, label: "Cada hora" },
    { value: 6, label: "Cada 6 horas" },
    { value: 12, label: "Cada 12 horas" },
    { value: 24, label: "Cada 24 horas" }
  ];

  useEffect(() => {
    if (user?.role !== "superadmin") {
      navigate("/");
      return;
    }
    fetchPlans();
  }, [user, navigate]);

  const fetchPlans = async () => {
    try {
      const res = await api.get("/admin/plans");
      setPlans(res.data);
    } catch (error) {
      toast.error("Error al cargar planes");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      max_suppliers: 5,
      max_catalogs: 3,
      max_products: 1000,
      max_stores: 1,
      price_monthly: 0,
      price_yearly: 0,
      features: [],
      is_default: false,
      sort_order: plans.length,
      crm_sync_enabled: false,
      crm_sync_intervals: []
    });
    setSelectedPlan(null);
    setNewFeature("");
  };

  const openCreate = () => {
    resetForm();
    setShowDialog(true);
  };

  const openEdit = (plan) => {
    setSelectedPlan(plan);
    setFormData({
      name: plan.name,
      description: plan.description || "",
      max_suppliers: plan.max_suppliers || 5,
      max_catalogs: plan.max_catalogs || 3,
      max_products: plan.max_products || 1000,
      max_stores: plan.max_stores || 1,
      price_monthly: plan.price_monthly || 0,
      price_yearly: plan.price_yearly || 0,
      features: plan.features || [],
      is_default: plan.is_default || false,
      sort_order: plan.sort_order || 0,
      crm_sync_enabled: plan.crm_sync_enabled || false,
      crm_sync_intervals: plan.crm_sync_intervals || []
    });
    setShowDialog(true);
  };

  const openDelete = (plan) => {
    setSelectedPlan(plan);
    setShowDeleteDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("El nombre es obligatorio");
      return;
    }

    setSaving(true);
    try {
      if (selectedPlan) {
        await api.put(`/admin/plans/${selectedPlan.id}`, formData);
        toast.success("Plan actualizado");
      } else {
        await api.post("/admin/plans", formData);
        toast.success("Plan creado");
      }
      setShowDialog(false);
      resetForm();
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/admin/plans/${selectedPlan.id}`);
      toast.success("Plan eliminado");
      setShowDeleteDialog(false);
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const addFeature = () => {
    if (newFeature.trim() && !formData.features.includes(newFeature.trim())) {
      setFormData({
        ...formData,
        features: [...formData.features, newFeature.trim()]
      });
      setNewFeature("");
    }
  };

  const removeFeature = (feature) => {
    setFormData({
      ...formData,
      features: formData.features.filter(f => f !== feature)
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Gestión de Planes
          </h1>
          <p className="text-slate-500">Configura los planes de suscripción disponibles</p>
        </div>
        <Button onClick={openCreate} className="btn-primary" data-testid="add-plan-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Plan
        </Button>
      </div>

      {/* Plans Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
        {plans.map((plan) => (
          <Card key={plan.id} className={`relative ${plan.is_default ? "ring-2 ring-purple-500" : ""}`}>
            {plan.is_default && (
              <Badge className="absolute -top-2 -right-2 bg-purple-600">
                <Star className="w-3 h-3 mr-1" />
                Predeterminado
              </Badge>
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{plan.name}</CardTitle>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => openEdit(plan)}>
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => openDelete(plan)} className="text-rose-600 hover:text-rose-700">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              {plan.description && (
                <CardDescription>{plan.description}</CardDescription>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Pricing */}
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900">
                  {plan.price_monthly > 0 ? `${plan.price_monthly}€` : "Gratis"}
                </span>
                {plan.price_monthly > 0 && <span className="text-slate-500">/mes</span>}
              </div>
              {plan.price_yearly > 0 && (
                <p className="text-sm text-slate-500">
                  o {plan.price_yearly}€/año (ahorra {Math.round((1 - plan.price_yearly / (plan.price_monthly * 12)) * 100)}%)
                </p>
              )}

              {/* Limits */}
              <div className="space-y-2 pt-4 border-t">
                <div className="flex items-center gap-2 text-sm">
                  <Truck className="w-4 h-4 text-slate-400" />
                  <span>{plan.max_suppliers} proveedores</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <BookOpen className="w-4 h-4 text-slate-400" />
                  <span>{plan.max_catalogs} catálogos</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Package className="w-4 h-4 text-slate-400" />
                  <span>{plan.max_products?.toLocaleString() || "1,000"} productos</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Store className="w-4 h-4 text-slate-400" />
                  <span>{plan.max_stores} tiendas</span>
                </div>
                {plan.crm_sync_enabled && (
                  <div className="flex items-center gap-2 text-sm">
                    <Building2 className="w-4 h-4 text-blue-500" />
                    <span className="text-blue-600 font-medium">
                      Sync CRM: {plan.crm_sync_intervals?.map(h => `${h}h`).join(", ") || "24h"}
                    </span>
                  </div>
                )}
              </div>

              {/* Features */}
              {plan.features && plan.features.length > 0 && (
                <div className="space-y-2 pt-4 border-t">
                  {plan.features.map((feature, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}

        {plans.length === 0 && (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <CreditCard className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No hay planes</h3>
              <p className="text-slate-500 mb-4">Crea el primer plan de suscripción</p>
              <Button onClick={openCreate} className="btn-primary">
                <Plus className="w-4 h-4 mr-2" />
                Crear Plan
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <CreditCard className="w-5 h-5 text-purple-600" />
              {selectedPlan ? "Editar Plan" : "Nuevo Plan"}
            </DialogTitle>
            <DialogDescription>
              {selectedPlan ? "Modifica los detalles del plan" : "Configura un nuevo plan de suscripción"}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Info */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Plan Pro"
                  className="input-base"
                  data-testid="plan-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sort_order">Orden</Label>
                <Input
                  id="sort_order"
                  type="number"
                  value={formData.sort_order}
                  onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                  className="input-base"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descripción</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Ideal para pequeños negocios"
                className="input-base"
              />
            </div>

            {/* Pricing */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="price_monthly">Precio Mensual (€)</Label>
                <Input
                  id="price_monthly"
                  type="number"
                  step="0.01"
                  value={formData.price_monthly}
                  onChange={(e) => setFormData({ ...formData, price_monthly: parseFloat(e.target.value) || 0 })}
                  className="input-base"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="price_yearly">Precio Anual (€)</Label>
                <Input
                  id="price_yearly"
                  type="number"
                  step="0.01"
                  value={formData.price_yearly}
                  onChange={(e) => setFormData({ ...formData, price_yearly: parseFloat(e.target.value) || 0 })}
                  className="input-base"
                />
              </div>
            </div>

            {/* Limits */}
            <div className="space-y-3 pt-4 border-t">
              <Label className="text-base font-semibold">Límites del Plan</Label>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="max_suppliers" className="text-sm flex items-center gap-2">
                    <Truck className="w-4 h-4" /> Proveedores
                  </Label>
                  <Input
                    id="max_suppliers"
                    type="number"
                    value={formData.max_suppliers}
                    onChange={(e) => setFormData({ ...formData, max_suppliers: parseInt(e.target.value) || 0 })}
                    className="input-base"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_catalogs" className="text-sm flex items-center gap-2">
                    <BookOpen className="w-4 h-4" /> Catálogos
                  </Label>
                  <Input
                    id="max_catalogs"
                    type="number"
                    value={formData.max_catalogs}
                    onChange={(e) => setFormData({ ...formData, max_catalogs: parseInt(e.target.value) || 0 })}
                    className="input-base"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_products" className="text-sm flex items-center gap-2">
                    <Package className="w-4 h-4" /> Productos
                  </Label>
                  <Input
                    id="max_products"
                    type="number"
                    value={formData.max_products}
                    onChange={(e) => setFormData({ ...formData, max_products: parseInt(e.target.value) || 0 })}
                    className="input-base"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_stores" className="text-sm flex items-center gap-2">
                    <Store className="w-4 h-4" /> Tiendas
                  </Label>
                  <Input
                    id="max_stores"
                    type="number"
                    value={formData.max_stores}
                    onChange={(e) => setFormData({ ...formData, max_stores: parseInt(e.target.value) || 0 })}
                    className="input-base"
                  />
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="space-y-3 pt-4 border-t">
              <Label className="text-base font-semibold">Características</Label>
              <div className="flex gap-2">
                <Input
                  value={newFeature}
                  onChange={(e) => setNewFeature(e.target.value)}
                  placeholder="Ej: Soporte prioritario"
                  className="input-base"
                  onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addFeature())}
                />
                <Button type="button" variant="outline" onClick={addFeature}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.features.map((feature, idx) => (
                  <Badge key={idx} variant="secondary" className="py-1 px-3">
                    {feature}
                    <button 
                      type="button"
                      onClick={() => removeFeature(feature)}
                      className="ml-2 hover:text-rose-600"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </div>

            {/* Default Plan */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="space-y-0.5">
                <Label>Plan Predeterminado</Label>
                <p className="text-sm text-slate-500">Este plan se asignará a nuevos usuarios</p>
              </div>
              <Switch
                checked={formData.is_default}
                onCheckedChange={(checked) => setFormData({ ...formData, is_default: checked })}
              />
            </div>

            {/* CRM Auto-Sync */}
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-blue-600" />
                    Sincronización CRM Automática
                  </Label>
                  <p className="text-sm text-slate-500">Permite sincronización programada con CRM</p>
                </div>
                <Switch
                  checked={formData.crm_sync_enabled}
                  onCheckedChange={(checked) => setFormData({ 
                    ...formData, 
                    crm_sync_enabled: checked,
                    crm_sync_intervals: checked ? [24] : []
                  })}
                  data-testid="crm-sync-enabled-switch"
                />
              </div>
              
              {formData.crm_sync_enabled && (
                <div className="space-y-2 pl-6 border-l-2 border-blue-200">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Intervalos permitidos
                  </Label>
                  <div className="flex flex-wrap gap-3">
                    {SYNC_INTERVAL_OPTIONS.map((option) => (
                      <label 
                        key={option.value}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                          formData.crm_sync_intervals.includes(option.value)
                            ? "bg-blue-50 border-blue-300 text-blue-700"
                            : "bg-slate-50 border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <Checkbox
                          checked={formData.crm_sync_intervals.includes(option.value)}
                          onCheckedChange={(checked) => {
                            const newIntervals = checked
                              ? [...formData.crm_sync_intervals, option.value].sort((a, b) => a - b)
                              : formData.crm_sync_intervals.filter(i => i !== option.value);
                            setFormData({ ...formData, crm_sync_intervals: newIntervals });
                          }}
                        />
                        <span className="text-sm font-medium">{option.label}</span>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Los usuarios de este plan podrán elegir entre estos intervalos para sincronizar con su CRM
                  </p>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="plan-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedPlan ? "Guardar" : "Crear Plan"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar plan?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará el plan "{selectedPlan?.name}". Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminPlans;
