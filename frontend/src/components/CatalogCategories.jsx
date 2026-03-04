import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  FolderTree,
  Plus,
  Pencil,
  Trash2,
  ChevronRight,
  ChevronDown,
  MoreVertical,
  GripVertical,
  FolderPlus,
  RefreshCw
} from "lucide-react";

const CatalogCategories = ({ catalogId, catalogName, onClose }) => {
  const [categories, setCategories] = useState([]);
  const [flatCategories, setFlatCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [parentCategory, setParentCategory] = useState(null);
  const [expandedIds, setExpandedIds] = useState([]);
  const [formData, setFormData] = useState({ name: "", description: "", parent_id: "" });
  const [saving, setSaving] = useState(false);

  const fetchCategories = useCallback(async () => {
    try {
      const [treeRes, flatRes] = await Promise.all([
        api.get(`/catalogs/${catalogId}/categories`),
        api.get(`/catalogs/${catalogId}/categories?flat=true`)
      ]);
      setCategories(treeRes.data);
      setFlatCategories(flatRes.data);
      setExpandedIds(flatRes.data.map(c => c.id));
    } catch (error) {
      toast.error("Error al cargar categorías");
    } finally {
      setLoading(false);
    }
  }, [catalogId]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const toggleExpand = (id) => {
    setExpandedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const resetForm = () => {
    setFormData({ name: "", description: "", parent_id: "" });
    setSelectedCategory(null);
    setParentCategory(null);
  };

  const openCreate = (parent = null) => {
    resetForm();
    setParentCategory(parent);
    if (parent) {
      setFormData(prev => ({ ...prev, parent_id: parent.id }));
    }
    setShowDialog(true);
  };

  const openEdit = (category) => {
    setSelectedCategory(category);
    setFormData({
      name: category.name,
      description: category.description || "",
      parent_id: category.parent_id || ""
    });
    setShowDialog(true);
  };

  const openDelete = (category) => {
    setSelectedCategory(category);
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
      const payload = {
        name: formData.name,
        description: formData.description || null,
        parent_id: formData.parent_id || null
      };

      if (selectedCategory) {
        await api.put(`/catalogs/${catalogId}/categories/${selectedCategory.id}`, payload);
        toast.success("Categoría actualizada");
      } else {
        await api.post(`/catalogs/${catalogId}/categories`, payload);
        toast.success("Categoría creada");
      }
      setShowDialog(false);
      resetForm();
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/catalogs/${catalogId}/categories/${selectedCategory.id}`);
      toast.success("Categoría eliminada");
      setShowDeleteDialog(false);
      fetchCategories();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleMoveUp = async (category) => {
    const siblings = flatCategories.filter(c => c.parent_id === category.parent_id);
    const currentIndex = siblings.findIndex(c => c.id === category.id);
    if (currentIndex <= 0) return;
    
    const newPosition = siblings[currentIndex - 1].position;
    try {
      await api.post(`/catalogs/${catalogId}/categories/reorder`, {
        updates: [
          { category_id: category.id, new_parent_id: category.parent_id, new_position: newPosition },
          { category_id: siblings[currentIndex - 1].id, new_parent_id: category.parent_id, new_position: category.position }
        ]
      });
      fetchCategories();
    } catch (error) {
      toast.error("Error al reordenar");
    }
  };

  const handleMoveDown = async (category) => {
    const siblings = flatCategories.filter(c => c.parent_id === category.parent_id);
    const currentIndex = siblings.findIndex(c => c.id === category.id);
    if (currentIndex >= siblings.length - 1) return;
    
    const newPosition = siblings[currentIndex + 1].position;
    try {
      await api.post(`/catalogs/${catalogId}/categories/reorder`, {
        updates: [
          { category_id: category.id, new_parent_id: category.parent_id, new_position: newPosition },
          { category_id: siblings[currentIndex + 1].id, new_parent_id: category.parent_id, new_position: category.position }
        ]
      });
      fetchCategories();
    } catch (error) {
      toast.error("Error al reordenar");
    }
  };

  const getAvailableParents = () => {
    if (!selectedCategory) return flatCategories.filter(c => c.level < 3);
    
    const getDescendants = (catId) => {
      const descendants = [];
      flatCategories.forEach(c => {
        if (c.parent_id === catId) {
          descendants.push(c.id);
          descendants.push(...getDescendants(c.id));
        }
      });
      return descendants;
    };
    
    const descendants = getDescendants(selectedCategory.id);
    return flatCategories.filter(c => 
      c.id !== selectedCategory.id && 
      !descendants.includes(c.id) &&
      c.level < 3
    );
  };

  // Render a single category item
  const renderCategoryItem = (category, level = 0) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expandedIds.includes(category.id);
    const canAddChild = level < 3;
    
    return (
      <div key={category.id} className="category-item">
        <div 
          className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 transition-colors group"
          style={{ marginLeft: `${level * 24}px` }}
        >
          <button 
            onClick={() => toggleExpand(category.id)}
            className={`w-6 h-6 flex items-center justify-center rounded hover:bg-slate-200 ${!hasChildren ? 'invisible' : ''}`}
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-slate-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-500" />
            )}
          </button>
          
          <GripVertical className="w-4 h-4 text-slate-300 cursor-grab opacity-0 group-hover:opacity-100 transition-opacity" />
          
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <FolderTree className="w-4 h-4 text-indigo-500 flex-shrink-0" />
            <span className="font-medium text-slate-800 truncate">{category.name}</span>
            {category.product_count > 0 && (
              <Badge variant="secondary" className="bg-slate-100 text-slate-600 text-xs">
                {category.product_count} prod.
              </Badge>
            )}
            <Badge variant="outline" className="text-xs text-slate-400 border-slate-200">
              Nivel {level + 1}
            </Badge>
          </div>
          
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {canAddChild && (
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-7 w-7"
                onClick={() => openCreate(category)}
                title="Añadir subcategoría"
              >
                <FolderPlus className="w-4 h-4 text-indigo-500" />
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => openEdit(category)}>
                  <Pencil className="w-4 h-4 mr-2" />
                  Editar
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleMoveUp(category)}>
                  <ChevronRight className="w-4 h-4 mr-2 rotate-[-90deg]" />
                  Subir
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleMoveDown(category)}>
                  <ChevronRight className="w-4 h-4 mr-2 rotate-90" />
                  Bajar
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => openDelete(category)}
                  className="text-rose-600 focus:text-rose-600"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Eliminar
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="children">
            {category.children.map((child) => renderCategoryItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Categorías del Catálogo
          </h3>
          <p className="text-sm text-slate-500">
            {flatCategories.length} categoría{flatCategories.length !== 1 ? 's' : ''} • Máximo 4 niveles
          </p>
        </div>
        <Button onClick={() => openCreate()} className="btn-primary" data-testid="add-category-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Categoría
        </Button>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
          <FolderTree className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600 font-medium mb-1">No hay categorías</p>
          <p className="text-slate-500 text-sm mb-4">Crea categorías para organizar los productos de este catálogo</p>
          <Button onClick={() => openCreate()} className="btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            Crear Primera Categoría
          </Button>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-4">
            {categories.map((category) => renderCategoryItem(category, 0))}
          </CardContent>
        </Card>
      )}

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <FolderTree className="w-5 h-5 text-indigo-600" />
              {selectedCategory ? "Editar Categoría" : parentCategory ? `Nueva Subcategoría de "${parentCategory.name}"` : "Nueva Categoría"}
            </DialogTitle>
            <DialogDescription>
              {parentCategory ? `Se creará como subcategoría de "${parentCategory.name}"` : "Las categorías organizan los productos del catálogo"}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cat-name">Nombre *</Label>
              <Input
                id="cat-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ej: Electrónica, Ropa, Accesorios..."
                className="input-base"
                data-testid="category-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="cat-desc">Descripción (opcional)</Label>
              <Input
                id="cat-desc"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Descripción de la categoría"
                className="input-base"
              />
            </div>
            
            {!parentCategory && (
              <div className="space-y-2">
                <Label>Categoría padre (opcional)</Label>
                <Select 
                  value={formData.parent_id || "none"} 
                  onValueChange={(v) => setFormData({ ...formData, parent_id: v === "none" ? "" : v })}
                >
                  <SelectTrigger className="input-base">
                    <SelectValue placeholder="Sin categoría padre (nivel raíz)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin categoría padre</SelectItem>
                    {getAvailableParents().map((cat) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {"—".repeat(cat.level)} {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="category-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : selectedCategory ? "Guardar" : "Crear"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar categoría?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará "{selectedCategory?.name}" y todas sus subcategorías. Los productos asignados perderán esta categoría.
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

export default CatalogCategories;
