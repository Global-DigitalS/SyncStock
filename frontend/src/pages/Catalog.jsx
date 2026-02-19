import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
  BookOpen,
  Search,
  Package,
  Pencil,
  Trash2,
  ArrowRight,
  Filter,
  Download,
  RefreshCw,
  Truck,
  TrendingUp
} from "lucide-react";

const Catalog = () => {
  const [catalogItems, setCatalogItems] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [editForm, setEditForm] = useState({
    custom_price: "",
    custom_name: "",
    active: true
  });
  const [saving, setSaving] = useState(false);
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0, totalValue: 0 });

  const fetchData = useCallback(async () => {
    try {
      const [catalogRes, suppliersRes] = await Promise.all([
        api.get("/catalog"),
        api.get("/suppliers")
      ]);
      setCatalogItems(catalogRes.data);
      setSuppliers(suppliersRes.data);
      
      // Calculate stats
      const items = catalogRes.data;
      setStats({
        total: items.length,
        active: items.filter(i => i.active).length,
        inactive: items.filter(i => !i.active).length,
        totalValue: items.filter(i => i.active).reduce((sum, i) => sum + (i.final_price * (i.product?.stock || 0)), 0)
      });
    } catch (error) {
      toast.error("Error al cargar el catálogo");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredItems = catalogItems.filter(item => {
    // Search filter
    if (search) {
      const searchLower = search.toLowerCase();
      const name = (item.custom_name || item.product?.name || "").toLowerCase();
      const sku = (item.product?.sku || "").toLowerCase();
      if (!name.includes(searchLower) && !sku.includes(searchLower)) {
        return false;
      }
    }
    // Supplier filter
    if (supplierFilter !== "all" && item.product?.supplier_id !== supplierFilter) {
      return false;
    }
    // Status filter
    if (statusFilter === "active" && !item.active) return false;
    if (statusFilter === "inactive" && item.active) return false;
    
    return true;
  });

  const openEdit = (item) => {
    setSelectedItem(item);
    setEditForm({
      custom_price: item.custom_price || "",
      custom_name: item.custom_name || "",
      active: item.active
    });
    setShowEditDialog(true);
  };

  const openDelete = (item) => {
    setSelectedItem(item);
    setShowDeleteDialog(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/catalog/${selectedItem.id}`, {
        product_id: selectedItem.product_id,
        custom_price: editForm.custom_price ? parseFloat(editForm.custom_price) : null,
        custom_name: editForm.custom_name || null,
        active: editForm.active
      });
      toast.success("Producto actualizado");
      setShowEditDialog(false);
      fetchCatalog();
    } catch (error) {
      toast.error("Error al guardar los cambios");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/catalog/${selectedItem.id}`);
      toast.success("Producto eliminado del catálogo");
      setShowDeleteDialog(false);
      fetchCatalog();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleToggleActive = async (item) => {
    try {
      await api.put(`/catalog/${item.id}`, {
        product_id: item.product_id,
        custom_price: item.custom_price,
        custom_name: item.custom_name,
        active: !item.active
      });
      fetchCatalog();
    } catch (error) {
      toast.error("Error al cambiar el estado");
    }
  };

  const getStockBadge = (stock) => {
    if (stock === 0) return <span className="badge-error">Sin stock</span>;
    if (stock <= 5) return <span className="badge-warning">{stock} uds</span>;
    return <span className="badge-success">{stock} uds</span>;
  };

  if (loading && catalogItems.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Mi Catálogo
        </h1>
        <p className="text-slate-500">
          {catalogItems.length.toLocaleString()} productos en tu catálogo personalizado
        </p>
      </div>

      {/* Search */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" strokeWidth={1.5} />
              <Input
                placeholder="Buscar en mi catálogo..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-9 input-base"
                data-testid="search-catalog"
              />
            </div>
            <Button onClick={handleSearch} className="btn-secondary" data-testid="search-catalog-btn">
              Buscar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Catalog Table */}
      {catalogItems.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <BookOpen className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Tu catálogo está vacío
          </h3>
          <p className="text-slate-500 mb-4">
            Añade productos desde la sección de Productos para crear tu catálogo
          </p>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Producto</TableHead>
                  <TableHead>Proveedor</TableHead>
                  <TableHead className="text-right">Precio Original</TableHead>
                  <TableHead className="text-right">Precio Final</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-center">Activo</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {catalogItems.map((item) => (
                  <TableRow
                    key={item.id}
                    className={`table-row ${!item.active ? "opacity-50" : ""}`}
                    data-testid={`catalog-row-${item.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3 max-w-[300px]">
                        {item.product.image_url ? (
                          <img
                            src={item.product.image_url}
                            alt={item.product.name}
                            className="w-10 h-10 object-cover rounded-sm border border-slate-200"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-slate-100 rounded-sm flex items-center justify-center">
                            <Package className="w-5 h-5 text-slate-400" strokeWidth={1.5} />
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900 truncate">
                            {item.custom_name || item.product.name}
                          </p>
                          <p className="text-xs text-slate-500 font-mono">{item.product.sku}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-600">{item.product.supplier_name}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-sm text-slate-500">
                        {item.product.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {item.custom_price && item.custom_price !== item.product.price && (
                          <ArrowRight className="w-4 h-4 text-slate-300" strokeWidth={1.5} />
                        )}
                        <span className="font-mono font-semibold text-emerald-600">
                          {item.final_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {getStockBadge(item.product.stock)}
                    </TableCell>
                    <TableCell className="text-center">
                      <Switch
                        checked={item.active}
                        onCheckedChange={() => handleToggleActive(item)}
                        data-testid={`toggle-active-${item.id}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEdit(item)}
                          className="h-8 w-8 p-0"
                          data-testid={`edit-catalog-${item.id}`}
                        >
                          <Pencil className="w-4 h-4" strokeWidth={1.5} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDelete(item)}
                          className="h-8 w-8 p-0 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                          data-testid={`delete-catalog-${item.id}`}
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

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Editar Producto</DialogTitle>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 rounded-sm">
                <p className="font-medium text-slate-900 mb-1">{selectedItem.product.name}</p>
                <p className="text-sm text-slate-500 font-mono">{selectedItem.product.sku}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="custom_name">Nombre personalizado</Label>
                <Input
                  id="custom_name"
                  value={editForm.custom_name}
                  onChange={(e) => setEditForm({ ...editForm, custom_name: e.target.value })}
                  placeholder={selectedItem.product.name}
                  className="input-base"
                  data-testid="edit-custom-name"
                />
                <p className="text-xs text-slate-500">Deja vacío para usar el nombre original</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="custom_price">Precio personalizado (€)</Label>
                <Input
                  id="custom_price"
                  type="number"
                  step="0.01"
                  value={editForm.custom_price}
                  onChange={(e) => setEditForm({ ...editForm, custom_price: e.target.value })}
                  placeholder={selectedItem.product.price.toString()}
                  className="input-base font-mono"
                  data-testid="edit-custom-price"
                />
                <p className="text-xs text-slate-500">
                  Precio original: {selectedItem.product.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                </p>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="active">Producto activo</Label>
                <Switch
                  id="active"
                  checked={editForm.active}
                  onCheckedChange={(checked) => setEditForm({ ...editForm, active: checked })}
                  data-testid="edit-active-switch"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)} className="btn-secondary">
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={saving} className="btn-primary" data-testid="save-catalog-edit">
              Guardar Cambios
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar del catálogo?</AlertDialogTitle>
            <AlertDialogDescription>
              El producto "{selectedItem?.product.name}" será eliminado de tu catálogo. El producto seguirá disponible en la lista de productos del proveedor.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700 text-white" data-testid="confirm-delete-catalog">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Catalog;
