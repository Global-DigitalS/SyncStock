import { useState } from "react";
import { api } from "../../App";
import { toast } from "sonner";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Package, Save, Pencil, Star, Truck } from "lucide-react";
import StockBadge from "../shared/StockBadge";

const ProductDetailDialog = ({
  open,
  onOpenChange,
  product,
  onProductUpdate
}) => {
  const [activeTab, setActiveTab] = useState("proveedores");
  const [editForm, setEditForm] = useState({});
  const [savingProduct, setSavingProduct] = useState(false);

  const handleOpenChange = (isOpen) => {
    if (!isOpen) {
      setEditForm({});
      setActiveTab("proveedores");
    }
    onOpenChange(isOpen);
  };

  const handleSaveProduct = async () => {
    if (!product) return;
    
    setSavingProduct(true);
    try {
      const updateData = { ...editForm };
      
      // Clean up undefined/empty values
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === "" || updateData[key] === undefined) {
          delete updateData[key];
        }
      });

      await api.put(`/products/${product.id}`, updateData);
      toast.success("Producto actualizado correctamente");
      
      if (onProductUpdate) {
        onProductUpdate();
      }
      handleOpenChange(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar producto");
    } finally {
      setSavingProduct(false);
    }
  };

  if (!product) return null;

  // Check if this is a unified product (has suppliers array)
  const isUnified = product.suppliers && Array.isArray(product.suppliers);
  const hasChanges = Object.keys(editForm).length > 0;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Package className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <span className="block">{product.name}</span>
              <span className="text-sm font-normal text-slate-500">SKU: {product.sku}</span>
            </div>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="proveedores" className="flex items-center gap-2">
              <Truck className="w-4 h-4" />
              {isUnified ? "Proveedores" : "Información"}
            </TabsTrigger>
            <TabsTrigger value="editar" className="flex items-center gap-2">
              <Pencil className="w-4 h-4" />
              Editar Datos
            </TabsTrigger>
          </TabsList>

          {/* Tab: Proveedores / Info */}
          <TabsContent value="proveedores" className="mt-4">
            {isUnified ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-600">
                    {product.supplier_count} proveedores disponibles
                  </span>
                  <span className="text-sm text-slate-600">
                    Stock total: <strong>{product.total_stock}</strong>
                  </span>
                </div>
                {product.suppliers.map((supplier, idx) => (
                  <div 
                    key={idx}
                    className={`p-4 rounded-lg border transition-colors ${
                      supplier.is_best_offer 
                        ? "border-emerald-200 bg-emerald-50" 
                        : "border-slate-200 bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {supplier.is_best_offer && (
                          <Star className="w-5 h-5 text-emerald-500 fill-emerald-500" />
                        )}
                        <div>
                          <p className="font-medium text-slate-900">{supplier.supplier_name}</p>
                          <p className="text-sm text-slate-500">SKU: {supplier.sku}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-lg font-bold ${
                          supplier.is_best_offer ? "text-emerald-600" : "text-slate-900"
                        }`}>
                          €{supplier.price.toFixed(2)}
                        </p>
                        <StockBadge stock={supplier.stock} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Precio</span>
                    <p className="text-lg font-bold text-slate-900">€{product.price?.toFixed(2)}</p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Stock</span>
                    <div className="mt-1">
                      <StockBadge stock={product.stock || 0} />
                    </div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Proveedor</span>
                    <p className="font-medium text-slate-900">{product.supplier_name}</p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">EAN</span>
                    <p className="font-medium text-slate-900">{product.ean || "-"}</p>
                  </div>
                </div>
                {product.description && (
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Descripción</span>
                    <p className="text-sm text-slate-700 mt-1">{product.description}</p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Tab: Editar */}
          <TabsContent value="editar" className="mt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nombre</Label>
                  <Input
                    value={editForm.name ?? product.name ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    placeholder="Nombre del producto"
                    data-testid="edit-product-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>SKU</Label>
                  <Input
                    value={editForm.sku ?? product.sku ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, sku: e.target.value })}
                    placeholder="Código SKU"
                    disabled
                  />
                </div>
                <div className="space-y-2">
                  <Label>Precio</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editForm.price ?? product.price ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, price: parseFloat(e.target.value) || 0 })}
                    placeholder="0.00"
                    data-testid="edit-product-price"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Stock</Label>
                  <Input
                    type="number"
                    value={editForm.stock ?? product.stock ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, stock: parseInt(e.target.value) || 0 })}
                    placeholder="0"
                    data-testid="edit-product-stock"
                  />
                </div>
                <div className="space-y-2">
                  <Label>EAN/Código de barras</Label>
                  <Input
                    value={editForm.ean ?? product.ean ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, ean: e.target.value })}
                    placeholder="EAN13"
                    data-testid="edit-product-ean"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Marca</Label>
                  <Input
                    value={editForm.brand ?? product.brand ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, brand: e.target.value })}
                    placeholder="Marca"
                    data-testid="edit-product-brand"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Categoría</Label>
                  <Input
                    value={editForm.category ?? product.category ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    placeholder="Categoría"
                    data-testid="edit-product-category"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Peso (kg)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editForm.weight ?? product.weight ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, weight: parseFloat(e.target.value) || 0 })}
                    placeholder="0.00"
                    data-testid="edit-product-weight"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Descripción</Label>
                <textarea
                  className="input-base min-h-[80px] w-full"
                  value={editForm.description ?? product.description ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="Descripción del producto"
                  data-testid="edit-product-description"
                />
              </div>

              <div className="space-y-2">
                <Label>URL de imagen</Label>
                <Input
                  value={editForm.image_url ?? product.image_url ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, image_url: e.target.value })}
                  placeholder="https://..."
                  data-testid="edit-product-image"
                />
              </div>

              {/* Extended fields toggles */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <Label>Activado</Label>
                  <Switch
                    checked={editForm.activado ?? product.activado ?? true}
                    onCheckedChange={(v) => setEditForm({ ...editForm, activado: v })}
                    data-testid="edit-product-activado"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Requiere envío</Label>
                  <Switch
                    checked={editForm.requiere_envio ?? product.requiere_envio ?? true}
                    onCheckedChange={(v) => setEditForm({ ...editForm, requiere_envio: v })}
                    data-testid="edit-product-envio"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Envío gratis</Label>
                  <Switch
                    checked={editForm.envio_gratis ?? product.envio_gratis ?? false}
                    onCheckedChange={(v) => setEditForm({ ...editForm, envio_gratis: v })}
                    data-testid="edit-product-envio-gratis"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Vender sin stock</Label>
                  <Switch
                    checked={editForm.vender_sin_stock ?? product.vender_sin_stock ?? false}
                    onCheckedChange={(v) => setEditForm({ ...editForm, vender_sin_stock: v })}
                    data-testid="edit-product-vender-sin-stock"
                  />
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cerrar
          </Button>
          {activeTab === "editar" && hasChanges && (
            <Button 
              className="btn-primary"
              onClick={handleSaveProduct}
              disabled={savingProduct}
              data-testid="save-product-btn"
            >
              {savingProduct ? (
                <>
                  <div className="spinner mr-2" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Guardar Cambios
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ProductDetailDialog;
