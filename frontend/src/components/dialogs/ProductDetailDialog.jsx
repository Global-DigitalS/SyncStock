import { useState, useRef } from "react";
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
import { Package, Save, Pencil, Star, Truck, Upload, X, Image, Plus, Trash2 } from "lucide-react";
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
  const [uploadingImage, setUploadingImage] = useState(false);
  const [localGalleryImages, setLocalGalleryImages] = useState([]);
  const mainImageInputRef = useRef(null);
  const galleryImageInputRef = useRef(null);

  const handleOpenChange = (isOpen) => {
    if (!isOpen) {
      setEditForm({});
      setActiveTab("proveedores");
      setLocalGalleryImages([]);
    } else if (product) {
      // Initialize gallery images from product
      setLocalGalleryImages(product.gallery_images || []);
    }
    onOpenChange(isOpen);
  };

  const handleSaveProduct = async () => {
    if (!product) return;
    
    setSavingProduct(true);
    try {
      const updateData = { ...editForm };
      
      // Include gallery images if modified
      if (localGalleryImages.length > 0 || (product.gallery_images && product.gallery_images.length > 0)) {
        updateData.gallery_images = localGalleryImages;
      }
      
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

  const handleUploadMainImage = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !product) return;

    setUploadingImage(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await api.post(
        `/products/${product.id}/upload-image?image_type=main`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      
      setEditForm({ ...editForm, image_url: response.data.url });
      toast.success("Imagen principal subida correctamente");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al subir imagen");
    } finally {
      setUploadingImage(false);
      if (mainImageInputRef.current) {
        mainImageInputRef.current.value = "";
      }
    }
  };

  const handleUploadGalleryImage = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !product) return;

    setUploadingImage(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await api.post(
        `/products/${product.id}/upload-image?image_type=gallery`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      
      setLocalGalleryImages([...localGalleryImages, response.data.url]);
      toast.success("Imagen añadida a la galería");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al subir imagen");
    } finally {
      setUploadingImage(false);
      if (galleryImageInputRef.current) {
        galleryImageInputRef.current.value = "";
      }
    }
  };

  const handleRemoveGalleryImage = async (imageUrl) => {
    try {
      await api.delete(`/products/${product.id}/gallery-image?image_url=${encodeURIComponent(imageUrl)}`);
      setLocalGalleryImages(localGalleryImages.filter(img => img !== imageUrl));
      toast.success("Imagen eliminada de la galería");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar imagen");
    }
  };

  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    // For local uploads, prepend the backend URL
    const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
    return `${backendUrl}${url}`;
  };

  if (!product) return null;

  // Check if this is a unified product (has suppliers array)
  const isUnified = product.suppliers && Array.isArray(product.suppliers);
  const hasChanges = Object.keys(editForm).length > 0 || 
    JSON.stringify(localGalleryImages) !== JSON.stringify(product.gallery_images || []);
  
  const currentImageUrl = editForm.image_url ?? product.image_url;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
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
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="proveedores" className="flex items-center gap-2">
              <Truck className="w-4 h-4" />
              {isUnified ? "Proveedores" : "Info"}
            </TabsTrigger>
            <TabsTrigger value="editar" className="flex items-center gap-2">
              <Pencil className="w-4 h-4" />
              Editar
            </TabsTrigger>
            <TabsTrigger value="imagenes" className="flex items-center gap-2">
              <Image className="w-4 h-4" />
              Imágenes
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
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Marca</span>
                    <p className="font-medium text-slate-900">{product.brand || "-"}</p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Categoría</span>
                    <p className="font-medium text-slate-900">{product.category || "-"}</p>
                  </div>
                </div>
                {product.short_description && (
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Descripción Corta</span>
                    <p className="text-sm text-slate-700 mt-1">{product.short_description}</p>
                  </div>
                )}
                {(product.description || product.long_description) && (
                  <div className="bg-slate-50 p-3 rounded-lg">
                    <span className="text-sm text-slate-500">Descripción Larga</span>
                    <p className="text-sm text-slate-700 mt-1 whitespace-pre-wrap">
                      {product.long_description || product.description}
                    </p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Tab: Editar */}
          <TabsContent value="editar" className="mt-4">
            <div className="space-y-4">
              {/* Nombre */}
              <div className="space-y-2">
                <Label className="font-semibold">Nombre del Producto</Label>
                <Input
                  value={editForm.name ?? product.name ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  placeholder="Nombre del producto"
                  data-testid="edit-product-name"
                />
              </div>

              {/* Marca y Categoría */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="font-semibold">Marca</Label>
                  <Input
                    value={editForm.brand ?? product.brand ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, brand: e.target.value })}
                    placeholder="Marca del producto"
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
              </div>

              {/* Descripción Corta */}
              <div className="space-y-2">
                <Label className="font-semibold">Descripción Corta</Label>
                <textarea
                  className="input-base min-h-[60px] w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={editForm.short_description ?? product.short_description ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, short_description: e.target.value })}
                  placeholder="Breve descripción del producto (se muestra en listados)"
                  data-testid="edit-product-short-description"
                  maxLength={500}
                />
                <p className="text-xs text-slate-400">Máximo 500 caracteres</p>
              </div>

              {/* Descripción Larga */}
              <div className="space-y-2">
                <Label className="font-semibold">Descripción Larga</Label>
                <textarea
                  className="input-base min-h-[120px] w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={editForm.long_description ?? product.long_description ?? product.description ?? ""}
                  onChange={(e) => setEditForm({ ...editForm, long_description: e.target.value })}
                  placeholder="Descripción detallada del producto"
                  data-testid="edit-product-long-description"
                />
              </div>

              {/* Precio, Stock, EAN, Peso */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-200">
                <div className="space-y-2">
                  <Label>Precio (€)</Label>
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
                  <Label>EAN</Label>
                  <Input
                    value={editForm.ean ?? product.ean ?? ""}
                    onChange={(e) => setEditForm({ ...editForm, ean: e.target.value })}
                    placeholder="EAN13"
                    data-testid="edit-product-ean"
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

              {/* Opciones adicionales */}
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
                  <Label>Envío gratis</Label>
                  <Switch
                    checked={editForm.envio_gratis ?? product.envio_gratis ?? false}
                    onCheckedChange={(v) => setEditForm({ ...editForm, envio_gratis: v })}
                    data-testid="edit-product-envio-gratis"
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Tab: Imágenes */}
          <TabsContent value="imagenes" className="mt-4">
            <div className="space-y-6">
              {/* Imagen Principal */}
              <div className="space-y-3">
                <Label className="font-semibold text-base">Imagen Principal</Label>
                <div className="flex gap-4">
                  <div className="w-40 h-40 border-2 border-dashed border-slate-300 rounded-lg overflow-hidden flex items-center justify-center bg-slate-50">
                    {currentImageUrl ? (
                      <img 
                        src={getImageUrl(currentImageUrl)} 
                        alt="Imagen principal" 
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Crect fill='%23f1f5f9' width='100' height='100'/%3E%3Ctext fill='%2394a3b8' font-family='sans-serif' font-size='12' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3ESin imagen%3C/text%3E%3C/svg%3E";
                        }}
                      />
                    ) : (
                      <div className="text-center text-slate-400">
                        <Image className="w-8 h-8 mx-auto mb-1" />
                        <span className="text-xs">Sin imagen</span>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="space-y-2">
                      <Label className="text-sm">URL de imagen</Label>
                      <Input
                        value={editForm.image_url ?? product.image_url ?? ""}
                        onChange={(e) => setEditForm({ ...editForm, image_url: e.target.value })}
                        placeholder="https://ejemplo.com/imagen.jpg"
                        data-testid="edit-product-image-url"
                      />
                    </div>
                    <div className="text-center text-slate-400 text-sm">o</div>
                    <div>
                      <input
                        type="file"
                        ref={mainImageInputRef}
                        onChange={handleUploadMainImage}
                        accept="image/*"
                        className="hidden"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        className="w-full"
                        onClick={() => mainImageInputRef.current?.click()}
                        disabled={uploadingImage}
                        data-testid="upload-main-image-btn"
                      >
                        {uploadingImage ? (
                          <>
                            <div className="spinner mr-2" />
                            Subiendo...
                          </>
                        ) : (
                          <>
                            <Upload className="w-4 h-4 mr-2" />
                            Subir imagen
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Galería de Imágenes */}
              <div className="space-y-3 pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <Label className="font-semibold text-base">Imágenes Secundarias (Galería)</Label>
                  <Badge variant="outline">{localGalleryImages.length} imágenes</Badge>
                </div>
                
                <div className="grid grid-cols-4 gap-3">
                  {localGalleryImages.map((imgUrl, idx) => (
                    <div 
                      key={idx} 
                      className="relative group w-full aspect-square border border-slate-200 rounded-lg overflow-hidden bg-slate-50"
                    >
                      <img 
                        src={getImageUrl(imgUrl)} 
                        alt={`Galería ${idx + 1}`}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Crect fill='%23f1f5f9' width='100' height='100'/%3E%3Ctext fill='%2394a3b8' font-family='sans-serif' font-size='10' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EError%3C/text%3E%3C/svg%3E";
                        }}
                      />
                      <button
                        onClick={() => handleRemoveGalleryImage(imgUrl)}
                        className="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Eliminar imagen"
                        data-testid={`remove-gallery-image-${idx}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                  
                  {/* Add Image Button */}
                  <div 
                    className="w-full aspect-square border-2 border-dashed border-slate-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-colors"
                    onClick={() => galleryImageInputRef.current?.click()}
                  >
                    <input
                      type="file"
                      ref={galleryImageInputRef}
                      onChange={handleUploadGalleryImage}
                      accept="image/*"
                      className="hidden"
                    />
                    {uploadingImage ? (
                      <div className="spinner" />
                    ) : (
                      <>
                        <Plus className="w-6 h-6 text-slate-400" />
                        <span className="text-xs text-slate-400 mt-1">Añadir</span>
                      </>
                    )}
                  </div>
                </div>
                
                <p className="text-xs text-slate-400">
                  Las imágenes secundarias se mostrarán en la galería del producto en las tiendas online.
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cerrar
          </Button>
          {(activeTab === "editar" || activeTab === "imagenes") && hasChanges && (
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
