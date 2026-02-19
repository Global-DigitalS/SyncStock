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
  ArrowRight
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const Catalogs = () => {
  const navigate = useNavigate();
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRulesDialog, setShowRulesDialog] = useState(false);
  const [selectedCatalog, setSelectedCatalog] = useState(null);
  const [formData, setFormData] = useState({ name: "", description: "", is_default: false });
  const [saving, setSaving] = useState(false);
  
  // Rules state
  const [catalogRules, setCatalogRules] = useState([]);
  const [ruleForm, setRuleForm] = useState({
    name: "",
    rule_type: "percentage",
    value: "",
    apply_to: "all",
    apply_to_value: "",
    priority: 0
  });

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

  useEffect(() => {
    fetchCatalogs();
  }, [fetchCatalogs]);

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
    try {
      const res = await api.get(`/catalogs/${catalog.id}/margin-rules`);
      setCatalogRules(res.data);
    } catch (error) {
      toast.error("Error al cargar reglas");
    }
    setShowRulesDialog(true);
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

  const handleAddRule = async (e) => {
    e.preventDefault();
    if (!ruleForm.name.trim() || !ruleForm.value) {
      toast.error("Nombre y valor son obligatorios");
      return;
    }

    try {
      await api.post(`/catalogs/${selectedCatalog.id}/margin-rules`, {
        ...ruleForm,
        catalog_id: selectedCatalog.id,
        value: parseFloat(ruleForm.value),
        priority: parseInt(ruleForm.priority) || 0
      });
      toast.success("Regla añadida");
      const res = await api.get(`/catalogs/${selectedCatalog.id}/margin-rules`);
      setCatalogRules(res.data);
      setRuleForm({ name: "", rule_type: "percentage", value: "", apply_to: "all", apply_to_value: "", priority: 0 });
    } catch (error) {
      toast.error("Error al añadir regla");
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await api.delete(`/catalogs/${selectedCatalog.id}/margin-rules/${ruleId}`);
      toast.success("Regla eliminada");
      setCatalogRules(catalogRules.filter(r => r.id !== ruleId));
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
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-slate-900">{catalog.product_count}</p>
                    <p className="text-xs text-slate-500">Productos</p>
                  </div>
                  <div className="text-center p-2 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-slate-900">{catalog.margin_rules_count}</p>
                    <p className="text-xs text-slate-500">Reglas</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => navigate(`/catalogs/${catalog.id}`)}
                  >
                    <Eye className="w-3.5 h-3.5 mr-1.5" />
                    Ver
                  </Button>
                  <Button 
                    size="sm" 
                    className="flex-1 btn-primary"
                    onClick={() => openRules(catalog)}
                  >
                    <Percent className="w-3.5 h-3.5 mr-1.5" />
                    Márgenes
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
      <Dialog open={showRulesDialog} onOpenChange={setShowRulesDialog}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Percent className="w-5 h-5 text-indigo-600" />
              Reglas de Margen - {selectedCatalog?.name}
            </DialogTitle>
            <DialogDescription>
              Configura los márgenes de beneficio para este catálogo específico
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto space-y-4">
            {/* Add Rule Form */}
            <Card className="border-indigo-200 bg-indigo-50">
              <CardContent className="p-4">
                <form onSubmit={handleAddRule} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Nombre de la regla</Label>
                      <Input
                        value={ruleForm.name}
                        onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                        placeholder="Ej: Margen general"
                        className="input-base h-9"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Tipo</Label>
                      <Select value={ruleForm.rule_type} onValueChange={(v) => setRuleForm({ ...ruleForm, rule_type: v })}>
                        <SelectTrigger className="input-base h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="percentage">Porcentaje (%)</SelectItem>
                          <SelectItem value="fixed">Cantidad fija (€)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Valor</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={ruleForm.value}
                        onChange={(e) => setRuleForm({ ...ruleForm, value: e.target.value })}
                        placeholder={ruleForm.rule_type === 'percentage' ? '15' : '5.00'}
                        className="input-base h-9"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Aplicar a</Label>
                      <Select value={ruleForm.apply_to} onValueChange={(v) => setRuleForm({ ...ruleForm, apply_to: v })}>
                        <SelectTrigger className="input-base h-9">
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
                    <div className="space-y-1">
                      <Label className="text-xs">Prioridad</Label>
                      <Input
                        type="number"
                        value={ruleForm.priority}
                        onChange={(e) => setRuleForm({ ...ruleForm, priority: e.target.value })}
                        placeholder="0"
                        className="input-base h-9"
                      />
                    </div>
                  </div>
                  {ruleForm.apply_to !== 'all' && (
                    <div className="space-y-1">
                      <Label className="text-xs">
                        {ruleForm.apply_to === 'category' ? 'Categoría' : ruleForm.apply_to === 'supplier' ? 'Proveedor' : 'Marca'}
                      </Label>
                      <Input
                        value={ruleForm.apply_to_value}
                        onChange={(e) => setRuleForm({ ...ruleForm, apply_to_value: e.target.value })}
                        placeholder={`Nombre de ${ruleForm.apply_to === 'category' ? 'la categoría' : ruleForm.apply_to === 'supplier' ? 'el proveedor' : 'la marca'}`}
                        className="input-base h-9"
                      />
                    </div>
                  )}
                  <Button type="submit" size="sm" className="btn-primary w-full">
                    <Plus className="w-4 h-4 mr-1" />
                    Añadir Regla
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Rules List */}
            {catalogRules.length === 0 ? (
              <div className="text-center py-6">
                <Percent className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">No hay reglas configuradas para este catálogo</p>
              </div>
            ) : (
              <div className="space-y-2">
                {catalogRules.map((rule) => (
                  <div key={rule.id} className="flex items-center justify-between p-3 bg-white border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                        <Percent className="w-4 h-4 text-indigo-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{rule.name}</p>
                        <p className="text-xs text-slate-500">
                          {rule.rule_type === 'percentage' ? `+${rule.value}%` : `+${rule.value}€`}
                          {rule.apply_to !== 'all' && ` • ${rule.apply_to}: ${rule.apply_to_value}`}
                          {` • Prioridad: ${rule.priority}`}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => handleDeleteRule(rule.id)}>
                      <Trash2 className="w-4 h-4 text-rose-500" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <DialogFooter className="pt-4 border-t">
            <Button variant="outline" onClick={() => setShowRulesDialog(false)}>
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
    </div>
  );
};

export default Catalogs;
