import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Checkbox } from "../components/ui/checkbox";
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
  DialogDescription,
} from "../components/ui/dialog";
import {
  Truck,
  Package,
  Search,
  Upload,
  Plus,
  Eye,
  ArrowLeft,
  FileUp,
  CheckSquare,
  Square,
  ShoppingCart,
  Server,
  FileText,
  RefreshCw
} from "lucide-react";

const SupplierDetail = () => {
  const { supplierId } = useParams();
  const navigate = useNavigate();
  const [supplier, setSupplier] = useState(null);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [filters, setFilters] = useState({
    search: "",
    category: "all",
    stock: "all"
  });
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const fileInputRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [supplierRes, productsRes, categoriesRes] = await Promise.all([
        api.get(`/suppliers/${supplierId}`),
        api.get("/products", { params: { supplier_id: supplierId } }),
        api.get("/products/categories")
      ]);
      setSupplier(supplierRes.data);
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error("Error al cargar los datos del proveedor");
      navigate("/suppliers");
    } finally {
      setLoading(false);
    }
  }, [supplierId, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredProducts = products.filter((product) => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      if (!product.name.toLowerCase().includes(searchLower) && 
          !product.sku.toLowerCase().includes(searchLower) &&
          !(product.ean && product.ean.toLowerCase().includes(searchLower))) {
        return false;
      }
    }
    if (filters.category && filters.category !== "all" && product.category !== filters.category) {
      return false;
    }
    if (filters.stock === "low" && (product.stock === 0 || product.stock > 5)) {
      return false;
    }
    if (filters.stock === "out" && product.stock !== 0) {
      return false;
    }
    if (filters.stock === "in" && product.stock === 0) {
      return false;
    }
    return true;
  });

  const handleFileUpload = async (file) => {
    const validExtensions = ['.csv', '.xlsx', '.xls', '.xml'];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!validExtensions.includes(ext)) {
      toast.error("Formato no soportado. Use CSV, XLSX, XLS o XML");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post(`/products/import/${supplierId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(`Importación completada: ${res.data.imported} nuevos, ${res.data.updated} actualizados`);
      setShowUploadDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al importar productos");
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const toggleProductSelection = (productId) => {
    setSelectedProducts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        newSet.add(productId);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedProducts.size === filteredProducts.length) {
      setSelectedProducts(new Set());
    } else {
      setSelectedProducts(new Set(filteredProducts.map((p) => p.id)));
    }
  };

  const handleAddSelectedToCatalog = async () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }

    setAddingToCatalog(true);
    let added = 0;
    let skipped = 0;

    for (const productId of selectedProducts) {
      try {
        await api.post("/catalog", { product_id: productId });
        added++;
      } catch (error) {
        if (error.response?.status === 400) {
          skipped++;
        }
      }
    }

    setAddingToCatalog(false);
    setSelectedProducts(new Set());

    if (added > 0 && skipped > 0) {
      toast.success(`${added} productos añadidos, ${skipped} ya estaban en el catálogo`);
    } else if (added > 0) {
      toast.success(`${added} productos añadidos al catálogo`);
    } else {
      toast.info("Todos los productos seleccionados ya estaban en el catálogo");
    }
  };

  const handleAddSingleToCatalog = async (productId) => {
    try {
      await api.post("/catalog", { product_id: productId });
      toast.success("Producto añadido al catálogo");
    } catch (error) {
      if (error.response?.status === 400) {
        toast.info("El producto ya está en el catálogo");
      } else {
        toast.error("Error al añadir al catálogo");
      }
    }
  };

  const getStockBadge = (stock) => {
    if (stock === 0) return <span className="badge-error">Sin stock</span>;
    if (stock <= 5) return <span className="badge-warning">{stock} uds</span>;
    return <span className="badge-success">{stock} uds</span>;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
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
      {/* Back Button & Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/suppliers")}
          className="mb-4 text-slate-600 hover:text-slate-900"
          data-testid="back-to-suppliers"
        >
          <ArrowLeft className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Volver a Proveedores
        </Button>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-indigo-100 rounded-sm flex items-center justify-center">
              <Truck className="w-7 h-7 text-indigo-600" strokeWidth={1.5} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {supplier?.name}
              </h1>
              {supplier?.description && (
                <p className="text-slate-500">{supplier.description}</p>
              )}
            </div>
          </div>
          <Button onClick={() => setShowUploadDialog(true)} className="btn-primary" data-testid="import-products-btn">
            <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Importar Productos
          </Button>
        </div>
      </div>

      {/* Supplier Info Card */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-slate-500">Formato de archivo</p>
              <div className="flex items-center gap-1.5 mt-1">
                <FileText className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
                <span className="font-medium uppercase text-sm">{supplier?.file_format || "CSV"}</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-500">Conexión FTP</p>
              <div className="flex items-center gap-1.5 mt-1">
                <Server className={`w-4 h-4 ${supplier?.ftp_host ? 'text-emerald-500' : 'text-slate-300'}`} strokeWidth={1.5} />
                <span className="text-sm font-mono">{supplier?.ftp_host || "No configurado"}</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-500">Productos</p>
              <p className="font-mono text-xl font-semibold text-slate-900">{products.length.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Última sincronización</p>
              <p className="text-sm text-slate-700">{formatDate(supplier?.last_sync)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Selection Actions */}
      {selectedProducts.size > 0 && (
        <Card className="border-indigo-200 bg-indigo-50 mb-6 animate-slide-up">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckSquare className="w-5 h-5 text-indigo-600" strokeWidth={1.5} />
                <span className="font-medium text-indigo-900">
                  {selectedProducts.size} producto{selectedProducts.size !== 1 ? "s" : ""} seleccionado{selectedProducts.size !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  onClick={() => setSelectedProducts(new Set())}
                  className="btn-secondary"
                  data-testid="clear-selection"
                >
                  Limpiar selección
                </Button>
                <Button
                  onClick={handleAddSelectedToCatalog}
                  disabled={addingToCatalog}
                  className="btn-primary"
                  data-testid="add-selected-to-catalog"
                >
                  {addingToCatalog ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
                  ) : (
                    <ShoppingCart className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  )}
                  Añadir a Mi Catálogo
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" strokeWidth={1.5} />
              <Input
                placeholder="Buscar por nombre, SKU o EAN..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-9 input-base"
                data-testid="search-products"
              />
            </div>
            <Select
              value={filters.category}
              onValueChange={(value) => setFilters({ ...filters, category: value })}
            >
              <SelectTrigger className="w-full lg:w-[180px] input-base" data-testid="filter-category">
                <SelectValue placeholder="Categoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las categorías</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.stock}
              onValueChange={(value) => setFilters({ ...filters, stock: value })}
            >
              <SelectTrigger className="w-full lg:w-[150px] input-base" data-testid="filter-stock">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="in">Con stock</SelectItem>
                <SelectItem value="low">Stock bajo</SelectItem>
                <SelectItem value="out">Sin stock</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      {filteredProducts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Package className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            {products.length === 0 ? "No hay productos" : "No se encontraron productos"}
          </h3>
          <p className="text-slate-500 mb-4">
            {products.length === 0 
              ? "Importa productos de este proveedor para comenzar"
              : "Prueba con otros filtros de búsqueda"
            }
          </p>
          {products.length === 0 && (
            <Button onClick={() => setShowUploadDialog(true)} className="btn-primary" data-testid="empty-import-btn">
              <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Importar Productos
            </Button>
          )}
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="w-[50px]">
                    <Checkbox
                      checked={selectedProducts.size === filteredProducts.length && filteredProducts.length > 0}
                      onCheckedChange={toggleSelectAll}
                      data-testid="select-all-checkbox"
                    />
                  </TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.map((product) => (
                  <TableRow
                    key={product.id}
                    className={`table-row ${selectedProducts.has(product.id) ? "bg-indigo-50" : ""}`}
                    data-testid={`product-row-${product.id}`}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedProducts.has(product.id)}
                        onCheckedChange={() => toggleProductSelection(product.id)}
                        data-testid={`select-product-${product.id}`}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3 max-w-[300px]">
                        {product.image_url ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-10 h-10 object-cover rounded-sm border border-slate-200"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-slate-100 rounded-sm flex items-center justify-center">
                            <Package className="w-5 h-5 text-slate-400" strokeWidth={1.5} />
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900 truncate">{product.name}</p>
                          {product.brand && (
                            <p className="text-xs text-slate-500">{product.brand}</p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-sm text-slate-600">{product.sku}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-600">{product.category || "-"}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono font-semibold text-slate-900">
                        {product.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {getStockBadge(product.stock)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { setSelectedProduct(product); setShowDetailDialog(true); }}
                          className="h-8 w-8 p-0"
                          data-testid={`view-product-${product.id}`}
                        >
                          <Eye className="w-4 h-4" strokeWidth={1.5} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAddSingleToCatalog(product.id)}
                          className="h-8 w-8 p-0 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                          data-testid={`add-to-catalog-${product.id}`}
                        >
                          <Plus className="w-4 h-4" strokeWidth={1.5} />
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

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Importar Productos</DialogTitle>
            <DialogDescription>
              Sube un archivo con los productos de {supplier?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div
              className={`upload-zone ${dragActive ? "dragging" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.xml"
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
                data-testid="file-input"
              />
              {uploading ? (
                <div className="flex flex-col items-center">
                  <div className="spinner mb-3"></div>
                  <p className="text-slate-600">Importando productos...</p>
                </div>
              ) : (
                <>
                  <FileUp className="w-12 h-12 text-slate-400 mx-auto mb-3" strokeWidth={1.5} />
                  <p className="text-slate-600 font-medium mb-1">
                    Arrastra tu archivo aquí o haz clic para seleccionar
                  </p>
                  <p className="text-sm text-slate-400">
                    Formatos soportados: CSV, XLSX, XLS, XML
                  </p>
                </>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Product Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Detalle del Producto</DialogTitle>
            <DialogDescription>
              Información completa del producto
            </DialogDescription>
          </DialogHeader>
          {selectedProduct && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                {selectedProduct.image_url ? (
                  <img
                    src={selectedProduct.image_url}
                    alt={selectedProduct.name}
                    className="w-full h-48 object-cover rounded-sm border border-slate-200"
                  />
                ) : (
                  <div className="w-full h-48 bg-slate-100 rounded-sm flex items-center justify-center">
                    <Package className="w-16 h-16 text-slate-300" strokeWidth={1.5} />
                  </div>
                )}
              </div>
              <div className="space-y-4">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-1">{selectedProduct.name}</h3>
                  {selectedProduct.brand && (
                    <p className="text-sm text-slate-500">{selectedProduct.brand}</p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-500">SKU</p>
                    <p className="font-mono font-medium">{selectedProduct.sku}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">EAN</p>
                    <p className="font-mono font-medium">{selectedProduct.ean || "-"}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Precio</p>
                    <p className="font-mono font-semibold text-lg text-slate-900">
                      {selectedProduct.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Stock</p>
                    <p className="font-mono">{getStockBadge(selectedProduct.stock)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Categoría</p>
                    <p className="font-medium">{selectedProduct.category || "-"}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Peso</p>
                    <p className="font-medium">{selectedProduct.weight ? `${selectedProduct.weight} kg` : "-"}</p>
                  </div>
                </div>
                {selectedProduct.description && (
                  <div>
                    <p className="text-slate-500 text-sm mb-1">Descripción</p>
                    <p className="text-sm text-slate-600">{selectedProduct.description}</p>
                  </div>
                )}
                <Button
                  onClick={() => { handleAddSingleToCatalog(selectedProduct.id); setShowDetailDialog(false); }}
                  className="w-full btn-primary"
                  data-testid="add-to-catalog-detail"
                >
                  <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  Añadir a Mi Catálogo
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SupplierDetail;
