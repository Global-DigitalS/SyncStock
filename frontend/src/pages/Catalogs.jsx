import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  BookOpen,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Package,
  Percent,
  Search,
  Star,
  Eye,
  RefreshCw,
  Settings,
  ArrowRight,
  FolderTree
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import CatalogCategories from "../components/CatalogCategories";

const Catalogs = () => {
  const navigate = useNavigate();
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRulesDialog, setShowRulesDialog] = useState(false);
  const [showCategoriesDialog, setShowCategoriesDialog] = useState(false);
  const [selectedCatalog, setSelectedCatalog] = useState(null);
  const [formData, setFormData] = useState({ name: "", description: "", is_default: false });
  const [saving, setSaving] = useState(false);
  const [stores, setStores] = useState([]);
  
  // Rules state
  const [catalogRules, setCatalogRules] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [ruleForm, setRuleForm] = useState({
    name: "",
    rule_type: "percentage",
    value: "",
    apply_to: "all",
    apply_to_value: "",
    min_price: "",
    max_price: "",
    priority: 0
  });
  const [editingRule, setEditingRule] = useState(null);
  const [savingRule, setSavingRule] = useState(false);

  const fetchCatalogs = useCallback(async () => {
    try {
      const res = await api.get("/catalogs");
      setCatalogs(res.data);
    } catch (error) {
      toast.error("Error al cargar catálogos");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSuppliersAndCategories = useCallback(async () => {
    try {
      const [suppliersRes, categoriesRes, storesRes] = await Promise.all([
        api.get("/suppliers"),
        api.get("/products/categories"),
        api.get("/stores/configs")
      ]);
      setSuppliers(suppliersRes.data);
      setCategories(categoriesRes.data);
      setStores(storesRes.data || []);
    } catch (error) {
      // handled silently
    }
  }, []);

  useEffect(() => {
    fetchCatalogs();
    fetchSuppliersAndCategories();
  }, [fetchCatalogs, fetchSuppliersAndCategories]);

  const resetForm = () => {
    setFormData({ name: "", description: "", is_default: false });
    setSelectedCatalog(null);
  };

  const openEdit = (catalog) => {
    setSelectedCatalog(catalog);
    setFormData({
      name: catalog.name,
      description: catalog.description || "",
      is_default: catalog.is_default
    });
    setShowDialog(true);
  };

  const openDelete = (catalog) => {
    setSelectedCatalog(catalog);
    setShowDeleteDialog(true);
  };

  const openRules = async (catalog) => {
    setSelectedCatalog(catalog);
    setEditingRule(null);
    setRuleForm({
      name: "",
      rule_type: "percentage",
      value: "",
      apply_to: "all",
      apply_to_value: "",
      min_price: "",
      max_price: "",
      priority: 0
    });
    try {
      const res = await api.get(`/catalogs/${catalog.id}/margin-rules`);
      setCatalogRules(res.data);
    } catch (error) {
      toast.error("Error al cargar reglas");
    }
    setShowRulesDialog(true);
  };

  const openCategories = (catalog) => {
    setSelectedCatalog(catalog);
    setShowCategoriesDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("El nombre es obligatorio");
      return;
    }

    setSaving(true);
    try {
      if (selectedCatalog) {
        await api.put(`/catalogs/${selectedCatalog.id}`, formData);
        toast.success("Catálogo actualizado");
      } else {
        await api.post("/catalogs", formData);
        toast.success("Catálogo creado");
      }
      setShowDialog(false);
      resetForm();
      fetchCatalogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/catalogs/${selectedCatalog.id}`);
      toast.success("Catálogo eliminado");
      setShowDeleteDialog(false);
      fetchCatalogs();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const resetRuleForm = () => {
    setRuleForm({
      name: "",
      rule_type: "percentage",
      value: "",
      apply_to: "all",
      apply_to_value: "",
      min_price: "",
      max_price: "",
      priority: 0
    });
    setEditingRule(null);
  };

  const handleAddRule = async (e) => {
    e.preventDefault();
    if (!ruleForm.name.trim() || !ruleForm.value) {
      toast.error("Nombre y valor son obligatorios");
      return;
    }

    setSavingRule(true);
    try {
      const payload = {
        catalog_id: selectedCatalog.id,
        name: ruleForm.name,
        rule_type: ruleForm.rule_type,
        value: parseFloat(ruleForm.value),
        apply_to: ruleForm.apply_to,
        apply_to_value: ruleForm.apply_to !== "all" ? ruleForm.apply_to_value : null,
        min_price: ruleForm.min_price ? parseFloat(ruleForm.min_price) : null,
        max_price: ruleForm.max_price ? parseFloat(ruleForm.max_price) : null,
        priority: parseInt(ruleForm.priority) || 0
      };

      if (editingRule) {
        await api.put(`/catalogs/${selectedCatalog.id}/margin-rules/${editingRule.id}`, payload);
        toast.success("Regla actualizada");
      } else {
        await api.post(`/catalogs/${selectedCatalog.id}/margin-rules`, payload);
        toast.success("Regla añadida");
      }
      
      const res = await api.get(`/catalogs/${selectedCatalog.id}/margin-rules`);
      setCatalogRules(res.data);
      resetRuleForm();
      fetchCatalogs(); // Update margin_rules_count
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar regla");
    } finally {
      setSavingRule(false);
    }
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      name: rule.name,
      rule_type: rule.rule_type,
      value: rule.value.toString(),
      apply_to: rule.apply_to,
      apply_to_value: rule.apply_to_value || "",
      min_price: rule.min_price?.toString() || "",
      max_price: rule.max_price?.toString() || "",
      priority: rule.priority
    });
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await api.delete(`/catalogs/${selectedCatalog.id}/margin-rules/${ruleId}`);
      toast.success("Regla eliminada");
      setCatalogRules(catalogRules.filter(r => r.id !== ruleId));
      fetchCatalogs(); // Update margin_rules_count
    } catch (error) {
      toast.error("Error al eliminar regla");
    }
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Catálogos
          </h1>
          <p className="text-slate-500">
            Crea y gestiona diferentes catálogos con reglas de margen independientes
          </p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowDialog(true); }} 
          className="btn-primary"
          data-testid="add-catalog-btn"
        >
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Nuevo Catálogo
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Catálogos</p>
                <p className="text-2xl font-bold text-slate-900">{catalogs.length}</p>
              </div>
              <BookOpen className="w-8 h-8 text-indigo-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Total Productos</p>
                <p className="text-2xl font-bold text-emerald-700">
                  {catalogs.reduce((sum, c) => sum + c.product_count, 0)}
                </p>
              </div>
              <Package className="w-8 h-8 text-emerald-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Reglas de Margen</p>
                <p className="text-2xl font-bold text-slate-900">
                  {catalogs.reduce((sum, c) => sum + c.margin_rules_count, 0)}
                </p>
              </div>
              <Percent className="w-8 h-8 text-slate-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">Por Defecto</p>
                <p className="text-lg font-bold text-amber-700 truncate">
                  {catalogs.find(c => c.is_default)?.name || "Ninguno"}
                </p>
              </div>
              <Star className="w-8 h-8 text-amber-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Catalogs Grid */}
      {catalogs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <BookOpen className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay catálogos
          </h3>
          <p className="text-slate-500 mb-4">
            Crea tu primer catálogo para organizar tus productos y configurar reglas de margen
          </p>
          <Button onClick={() => { resetForm(); setShowDialog(true); }} className="btn-primary">
            <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Crear Catálogo
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {catalogs.map((catalog) => (
            <Card 
              key={catalog.id} 
              className={`border-slate-200 hover:shadow-md transition-shadow ${catalog.is_default ? 'ring-2 ring-indigo-500' : ''}`}
              data-testid={`catalog-card-${catalog.id}`}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                      <BookOpen className="w-5 h-5 text-indigo-600" strokeWidth={1.5} />
                    </div>
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        {catalog.name}
                        {catalog.is_default && (
                          <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">
                            <Star className="w-3 h-3 mr-1" />
                            Defecto
                          </Badge>
                        )}
                      </CardTitle>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => navigate(`/catalogs/${catalog.id}`)}>
                        <Eye className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Ver Productos
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openRules(catalog)}>
                        <Percent className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Reglas de Margen
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openCategories(catalog)}>
                        <FolderTree className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Categorías
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openEdit(catalog)}>
                        <Pencil className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => openDelete(catalog)}
                        className="text-rose-600 focus:text-rose-600"
                      >
                        <Trash2 className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                {catalog.description && (
                  <p className="text-sm text-slate-500 mb-3 line-clamp-2">{catalog.description}</p>
                )}
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-xl font-bold text-slate-900">{catalog.product_count}</p>
                    <p className="text-xs text-slate-500">Productos</p>
                  </div>
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-xl font-bold text-slate-900">{catalog.categories_count || 0}</p>
                    <p className="text-xs text-slate-500">Categorías</p>
                  </div>
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-xl font-bold text-slate-900">{catalog.margin_rules_count}</p>
                    <p className="text-xs text-slate-500">Reglas</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full"
                    onClick={() => navigate(`/catalogs/${catalog.id}`)}
                  >
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    Ver
                  </Button>
                  <Button 
                    variant="outline"
                    size="sm" 
                    className="w-full"
                    onClick={() => openCategories(catalog)}
                  >
                    <FolderTree className="w-3.5 h-3.5 mr-1" />
                    Cats.
                  </Button>
                  <Button 
                    size="sm" 
                    className="w-full btn-primary"
                    onClick={() => openRules(catalog)}
                  >
                    <Percent className="w-3.5 h-3.5 mr-1" />
                    Márg.
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <BookOpen className="w-5 h-5 text-indigo-600" />
              {selectedCatalog ? "Editar Catálogo" : "Nuevo Catálogo"}
            </DialogTitle>
            <DialogDescription>
              Los catálogos te permiten organizar productos y aplicar reglas de margen independientes
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre del catálogo *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ej: Tienda Online, Amazon, Outlet..."
                className="input-base"
                data-testid="catalog-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="description">Descripción</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Descripción opcional del catálogo"
                className="input-base min-h-[80px]"
              />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">Catálogo por defecto</p>
                <p className="text-sm text-slate-500">Se usará para exportaciones automáticas</p>
              </div>
              <Switch
                checked={formData.is_default}
                onCheckedChange={(checked) => setFormData({ ...formData, is_default: checked })}
              />
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="catalog-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : selectedCatalog ? "Guardar" : "Crear"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Margin Rules Dialog */}
      <Dialog open={showRulesDialog} onOpenChange={(open) => { setShowRulesDialog(open); if (!open) resetRuleForm(); }}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Percent className="w-5 h-5 text-indigo-600" />
              Reglas de Margen - {selectedCatalog?.name}
            </DialogTitle>
            <DialogDescription>
              Configura los márgenes de beneficio para este catálogo. Las reglas se aplican por prioridad (mayor número = mayor prioridad).
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {/* Add/Edit Rule Form */}
            <Card className={`border-2 ${editingRule ? 'border-amber-300 bg-amber-50' : 'border-indigo-200 bg-indigo-50'}`}>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  {editingRule ? (
                    <>
                      <Pencil className="w-4 h-4 text-amber-600" />
                      Editando: {editingRule.name}
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 text-indigo-600" />
                      Nueva Regla de Margen
                    </>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-2">
                <form onSubmit={handleAddRule} className="space-y-4">
                  {/* Row 1: Name and Type */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Nombre de la regla *</Label>
                      <Input
                        value={ruleForm.name}
                        onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                        placeholder="Ej: Margen general 30%"
                        className="input-base h-9"
                        data-testid="rule-name-input"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Tipo de margen</Label>
                      <Select value={ruleForm.rule_type} onValueChange={(v) => setRuleForm({ ...ruleForm, rule_type: v })}>
                        <SelectTrigger className="input-base h-9" data-testid="rule-type-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="percentage">Porcentaje (%)</SelectItem>
                          <SelectItem value="fixed">Cantidad fija (€)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  {/* Row 2: Value, Apply To, Priority */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Valor *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={ruleForm.value}
                        onChange={(e) => setRuleForm({ ...ruleForm, value: e.target.value })}
                        placeholder={ruleForm.rule_type === 'percentage' ? '30' : '10.00'}
                        className="input-base h-9 font-mono"
                        data-testid="rule-value-input"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Aplicar a</Label>
                      <Select 
                        value={ruleForm.apply_to} 
                        onValueChange={(v) => setRuleForm({ ...ruleForm, apply_to: v, apply_to_value: "" })}
                      >
                        <SelectTrigger className="input-base h-9" data-testid="rule-apply-to-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Todos los productos</SelectItem>
                          <SelectItem value="category">Por categoría</SelectItem>
                          <SelectItem value="supplier">Por proveedor</SelectItem>
                          <SelectItem value="brand">Por marca</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Prioridad</Label>
                      <Input
                        type="number"
                        value={ruleForm.priority}
                        onChange={(e) => setRuleForm({ ...ruleForm, priority: e.target.value })}
                        placeholder="0"
                        className="input-base h-9 font-mono"
                        data-testid="rule-priority-input"
                      />
                      <p className="text-[10px] text-slate-500">Mayor = más prioridad</p>
                    </div>
                  </div>
                  
                  {/* Row 3: Conditional Apply To Value */}
                  {ruleForm.apply_to === 'category' && (
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Categoría</Label>
                      {categories.length > 0 ? (
                        <Select 
                          value={ruleForm.apply_to_value} 
                          onValueChange={(v) => setRuleForm({ ...ruleForm, apply_to_value: v })}
                        >
                          <SelectTrigger className="input-base h-9" data-testid="rule-category-select">
                            <SelectValue placeholder="Seleccionar categoría" />
                          </SelectTrigger>
                          <SelectContent>
                            {categories.filter(Boolean).map((cat) => (
                              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          value={ruleForm.apply_to_value}
                          onChange={(e) => setRuleForm({ ...ruleForm, apply_to_value: e.target.value })}
                          placeholder="Nombre de la categoría"
                          className="input-base h-9"
                        />
                      )}
                    </div>
                  )}
                  
                  {ruleForm.apply_to === 'supplier' && (
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Proveedor</Label>
                      {suppliers.length > 0 ? (
                        <Select 
                          value={ruleForm.apply_to_value} 
                          onValueChange={(v) => setRuleForm({ ...ruleForm, apply_to_value: v })}
                        >
                          <SelectTrigger className="input-base h-9" data-testid="rule-supplier-select">
                            <SelectValue placeholder="Seleccionar proveedor" />
                          </SelectTrigger>
                          <SelectContent>
                            {suppliers.map((sup) => (
                              <SelectItem key={sup.id} value={sup.id}>{sup.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          value={ruleForm.apply_to_value}
                          onChange={(e) => setRuleForm({ ...ruleForm, apply_to_value: e.target.value })}
                          placeholder="ID del proveedor"
                          className="input-base h-9"
                        />
                      )}
                    </div>
                  )}
                  
                  {ruleForm.apply_to === 'brand' && (
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Marca</Label>
                      <Input
                        value={ruleForm.apply_to_value}
                        onChange={(e) => setRuleForm({ ...ruleForm, apply_to_value: e.target.value })}
                        placeholder="Nombre de la marca"
                        className="input-base h-9"
                      />
                    </div>
                  )}
                  
                  {/* Row 4: Price Range */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Precio mínimo (€)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={ruleForm.min_price}
                        onChange={(e) => setRuleForm({ ...ruleForm, min_price: e.target.value })}
                        placeholder="0.00 (sin límite)"
                        className="input-base h-9 font-mono"
                        data-testid="rule-min-price"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Precio máximo (€)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={ruleForm.max_price}
                        onChange={(e) => setRuleForm({ ...ruleForm, max_price: e.target.value })}
                        placeholder="Sin límite"
                        className="input-base h-9 font-mono"
                        data-testid="rule-max-price"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 -mt-2">
                    Deja vacío para aplicar a cualquier precio. Usa tramos para aplicar diferentes márgenes según el precio base del producto.
                  </p>
                  
                  {/* Buttons */}
                  <div className="flex gap-2 pt-2">
                    {editingRule && (
                      <Button 
                        type="button" 
                        variant="outline" 
                        size="sm" 
                        onClick={resetRuleForm}
                        className="flex-1"
                      >
                        Cancelar Edición
                      </Button>
                    )}
                    <Button 
                      type="submit" 
                      size="sm" 
                      className={`flex-1 ${editingRule ? 'bg-amber-600 hover:bg-amber-700' : 'btn-primary'}`}
                      disabled={savingRule}
                      data-testid="rule-submit-btn"
                    >
                      {savingRule ? (
                        <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                      ) : editingRule ? (
                        <Pencil className="w-4 h-4 mr-1" />
                      ) : (
                        <Plus className="w-4 h-4 mr-1" />
                      )}
                      {editingRule ? 'Guardar Cambios' : 'Añadir Regla'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Rules List */}
            {catalogRules.length === 0 ? (
              <div className="text-center py-8 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
                <Percent className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-600 font-medium mb-1">No hay reglas configuradas</p>
                <p className="text-slate-500 text-sm">Añade tu primera regla de margen para este catálogo</p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between px-1 pb-2">
                  <p className="text-sm font-medium text-slate-700">
                    {catalogRules.length} regla{catalogRules.length !== 1 ? 's' : ''} configurada{catalogRules.length !== 1 ? 's' : ''}
                  </p>
                  <Badge variant="secondary" className="bg-slate-100">
                    Ordenadas por prioridad
                  </Badge>
                </div>
                {catalogRules.map((rule) => (
                  <div 
                    key={rule.id} 
                    className={`flex items-center justify-between p-3 bg-white border rounded-lg hover:shadow-sm transition-shadow ${editingRule?.id === rule.id ? 'ring-2 ring-amber-400' : ''}`}
                    data-testid={`rule-item-${rule.id}`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-indigo-600 font-bold text-sm">
                          {rule.rule_type === 'percentage' ? `${rule.value}%` : `${rule.value}€`}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">{rule.name}</p>
                        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            {rule.apply_to === 'all' ? 'Todos' : 
                              rule.apply_to === 'category' ? `Cat: ${rule.apply_to_value}` :
                              rule.apply_to === 'supplier' ? `Prov: ${suppliers.find(s => s.id === rule.apply_to_value)?.name || rule.apply_to_value}` :
                              `Marca: ${rule.apply_to_value}`
                            }
                          </span>
                          {(rule.min_price || rule.max_price) && (
                            <span className="flex items-center gap-1 font-mono">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                              {rule.min_price ? `${rule.min_price}€` : '0€'} - {rule.max_price ? `${rule.max_price}€` : '∞'}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                            P: {rule.priority}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 ml-2">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8"
                        onClick={() => handleEditRule(rule)}
                        data-testid={`edit-rule-${rule.id}`}
                      >
                        <Pencil className="w-4 h-4 text-slate-500" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 hover:bg-rose-50"
                        onClick={() => handleDeleteRule(rule.id)}
                        data-testid={`delete-rule-${rule.id}`}
                      >
                        <Trash2 className="w-4 h-4 text-rose-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <DialogFooter className="pt-4 border-t">
            <Button variant="outline" onClick={() => { setShowRulesDialog(false); resetRuleForm(); }}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar catálogo?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminarán todos los productos y reglas de margen de "{selectedCatalog?.name}". Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700 text-white">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Categories Dialog */}
      <Dialog open={showCategoriesDialog} onOpenChange={(open) => { setShowCategoriesDialog(open); if (!open) fetchCatalogs(); }}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <FolderTree className="w-5 h-5 text-indigo-600" />
              Categorías - {selectedCatalog?.name}
            </DialogTitle>
            <DialogDescription>
              Organiza los productos del catálogo en categorías y subcategorías (máximo 4 niveles)
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto">
            {selectedCatalog && (
              <CatalogCategories 
                catalogId={selectedCatalog.id} 
                catalogName={selectedCatalog.name}
                onClose={() => setShowCategoriesDialog(false)}
                stores={stores}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Catalogs;
