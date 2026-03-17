import { useState, useRef } from "react";
import { api } from "../../App";
import { toast } from "sonner";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Textarea } from "../ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import {
  Package, Save, Pencil, Star, Truck, Upload, X, Image, Plus,
  Barcode, DollarSign, Globe, Tag, Settings, Box, Search,
  FileText, Video, Shield, MapPin, Clock, Layers,
} from "lucide-react";
import StockBadge from "../shared/StockBadge";

// ─── Collapsible Section ───────────────────────────────────────────
const Section = ({ title, icon: Icon, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
      >
        {Icon && <Icon className="w-4 h-4 text-indigo-500" />}
        <span className="font-semibold text-sm text-slate-700">{title}</span>
        <svg
          className={`w-4 h-4 ml-auto text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="p-4 space-y-4">{children}</div>}
    </div>
  );
};

// ─── Tag Input Component ───────────────────────────────────────────
const TagInput = ({ value = [], onChange }) => {
  const [input, setInput] = useState("");

  const addTag = () => {
    const tag = input.trim();
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setInput("");
  };

  const removeTag = (tag) => {
    onChange(value.filter((t) => t !== tag));
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); addTag(); }
          }}
          placeholder="Añadir etiqueta y pulsar Enter"
          className="flex-1"
        />
        <Button type="button" variant="outline" size="sm" onClick={addTag} disabled={!input.trim()}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1 pr-1">
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-1 hover:bg-slate-300 rounded-full p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Custom Attributes Editor ──────────────────────────────────────
const CustomAttributesEditor = ({ value = [], onChange }) => {
  const addAttribute = () => {
    onChange([...value, { name: "", value: "" }]);
  };

  const updateAttribute = (index, field, val) => {
    const updated = [...value];
    updated[index] = { ...updated[index], [field]: val };
    onChange(updated);
  };

  const removeAttribute = (index) => {
    onChange(value.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {value.map((attr, idx) => (
        <div key={idx} className="flex gap-2 items-start">
          <div className="flex-1">
            <Input
              value={attr.name}
              onChange={(e) => updateAttribute(idx, "name", e.target.value)}
              placeholder="Nombre del atributo (ej: Color, Talla)"
              className="text-sm"
            />
          </div>
          <div className="flex-1">
            <Input
              value={attr.value}
              onChange={(e) => updateAttribute(idx, "value", e.target.value)}
              placeholder="Valor (ej: Rojo, XL)"
              className="text-sm"
            />
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-red-500 hover:text-red-700 hover:bg-red-50 shrink-0"
            onClick={() => removeAttribute(idx)}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={addAttribute} className="w-full">
        <Plus className="w-4 h-4 mr-2" />
        Añadir Atributo
      </Button>
    </div>
  );
};

// ─── Main Dialog ───────────────────────────────────────────────────
const ProductDetailDialog = ({
  open,
  onOpenChange,
  product,
  onProductUpdate,
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
      setLocalGalleryImages(product.gallery_images || []);
    }
    onOpenChange(isOpen);
  };

  // ─── Field helpers ─────────────────────────────────────────────
  const field = (key) => editForm[key] ?? product?.[key] ?? "";
  const fieldNum = (key) => editForm[key] ?? product?.[key] ?? "";
  const fieldBool = (key, def = false) => editForm[key] ?? product?.[key] ?? def;
  const fieldList = (key) => editForm[key] ?? product?.[key] ?? [];
  const setField = (key, val) => setEditForm({ ...editForm, [key]: val });

  // ─── Save ──────────────────────────────────────────────────────
  const handleSaveProduct = async () => {
    if (!product) return;
    setSavingProduct(true);
    try {
      const updateData = { ...editForm };

      // Include gallery images if modified
      if (localGalleryImages.length > 0 || (product.gallery_images && product.gallery_images.length > 0)) {
        updateData.gallery_images = localGalleryImages;
      }

      // Clean up undefined/empty string values (keep false, 0, empty arrays)
      Object.keys(updateData).forEach((key) => {
        if (updateData[key] === undefined) delete updateData[key];
      });

      await api.put(`/products/${product.id}`, updateData);
      toast.success("Producto actualizado correctamente");
      if (onProductUpdate) onProductUpdate();
      handleOpenChange(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar producto");
    } finally {
      setSavingProduct(false);
    }
  };

  // ─── Image handlers ────────────────────────────────────────────
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
      if (mainImageInputRef.current) mainImageInputRef.current.value = "";
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
      if (galleryImageInputRef.current) galleryImageInputRef.current.value = "";
    }
  };

  const handleRemoveGalleryImage = async (imageUrl) => {
    try {
      await api.delete(`/products/${product.id}/gallery-image?image_url=${encodeURIComponent(imageUrl)}`);
      setLocalGalleryImages(localGalleryImages.filter((img) => img !== imageUrl));
      toast.success("Imagen eliminada de la galería");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar imagen");
    }
  };

  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
    return `${backendUrl}${url}`;
  };

  if (!product) return null;

  const isUnified = product.suppliers && Array.isArray(product.suppliers);
  const hasChanges =
    Object.keys(editForm).length > 0 ||
    JSON.stringify(localGalleryImages) !== JSON.stringify(product.gallery_images || []);
  const currentImageUrl = editForm.image_url ?? product.image_url;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3" style={{ fontFamily: "Manrope, sans-serif" }}>
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
          <TabsList className="flex w-full overflow-x-auto gap-0.5 bg-slate-100 p-1 rounded-lg">
            <TabsTrigger value="proveedores" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Truck className="w-3.5 h-3.5" />
              {isUnified ? "Proveedores" : "Info"}
            </TabsTrigger>
            <TabsTrigger value="general" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <FileText className="w-3.5 h-3.5" />
              General
            </TabsTrigger>
            <TabsTrigger value="identificadores" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Barcode className="w-3.5 h-3.5" />
              Identificadores
            </TabsTrigger>
            <TabsTrigger value="precios" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <DollarSign className="w-3.5 h-3.5" />
              Precios
            </TabsTrigger>
            <TabsTrigger value="logistica" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Box className="w-3.5 h-3.5" />
              Logística
            </TabsTrigger>
            <TabsTrigger value="atributos" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Layers className="w-3.5 h-3.5" />
              Atributos
            </TabsTrigger>
            <TabsTrigger value="seo" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Search className="w-3.5 h-3.5" />
              SEO
            </TabsTrigger>
            <TabsTrigger value="opciones" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Settings className="w-3.5 h-3.5" />
              Opciones
            </TabsTrigger>
            <TabsTrigger value="imagenes" className="flex items-center gap-1.5 text-xs px-3 whitespace-nowrap">
              <Image className="w-3.5 h-3.5" />
              Imágenes
            </TabsTrigger>
          </TabsList>

          {/* ────────────────────────────────────────────────────────
              Tab: Proveedores / Info
          ──────────────────────────────────────────────────────── */}
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
                        <p className={`text-lg font-bold ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-900"}`}>
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
                    <div className="mt-1"><StockBadge stock={product.stock || 0} /></div>
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

          {/* ────────────────────────────────────────────────────────
              Tab: General
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="general" className="mt-4 space-y-4">
            <Section title="Información Básica" icon={Package}>
              <div className="space-y-2">
                <Label className="font-semibold">Nombre del Producto</Label>
                <Input
                  value={field("name")}
                  onChange={(e) => setField("name", e.target.value)}
                  placeholder="Nombre del producto"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Marca</Label>
                  <Input
                    value={field("brand")}
                    onChange={(e) => setField("brand", e.target.value)}
                    placeholder="Marca del producto"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Fabricante</Label>
                  <Input
                    value={field("manufacturer")}
                    onChange={(e) => setField("manufacturer", e.target.value)}
                    placeholder="Fabricante (si difiere de la marca)"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Categoría</Label>
                  <Input
                    value={field("category")}
                    onChange={(e) => setField("category", e.target.value)}
                    placeholder="Categoría principal"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Condición</Label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={field("condicion") || "new"}
                    onChange={(e) => setField("condicion", e.target.value)}
                  >
                    <option value="new">Nuevo</option>
                    <option value="refurbished">Reacondicionado</option>
                    <option value="used">Usado</option>
                  </select>
                </div>
              </div>
            </Section>

            <Section title="Descripciones" icon={FileText}>
              <div className="space-y-2">
                <Label className="font-semibold">Descripción Corta</Label>
                <Textarea
                  value={field("short_description")}
                  onChange={(e) => setField("short_description", e.target.value)}
                  placeholder="Breve descripción del producto (se muestra en listados)"
                  maxLength={500}
                  className="min-h-[60px]"
                />
                <p className="text-xs text-slate-400">Máximo 500 caracteres</p>
              </div>

              <div className="space-y-2">
                <Label className="font-semibold">Descripción Larga</Label>
                <Textarea
                  value={editForm.long_description ?? product?.long_description ?? product?.description ?? ""}
                  onChange={(e) => setField("long_description", e.target.value)}
                  placeholder="Descripción detallada del producto. Admite texto extenso con toda la información del producto."
                  className="min-h-[150px]"
                />
              </div>
            </Section>

            <Section title="Contenido Multimedia" icon={Video} defaultOpen={false}>
              <div className="space-y-2">
                <Label>URL de Vídeo</Label>
                <Input
                  value={field("video_url")}
                  onChange={(e) => setField("video_url", e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=... o URL de vídeo"
                />
                <p className="text-xs text-slate-400">Enlace a vídeo del producto (YouTube, Vimeo, etc.)</p>
              </div>
            </Section>

            <Section title="Notas Internas" icon={FileText} defaultOpen={false}>
              <div className="space-y-2">
                <Textarea
                  value={field("notas_internas")}
                  onChange={(e) => setField("notas_internas", e.target.value)}
                  placeholder="Notas privadas sobre este producto (no visibles en tiendas)"
                  className="min-h-[80px]"
                />
                <p className="text-xs text-slate-400">Solo visible internamente, no se exporta a tiendas.</p>
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Identificadores
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="identificadores" className="mt-4 space-y-4">
            <Section title="Códigos del Producto" icon={Barcode}>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>SKU</Label>
                  <Input value={product.sku || ""} disabled className="bg-slate-50" />
                  <p className="text-xs text-slate-400">El SKU se asigna desde el proveedor</p>
                </div>
                <div className="space-y-2">
                  <Label>EAN / EAN-13</Label>
                  <Input
                    value={field("ean")}
                    onChange={(e) => setField("ean", e.target.value)}
                    placeholder="Código EAN-13"
                  />
                </div>
                <div className="space-y-2">
                  <Label>UPC</Label>
                  <Input
                    value={field("upc")}
                    onChange={(e) => setField("upc", e.target.value)}
                    placeholder="Código UPC"
                  />
                </div>
                <div className="space-y-2">
                  <Label>GTIN</Label>
                  <Input
                    value={field("gtin")}
                    onChange={(e) => setField("gtin", e.target.value)}
                    placeholder="Global Trade Item Number"
                  />
                </div>
                <div className="space-y-2">
                  <Label>ASIN (Amazon)</Label>
                  <Input
                    value={field("asin")}
                    onChange={(e) => setField("asin", e.target.value)}
                    placeholder="Amazon Standard Identification Number"
                  />
                </div>
                <div className="space-y-2">
                  <Label>MPN</Label>
                  <Input
                    value={field("mpn")}
                    onChange={(e) => setField("mpn", e.target.value)}
                    placeholder="Manufacturer Part Number"
                  />
                </div>
              </div>
            </Section>

            <Section title="Referencias Internas" icon={Tag} defaultOpen={false}>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Referencia</Label>
                  <Input
                    value={field("referencia")}
                    onChange={(e) => setField("referencia", e.target.value)}
                    placeholder="Referencia interna"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Part Number</Label>
                  <Input
                    value={field("part_number")}
                    onChange={(e) => setField("part_number", e.target.value)}
                    placeholder="Número de parte"
                  />
                </div>
                <div className="space-y-2">
                  <Label>OEM</Label>
                  <Input
                    value={field("oem")}
                    onChange={(e) => setField("oem", e.target.value)}
                    placeholder="Código OEM"
                  />
                </div>
                <div className="space-y-2">
                  <Label>ID ERP</Label>
                  <Input
                    value={field("id_erp")}
                    onChange={(e) => setField("id_erp", e.target.value)}
                    placeholder="Identificador en el ERP"
                  />
                </div>
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Precios y Stock
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="precios" className="mt-4 space-y-4">
            <Section title="Precios" icon={DollarSign}>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="font-semibold">Precio de Venta (€)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={fieldNum("price")}
                    onChange={(e) => setField("price", parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Precio de Coste (€)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={fieldNum("cost_price")}
                    onChange={(e) => setField("cost_price", parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                  />
                  <p className="text-xs text-slate-400">Precio de compra al proveedor</p>
                </div>
                <div className="space-y-2">
                  <Label>Precio Comparación (€)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={fieldNum("compare_at_price")}
                    onChange={(e) => setField("compare_at_price", parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                  />
                  <p className="text-xs text-slate-400">PVP recomendado / precio antes de descuento</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="space-y-2">
                  <Label>Moneda</Label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={field("currency") || "EUR"}
                    onChange={(e) => setField("currency", e.target.value)}
                  >
                    <option value="EUR">EUR - Euro</option>
                    <option value="USD">USD - Dólar</option>
                    <option value="GBP">GBP - Libra</option>
                    <option value="MXN">MXN - Peso Mexicano</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Clase de Impuesto</Label>
                  <Input
                    value={field("tax_class")}
                    onChange={(e) => setField("tax_class", e.target.value)}
                    placeholder="Ej: IVA 21%, Reducido, Exento"
                  />
                </div>
              </div>

              {/* Margin indicator */}
              {(fieldNum("price") > 0 && fieldNum("cost_price") > 0) && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-blue-700 font-medium">Margen de beneficio:</span>
                    <span className="text-blue-800 font-bold">
                      {(((fieldNum("price") - fieldNum("cost_price")) / fieldNum("cost_price")) * 100).toFixed(1)}%
                      {" "}
                      (€{(fieldNum("price") - fieldNum("cost_price")).toFixed(2)})
                    </span>
                  </div>
                </div>
              )}
            </Section>

            <Section title="Inventario" icon={Package}>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="font-semibold">Stock Actual</Label>
                  <Input
                    type="number"
                    value={fieldNum("stock")}
                    onChange={(e) => setField("stock", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Stock Disponible</Label>
                  <Input
                    type="number"
                    value={fieldNum("stock_disponible")}
                    onChange={(e) => setField("stock_disponible", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Stock Fantasma</Label>
                  <Input
                    type="number"
                    value={fieldNum("stock_fantasma")}
                    onChange={(e) => setField("stock_fantasma", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                  <p className="text-xs text-slate-400">Stock reservado o virtual</p>
                </div>
                <div className="space-y-2">
                  <Label>Stock Marketplace</Label>
                  <Input
                    type="number"
                    value={fieldNum("stock_market")}
                    onChange={(e) => setField("stock_market", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Unidades por Caja</Label>
                  <Input
                    type="number"
                    value={fieldNum("unid_caja")}
                    onChange={(e) => setField("unid_caja", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="space-y-2">
                  <Label>Cantidad Mínima de Compra</Label>
                  <Input
                    type="number"
                    value={fieldNum("cantidad_minima")}
                    onChange={(e) => setField("cantidad_minima", parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cantidad Máxima por Carrito</Label>
                  <Input
                    type="number"
                    value={fieldNum("cantidad_maxima_carrito")}
                    onChange={(e) => setField("cantidad_maxima_carrito", parseInt(e.target.value) || 0)}
                    placeholder="Sin límite"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div>
                  <Label>Vender sin Stock</Label>
                  <p className="text-xs text-slate-400">Permitir compras cuando no hay stock</p>
                </div>
                <Switch
                  checked={fieldBool("vender_sin_stock")}
                  onCheckedChange={(v) => setField("vender_sin_stock", v)}
                />
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Logística
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="logistica" className="mt-4 space-y-4">
            <Section title="Dimensiones y Peso" icon={Box}>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Peso</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={fieldNum("weight")}
                    onChange={(e) => setField("weight", parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo de Peso</Label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={field("tipo_peso") || "kilogram"}
                    onChange={(e) => setField("tipo_peso", e.target.value)}
                  >
                    <option value="gram">Gramos</option>
                    <option value="kilogram">Kilogramos</option>
                    <option value="ounce">Onzas</option>
                    <option value="pound">Libras</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Largo (cm)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={fieldNum("largo")}
                    onChange={(e) => setField("largo", parseFloat(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Ancho (cm)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={fieldNum("ancho")}
                    onChange={(e) => setField("ancho", parseFloat(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Alto (cm)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={fieldNum("alto")}
                    onChange={(e) => setField("alto", parseFloat(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
              </div>
            </Section>

            <Section title="Envío" icon={Truck}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Requiere Envío</Label>
                    <p className="text-xs text-slate-400">Producto físico que necesita envío</p>
                  </div>
                  <Switch
                    checked={fieldBool("requiere_envio", true)}
                    onCheckedChange={(v) => setField("requiere_envio", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Envío Gratis</Label>
                    <p className="text-xs text-slate-400">Sin coste de envío para el cliente</p>
                  </div>
                  <Switch
                    checked={fieldBool("envio_gratis")}
                    onCheckedChange={(v) => setField("envio_gratis", v)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Gastos de Envío (€)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={fieldNum("gastos_envio")}
                      onChange={(e) => setField("gastos_envio", parseFloat(e.target.value) || 0)}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Días de Entrega</Label>
                    <Input
                      type="number"
                      value={fieldNum("dias_entrega")}
                      onChange={(e) => setField("dias_entrega", parseInt(e.target.value) || 0)}
                      placeholder="Ej: 3"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Formas de Envío</Label>
                  <Input
                    value={field("formas_envio")}
                    onChange={(e) => setField("formas_envio", e.target.value)}
                    placeholder="todas"
                  />
                  <p className="text-xs text-slate-400">Métodos de envío permitidos (todas = todos los disponibles)</p>
                </div>
              </div>
            </Section>

            <Section title="Origen y Garantía" icon={MapPin} defaultOpen={false}>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>País de Origen</Label>
                  <Input
                    value={field("country_of_origin")}
                    onChange={(e) => setField("country_of_origin", e.target.value)}
                    placeholder="Ej: España, China, Alemania"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Garantía</Label>
                  <Input
                    value={field("warranty")}
                    onChange={(e) => setField("warranty", e.target.value)}
                    placeholder="Ej: 2 años, 6 meses"
                  />
                </div>
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Atributos y Etiquetas
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="atributos" className="mt-4 space-y-4">
            <Section title="Etiquetas" icon={Tag}>
              <p className="text-sm text-slate-500 mb-2">
                Las etiquetas ayudan a organizar y buscar productos. Se pueden usar para filtrar en catálogos y tiendas.
              </p>
              <TagInput
                value={fieldList("tags")}
                onChange={(v) => setField("tags", v)}
              />
            </Section>

            <Section title="Atributos Personalizados" icon={Layers}>
              <p className="text-sm text-slate-500 mb-2">
                Define características específicas del producto como color, talla, material, etc. Estos atributos se exportan a las tiendas online.
              </p>
              <CustomAttributesEditor
                value={fieldList("custom_attributes")}
                onChange={(v) => setField("custom_attributes", v)}
              />
            </Section>

            {/* Show raw attributes dict from supplier if exists */}
            {product.attributes && Object.keys(product.attributes).length > 0 && (
              <Section title="Atributos del Proveedor (solo lectura)" icon={Package} defaultOpen={false}>
                <div className="bg-slate-50 rounded-lg p-3">
                  <div className="space-y-2">
                    {Object.entries(product.attributes).map(([key, val]) => (
                      <div key={key} className="flex justify-between text-sm border-b border-slate-100 pb-1 last:border-0">
                        <span className="text-slate-600 font-medium">{key}</span>
                        <span className="text-slate-900">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-slate-400">
                  Estos atributos se importan automáticamente del proveedor y no se pueden editar directamente.
                </p>
              </Section>
            )}
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: SEO
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="seo" className="mt-4 space-y-4">
            <Section title="Posicionamiento SEO" icon={Search}>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="font-semibold">Meta Título</Label>
                  <Input
                    value={field("meta_title")}
                    onChange={(e) => setField("meta_title", e.target.value)}
                    placeholder={product.name || "Título para buscadores"}
                    maxLength={70}
                  />
                  <div className="flex justify-between">
                    <p className="text-xs text-slate-400">Título que aparece en Google. Recomendado: 50-60 caracteres.</p>
                    <p className={`text-xs ${(field("meta_title") || "").length > 60 ? "text-amber-500" : "text-slate-400"}`}>
                      {(field("meta_title") || "").length}/70
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="font-semibold">Meta Descripción</Label>
                  <Textarea
                    value={field("meta_description")}
                    onChange={(e) => setField("meta_description", e.target.value)}
                    placeholder="Descripción que aparece en los resultados de búsqueda de Google"
                    maxLength={160}
                    className="min-h-[80px]"
                  />
                  <div className="flex justify-between">
                    <p className="text-xs text-slate-400">Recomendado: 120-155 caracteres.</p>
                    <p className={`text-xs ${(field("meta_description") || "").length > 155 ? "text-amber-500" : "text-slate-400"}`}>
                      {(field("meta_description") || "").length}/160
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Palabras Clave (Meta Keywords)</Label>
                  <Input
                    value={field("meta_keywords")}
                    onChange={(e) => setField("meta_keywords", e.target.value)}
                    placeholder="palabra1, palabra2, palabra3"
                  />
                  <p className="text-xs text-slate-400">Separadas por comas. Usadas por algunos marketplaces.</p>
                </div>

                <div className="space-y-2">
                  <Label>Slug / URL amigable</Label>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400 whitespace-nowrap">/producto/</span>
                    <Input
                      value={field("slug")}
                      onChange={(e) => setField("slug", e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"))}
                      placeholder={product.name?.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+$/, "") || "mi-producto"}
                    />
                  </div>
                  <p className="text-xs text-slate-400">URL amigable para el producto en la tienda online.</p>
                </div>
              </div>

              {/* SEO Preview */}
              <div className="mt-4 p-4 border border-slate-200 rounded-lg bg-white">
                <p className="text-xs text-slate-400 mb-2 font-medium">Vista previa en Google:</p>
                <div className="space-y-1">
                  <p className="text-[#1a0dab] text-lg leading-tight truncate">
                    {field("meta_title") || product.name || "Título del producto"}
                  </p>
                  <p className="text-[#006621] text-sm truncate">
                    tutienda.com/producto/{field("slug") || product.name?.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "..."}
                  </p>
                  <p className="text-sm text-[#545454] line-clamp-2">
                    {field("meta_description") || product.short_description || "Descripción del producto que aparecerá en los resultados de búsqueda..."}
                  </p>
                </div>
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Opciones / Estado
          ──────────────────────────────────────────────────────── */}
          <TabsContent value="opciones" className="mt-4 space-y-4">
            <Section title="Estado del Producto" icon={Shield}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-semibold">Activado</Label>
                    <p className="text-xs text-slate-400">Producto visible y disponible para la venta</p>
                  </div>
                  <Switch
                    checked={fieldBool("activado", true)}
                    onCheckedChange={(v) => setField("activado", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Descatalogado</Label>
                    <p className="text-xs text-slate-400">Marcar como descatalogado por el fabricante</p>
                  </div>
                  <Switch
                    checked={fieldBool("descatalogado")}
                    onCheckedChange={(v) => setField("descatalogado", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Producto Nuevo</Label>
                    <p className="text-xs text-slate-400">Mostrar etiqueta "Nuevo" en la tienda</p>
                  </div>
                  <Switch
                    checked={field("nuevo") === "true" || field("nuevo") === true}
                    onCheckedChange={(v) => setField("nuevo", v ? "true" : "false")}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Fecha de Disponibilidad</Label>
                  <Input
                    type="date"
                    value={field("fecha_disponibilidad")}
                    onChange={(e) => setField("fecha_disponibilidad", e.target.value)}
                  />
                  <p className="text-xs text-slate-400">Fecha a partir de la cual el producto estará disponible</p>
                </div>
              </div>
            </Section>

            <Section title="Opciones de Venta" icon={Settings}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Activar en Punto de Venta (POS)</Label>
                    <p className="text-xs text-slate-400">Disponible en terminales de venta física</p>
                  </div>
                  <Switch
                    checked={fieldBool("activar_pos")}
                    onCheckedChange={(v) => setField("activar_pos", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Tipo Pack</Label>
                    <p className="text-xs text-slate-400">Este producto es un pack o bundle</p>
                  </div>
                  <Switch
                    checked={fieldBool("tipo_pack")}
                    onCheckedChange={(v) => setField("tipo_pack", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Resto Stock</Label>
                    <p className="text-xs text-slate-400">Mostrar cantidad de stock restante</p>
                  </div>
                  <Switch
                    checked={fieldBool("resto_stock", true)}
                    onCheckedChange={(v) => setField("resto_stock", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Cheque Regalo</Label>
                    <p className="text-xs text-slate-400">Este producto es un cheque/tarjeta regalo</p>
                  </div>
                  <Switch
                    checked={fieldBool("tipo_cheque_regalo")}
                    onCheckedChange={(v) => setField("tipo_cheque_regalo", v)}
                  />
                </div>
              </div>
            </Section>

            <Section title="Permisos de Actualización" icon={Shield} defaultOpen={false}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Permitir Actualizar Coste</Label>
                    <p className="text-xs text-slate-400">El precio de coste se actualiza en la sincronización</p>
                  </div>
                  <Switch
                    checked={fieldBool("permite_actualizar_coste", true)}
                    onCheckedChange={(v) => setField("permite_actualizar_coste", v)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Permitir Actualizar Stock</Label>
                    <p className="text-xs text-slate-400">El stock se actualiza en la sincronización</p>
                  </div>
                  <Switch
                    checked={fieldBool("permite_actualizar_stock", true)}
                    onCheckedChange={(v) => setField("permite_actualizar_stock", v)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Formas de Pago</Label>
                  <Input
                    value={field("formas_pago")}
                    onChange={(e) => setField("formas_pago", e.target.value)}
                    placeholder="todas"
                  />
                  <p className="text-xs text-slate-400">Métodos de pago permitidos (todas = todos los disponibles)</p>
                </div>
              </div>
            </Section>
          </TabsContent>

          {/* ────────────────────────────────────────────────────────
              Tab: Imágenes
          ──────────────────────────────────────────────────────── */}
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
                        onChange={(e) => setField("image_url", e.target.value)}
                        placeholder="https://ejemplo.com/imagen.jpg"
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

              {/* Galería */}
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
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}

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
          {activeTab !== "proveedores" && hasChanges && (
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
