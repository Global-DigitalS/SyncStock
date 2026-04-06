import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  Percent,
  Plus,
  Pencil,
  Trash2,
  ArrowUpRight,
  Info
} from "lucide-react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import { Badge } from "../components/ui/badge";

const MarginRules = () => {
  const [rules, setRules] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    rule_type: "percentage",
    value: "",
    apply_to: "all",
    apply_to_value: "",
    min_price: "",
    max_price: "",
    priority: 0
  });
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [rulesRes, suppliersRes, categoriesRes] = await Promise.all([
        api.get("/margin-rules"),
        api.get("/suppliers"),
        api.get("/products/categories")
      ]);
      setRules(rulesRes.data);
      setSuppliers(suppliersRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error("Error al cargar las reglas de margen");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const resetForm = () => {
    setFormData({
      name: "",
      rule_type: "percentage",
      value: "",
      apply_to: "all",
      apply_to_value: "",
      min_price: "",
      max_price: "",
      priority: 0
    });
    setSelectedRule(null);
  };

  const openCreate = () => {
    resetForm();
    setShowDialog(true);
  };

  const openEdit = (rule) => {
    setSelectedRule(rule);
    setFormData({
      name: rule.name,
      rule_type: rule.rule_type,
      value: rule.value.toString(),
      apply_to: rule.apply_to,
      apply_to_value: rule.apply_to_value || "",
      min_price: rule.min_price?.toString() || "",
      max_price: rule.max_price?.toString() || "",
      priority: rule.priority
    });
    setShowDialog(true);
  };

  const openDelete = (rule) => {
    setSelectedRule(rule);
    setShowDeleteDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.value) {
      toast.error("El nombre y valor son obligatorios");
      return;
    }

    setSaving(true);
    const payload = {
      name: formData.name,
      rule_type: formData.rule_type,
      value: parseFloat(formData.value),
      apply_to: formData.apply_to,
      apply_to_value: formData.apply_to !== "all" ? formData.apply_to_value : null,
      min_price: formData.min_price ? parseFloat(formData.min_price) : null,
      max_price: formData.max_price ? parseFloat(formData.max_price) : null,
      priority: parseInt(formData.priority) || 0
    };

    try {
      if (selectedRule) {
        await api.put(`/margin-rules/${selectedRule.id}`, payload);
        toast.success("Regla actualizada");
      } else {
        await api.post("/margin-rules", payload);
        toast.success("Regla creada");
      }
      setShowDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar la regla");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/margin-rules/${selectedRule.id}`);
      toast.success("Regla eliminada");
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar la regla");
    }
  };

  const getRuleTypeLabel = (type) => {
    switch (type) {
      case "percentage": return "Porcentaje";
      case "fixed": return "Fijo";
      default: return type;
    }
  };

  const getApplyToLabel = (applyTo, value) => {
    switch (applyTo) {
      case "all": return "Todos los productos";
      case "category": return `Categoría: ${value}`;
      case "supplier": 
        const supplier = suppliers.find(s => s.id === value);
        return `Proveedor: ${supplier?.name || value}`;
      default: return applyTo;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Reglas de Margen
          </h1>
          <p className="text-slate-500">
            Configura tus márgenes de beneficio automáticos
          </p>
        </div>
        <Button onClick={openCreate} className="btn-primary" data-testid="add-rule-btn">
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Nueva Regla
        </Button>
      </div>

      {/* Info Card */}
      <Card className="border-indigo-200 bg-indigo-50 mb-6">
        <CardContent className="p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-indigo-600 mt-0.5" strokeWidth={1.5} />
          <div className="text-sm text-indigo-800">
            <p className="font-medium mb-1">Cómo funcionan las reglas de margen</p>
            <p className="text-indigo-700">
              Las reglas se aplican en orden de prioridad (mayor número = mayor prioridad). 
              Se aplica la primera regla que coincida con el producto. Puedes crear reglas 
              para todos los productos, por categoría o por proveedor.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Rules List */}
      {rules.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Percent className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay reglas de margen
          </h3>
          <p className="text-slate-500 mb-4">
            Crea tu primera regla para aplicar márgenes automáticos a tus productos
          </p>
          <Button onClick={openCreate} className="btn-primary" data-testid="empty-add-rule">
            <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Nueva Regla
          </Button>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Regla</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                  <TableHead>Aplica a</TableHead>
                  <TableHead>Rango de precio</TableHead>
                  <TableHead className="text-center">Prioridad</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id} className="table-row" data-testid={`rule-row-${rule.id}`}>
                    <TableCell>
                      <p className="font-medium text-slate-900">{rule.name}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                        {getRuleTypeLabel(rule.rule_type)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono font-semibold text-emerald-600">
                        {rule.rule_type === "percentage" ? `+${rule.value}%` : `+${rule.value.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}`}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-600">
                        {getApplyToLabel(rule.apply_to, rule.apply_to_value)}
                      </span>
                    </TableCell>
                    <TableCell>
                      {rule.min_price || rule.max_price ? (
                        <span className="text-sm text-slate-500 font-mono">
                          {rule.min_price ? `${rule.min_price}€` : "0€"} - {rule.max_price ? `${rule.max_price}€` : "∞"}
                        </span>
                      ) : (
                        <span className="text-sm text-slate-400">Sin límite</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-mono font-medium">{rule.priority}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEdit(rule)}
                          className="h-8 w-8 p-0"
                          data-testid={`edit-rule-${rule.id}`}
                        >
                          <Pencil className="w-4 h-4" strokeWidth={1.5} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDelete(rule)}
                          className="h-8 w-8 p-0 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                          data-testid={`delete-rule-${rule.id}`}
                        >
                          <Trash2 className="w-4 h-4" strokeWidth={1.5} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              {selectedRule ? "Editar Regla" : "Nueva Regla de Margen"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la regla *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ej: Margen general 30%"
                className="input-base"
                data-testid="rule-name-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de margen</Label>
                <Select
                  value={formData.rule_type}
                  onValueChange={(value) => setFormData({ ...formData, rule_type: value })}
                >
                  <SelectTrigger className="input-base" data-testid="rule-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percentage">Porcentaje (%)</SelectItem>
                    <SelectItem value="fixed">Cantidad fija (€)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="value">Valor *</Label>
                <Input
                  id="value"
                  type="number"
                  step="0.01"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  placeholder={formData.rule_type === "percentage" ? "30" : "10.00"}
                  className="input-base font-mono"
                  data-testid="rule-value-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Aplicar a</Label>
              <Select
                value={formData.apply_to}
                onValueChange={(value) => setFormData({ ...formData, apply_to: value, apply_to_value: "" })}
              >
                <SelectTrigger className="input-base" data-testid="rule-apply-to-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos los productos</SelectItem>
                  <SelectItem value="category">Por categoría</SelectItem>
                  <SelectItem value="supplier">Por proveedor</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.apply_to === "category" && (
              <div className="space-y-2">
                <Label>Categoría</Label>
                <Select
                  value={formData.apply_to_value}
                  onValueChange={(value) => setFormData({ ...formData, apply_to_value: value })}
                >
                  <SelectTrigger className="input-base" data-testid="rule-category-select">
                    <SelectValue placeholder="Seleccionar categoría" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.filter(Boolean).map((cat) => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {formData.apply_to === "supplier" && (
              <div className="space-y-2">
                <Label>Proveedor</Label>
                <Select
                  value={formData.apply_to_value}
                  onValueChange={(value) => setFormData({ ...formData, apply_to_value: value })}
                >
                  <SelectTrigger className="input-base" data-testid="rule-supplier-select">
                    <SelectValue placeholder="Seleccionar proveedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map((sup) => (
                      <SelectItem key={sup.id} value={sup.id}>{sup.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="min_price">Precio mínimo (€)</Label>
                <Input
                  id="min_price"
                  type="number"
                  step="0.01"
                  value={formData.min_price}
                  onChange={(e) => setFormData({ ...formData, min_price: e.target.value })}
                  placeholder="0.00"
                  className="input-base font-mono"
                  data-testid="rule-min-price"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_price">Precio máximo (€)</Label>
                <Input
                  id="max_price"
                  type="number"
                  step="0.01"
                  value={formData.max_price}
                  onChange={(e) => setFormData({ ...formData, max_price: e.target.value })}
                  placeholder="Sin límite"
                  className="input-base font-mono"
                  data-testid="rule-max-price"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Prioridad</Label>
              <Input
                id="priority"
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                placeholder="0"
                className="input-base font-mono w-24"
                data-testid="rule-priority-input"
              />
              <p className="text-xs text-slate-500">Mayor número = mayor prioridad</p>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="rule-submit-btn">
                {selectedRule ? "Guardar Cambios" : "Crear Regla"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar regla?</AlertDialogTitle>
            <AlertDialogDescription>
              La regla "{selectedRule?.name}" será eliminada permanentemente. Los precios actuales de tu catálogo no se modificarán.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700 text-white" data-testid="confirm-delete-rule">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default MarginRules;
