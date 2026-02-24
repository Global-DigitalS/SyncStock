import { useState, useEffect } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import {
  Package, Eye, BookOpen, Star, RefreshCw, Truck, Save, Pencil, AlertTriangle
} from "lucide-react";

// Toggle field component for switches
export const ToggleField = ({ label, value, onChange, testId }) => (
  <div className="space-y-1">
    <Label className="text-xs text-slate-500">{label}</Label>
    <div className="flex rounded-lg border border-slate-200 overflow-hidden h-9">
      <button type="button" onClick={() => onChange(false)}
        className={`flex-1 text-xs font-medium transition-colors ${!value ? "bg-slate-200 text-slate-700" : "bg-white text-slate-400 hover:bg-slate-50"}`}
        data-testid={testId ? `${testId}-no` : undefined}>
        No
      </button>
      <button type="button" onClick={() => onChange(true)}
        className={`flex-1 text-xs font-medium transition-colors ${value ? "bg-emerald-500 text-white" : "bg-white text-slate-400 hover:bg-slate-50"}`}
        data-testid={testId ? `${testId}-si` : undefined}>
        Sí
      </button>
    </div>
  </div>
);

// Product detail dialog component
const ProductDetailDialog = ({
  open,
  onOpenChange,
  product,
  onAddToCatalog,
  onSave
}) => {
  const [activeTab, setActiveTab] = useState("proveedores");
  const [editForm, setEditForm] = useState({});
  const [savingProduct, setSavingProduct] = useState(false);

  useEffect(() => {
    if (product && open) {
      loadProductData();
    }
  }, [product, open]);

  const loadProductData = async () => {
    if (!product) return;
    const bestOffer = product.suppliers.find(s => s.is_best_offer);
    if (bestOffer) {
      try {
        const res = await api.get(`/products/${bestOffer.product_id}`);
        const p = res.data;
        setEditForm({
          name: p.name || "", ean: p.ean || "", sku: p.sku || "",
          description: p.description || "", price: p.price || 0,
          stock: p.stock || 0, category: p.category || "",
          brand: p.brand || "", weight: p.weight || 0,
          image_url: p.image_url || "",
          referencia: p.referencia || "", part_number: p.part_number || "",
          asin: p.asin || "", upc: p.upc || "", gtin: p.gtin || p.ean || "",
          oem: p.oem || "", id_erp: p.id_erp || "",
          activado: p.activado !== false, descatalogado: p.descatalogado || false,
          condicion: p.condicion || "", activar_pos: p.activar_pos || false,
          tipo_pack: p.tipo_pack || false, vender_sin_stock: p.vender_sin_stock || false,
          nuevo: p.nuevo || "", fecha_disponibilidad: p.fecha_disponibilidad || "",
          stock_disponible: p.stock_disponible ?? p.stock ?? 0,
          stock_fantasma: p.stock_fantasma ?? 0, stock_market: p.stock_market ?? 0,
          unid_caja: p.unid_caja ?? 0, cantidad_minima: p.cantidad_minima ?? 0,
          dias_entrega: p.dias_entrega ?? 0, cantidad_maxima_carrito: p.cantidad_maxima_carrito ?? 0,
          resto_stock: p.resto_stock !== false, requiere_envio: p.requiere_envio !== false,
          envio_gratis: p.envio_gratis || false, gastos_envio: p.gastos_envio ?? 0,
          largo: p.largo ?? 0, ancho: p.ancho ?? 0, alto: p.alto ?? 0,
          tipo_peso: p.tipo_peso || "kilogram", formas_pago: p.formas_pago || "todas",
          formas_envio: p.formas_envio || "todas",
          permite_actualizar_coste: p.permite_actualizar_coste !== false,
          permite_actualizar_stock: p.permite_actualizar_stock !== false,
          tipo_cheque_regalo: p.tipo_cheque_regalo || false,
          _product_id: bestOffer.product_id
        });
      } catch (error) {
        console.error("Error loading product data:", error);
      }
    }
  };

  const handleSaveProduct = async () => {
    if (!editForm._product_id) return;
    setSavingProduct(true);
    try {
      const { _product_id, ...payload } = editForm;
      await api.put(`/products/${_product_id}`, payload);
      toast.success("Producto actualizado correctamente");
      onSave?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar el producto");
    } finally {
      setSavingProduct(false);
    }
  };

  const updateEditField = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  if (!product) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
            Ficha del Producto
          </DialogTitle>
          <DialogDescription>{product.name}</DialogDescription>
        </DialogHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <div className="px-6 pt-2">
            <TabsList className="w-full grid grid-cols-2" data-testid="product-detail-tabs">
              <TabsTrigger value="proveedores" data-testid="tab-proveedores">
                <Truck className="w-4 h-4 mr-2" />
                Proveedores
              </TabsTrigger>
              <TabsTrigger value="datos" data-testid="tab-datos">
                <Pencil className="w-4 h-4 mr-2" />
                Datos del Producto
              </TabsTrigger>
            </TabsList>
          </div>

          {/* TAB 1: Proveedores */}
          <TabsContent value="proveedores" className="flex-1 overflow-y-auto px-6 pb-4 mt-0">
            <div className="space-y-5 pt-4">
              <div className="flex gap-5">
                <div className="w-24 h-24 flex-shrink-0">
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name}
                      className="w-full h-full object-cover rounded-lg border border-slate-200" />
                  ) : (
                    <div className="w-full h-full bg-slate-100 rounded-lg flex items-center justify-center">
                      <Package className="w-10 h-10 text-slate-300" />
                    </div>
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="text-lg font-semibold text-slate-900">{product.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-slate-100 text-slate-700 border-0 font-mono text-xs">EAN: {product.ean}</Badge>
                    {product.brand && <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">{product.brand}</Badge>}
                  </div>
                </div>
              </div>

              <Card className="border-emerald-200 bg-emerald-50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                        <Star className="w-5 h-5 text-emerald-600" />
                      </div>
                      <div>
                        <p className="text-sm text-emerald-600 font-medium">Mejor Oferta</p>
                        <p className="text-lg font-bold text-emerald-700">{product.best_supplier}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-700">
                        {product.best_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </p>
                      <p className="text-sm text-emerald-600">Stock total: {product.total_stock} uds</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">
                  Todos los Proveedores ({product.supplier_count})
                </h4>
                <div className="space-y-2">
                  {product.suppliers.map((supplier, idx) => (
                    <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                      supplier.is_best_offer ? "bg-emerald-50 border-emerald-200" :
                      supplier.stock > 0 ? "bg-white border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
                    }`}>
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${supplier.is_best_offer ? "bg-emerald-100" : "bg-slate-100"}`}>
                          <Truck className={`w-4 h-4 ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-500"}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-900">{supplier.supplier_name}</p>
                            {supplier.is_best_offer && (
                              <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs"><Star className="w-3 h-3 mr-1" />Mejor</Badge>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 font-mono">SKU: {supplier.sku}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-900"}`}>
                          {supplier.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                        </p>
                        {supplier.stock > 0 ? (
                          <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">{supplier.stock} uds</Badge>
                        ) : (
                          <Badge className="bg-rose-100 text-rose-700 border-0 text-xs"><AlertTriangle className="w-3 h-3 mr-1" />Sin stock</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* TAB 2: Datos del Producto */}
          <TabsContent value="datos" className="flex-1 overflow-y-auto px-6 pb-4 mt-0">
            <div className="space-y-6 pt-4">
              <div className="space-y-2">
                <Label className="text-sm font-semibold text-slate-800">Nombre del Producto</Label>
                <Input value={editForm.name || ""} onChange={(e) => updateEditField("name", e.target.value)}
                  className="input-base" data-testid="edit-name" />
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800 mb-3">Identificadores</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                  {["referencia", "part_number", "ean", "asin", "upc", "gtin", "oem"].map((field) => (
                    <div key={field} className="space-y-1">
                      <Label className="text-xs text-slate-500 capitalize">{field.replace('_', ' ')}</Label>
                      <Input value={editForm[field] || ""} onChange={(e) => updateEditField(field, e.target.value)}
                        className="input-base text-sm h-9 font-mono" data-testid={`edit-${field}`} />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800 mb-3">Stock y Precio</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { field: "stock", label: "Stock" },
                    { field: "price", label: "Precio", type: "float" },
                    { field: "weight", label: "Peso", type: "float" },
                    { field: "dias_entrega", label: "Días entrega" },
                  ].map(({ field, label, type }) => (
                    <div key={field} className="space-y-1">
                      <Label className="text-xs text-slate-500">{label}</Label>
                      <Input type="number" step={type === "float" ? "0.01" : "1"}
                        value={editForm[field] ?? 0}
                        onChange={(e) => updateEditField(field, type === "float" ? parseFloat(e.target.value) || 0 : parseInt(e.target.value) || 0)}
                        className="input-base text-sm h-9 font-mono" data-testid={`edit-${field}`} />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800 mb-3">Estado</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <ToggleField label="Activado" value={editForm.activado} onChange={(v) => updateEditField("activado", v)} testId="edit-activado" />
                  <ToggleField label="Descatalogado" value={editForm.descatalogado} onChange={(v) => updateEditField("descatalogado", v)} testId="edit-descatalogado" />
                  <ToggleField label="Vender sin stock" value={editForm.vender_sin_stock} onChange={(v) => updateEditField("vender_sin_stock", v)} />
                  <ToggleField label="Envío gratis" value={editForm.envio_gratis} onChange={(v) => updateEditField("envio_gratis", v)} />
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-xs text-slate-500">Descripción</Label>
                <textarea value={editForm.description || ""} onChange={(e) => updateEditField("description", e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[80px] resize-y"
                  data-testid="edit-description" />
              </div>
            </div>
          </TabsContent>
        </Tabs>
        
        <div className="border-t px-6 py-4 flex items-center justify-between">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="btn-secondary">
            Cerrar
          </Button>
          <div className="flex items-center gap-2">
            {activeTab === "datos" && (
              <Button onClick={handleSaveProduct} disabled={savingProduct} className="btn-primary" data-testid="save-product-btn">
                {savingProduct ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Guardar Cambios
              </Button>
            )}
            <Button onClick={() => { onAddToCatalog?.([product.ean]); onOpenChange(false); }} className="btn-primary" variant={activeTab === "datos" ? "outline" : "default"}>
              <BookOpen className="w-4 h-4 mr-2" />
              Añadir a Catálogos
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProductDetailDialog;
