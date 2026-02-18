import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
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
  Package,
  Search,
  Upload,
  Filter,
  Plus,
  X,
  Eye,
  ExternalLink,
  FileUp
} from "lucide-react";

const Products = () => {
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    supplier_id: "",
    category: "",
    stock: searchParams.get("stock") || ""
  });
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [uploadSupplierId, setUploadSupplierId] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [productsRes, suppliersRes, categoriesRes] = await Promise.all([
        api.get("/products", { params: buildQueryParams() }),
        api.get("/suppliers"),
        api.get("/products/categories")
      ]);
      setProducts(productsRes.data);
      setSuppliers(suppliersRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error("Error al cargar los productos");
    } finally {
      setLoading(false);
    }
  }, []);

  const buildQueryParams = () => {
    const params = {};
    if (filters.search) params.search = filters.search;
    if (filters.supplier_id) params.supplier_id = filters.supplier_id;
    if (filters.category) params.category = filters.category;
    if (filters.stock === "low") {
      params.min_stock = 1;
      params.max_stock = 5;
    } else if (filters.stock === "out") {
      params.max_stock = 0;
    }
    return params;
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await api.get("/products", { params: buildQueryParams() });
      setProducts(res.data);
    } catch (error) {
      toast.error("Error al buscar productos");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!uploadSupplierId) {
      toast.error("Selecciona un proveedor");
      return;
    }

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
      const res = await api.post(`/products/import/${uploadSupplierId}`, formData, {
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

  const handleAddToCatalog = async (productId) => {
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

  if (loading && products.length === 0) {
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
            Productos
          </h1>
          <p className="text-slate-500">
            {products.length.toLocaleString()} productos de tus proveedores
          </p>
        </div>
        <Button onClick={() => setShowUploadDialog(true)} className="btn-primary" data-testid="import-products-btn">
          <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Importar Productos
        </Button>
      </div>

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
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-9 input-base"
                data-testid="search-products"
              />
            </div>
            <Select
              value={filters.supplier_id || "all"}
              onValueChange={(value) => setFilters({ ...filters, supplier_id: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full lg:w-[200px] input-base" data-testid="filter-supplier">
                <SelectValue placeholder="Todos los proveedores" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los proveedores</SelectItem>
                {suppliers.map((s) => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.category || "all"}
              onValueChange={(value) => setFilters({ ...filters, category: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full lg:w-[180px] input-base" data-testid="filter-category">
                <SelectValue placeholder="Todas las categorías" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las categorías</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.stock || "all"}
              onValueChange={(value) => setFilters({ ...filters, stock: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full lg:w-[150px] input-base" data-testid="filter-stock">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="low">Stock bajo</SelectItem>
                <SelectItem value="out">Sin stock</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} className="btn-secondary" data-testid="apply-filters">
              <Filter className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      {products.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Package className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay productos
          </h3>
          <p className="text-slate-500 mb-4">
            Importa productos desde tus proveedores para comenzar
          </p>
          <Button onClick={() => setShowUploadDialog(true)} className="btn-primary" data-testid="empty-import-btn">
            <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Importar Productos
          </Button>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Proveedor</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id} className="table-row" data-testid={`product-row-${product.id}`}>
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
                      <span className="text-sm text-slate-600">{product.supplier_name}</span>
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
                          onClick={() => handleAddToCatalog(product.id)}
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
            <DialogDescription>Selecciona un proveedor y sube el archivo de productos</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Seleccionar proveedor *</label>
              <Select value={uploadSupplierId} onValueChange={setUploadSupplierId}>
                <SelectTrigger className="input-base" data-testid="upload-supplier-select">
                  <SelectValue placeholder="Seleccionar proveedor" />
                </SelectTrigger>
                <SelectContent>
                  {suppliers.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

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
                    <p className="text-slate-500">Proveedor</p>
                    <p className="font-medium">{selectedProduct.supplier_name}</p>
                  </div>
                </div>
                {selectedProduct.description && (
                  <div>
                    <p className="text-slate-500 text-sm mb-1">Descripción</p>
                    <p className="text-sm text-slate-600">{selectedProduct.description}</p>
                  </div>
                )}
                <Button
                  onClick={() => { handleAddToCatalog(selectedProduct.id); setShowDetailDialog(false); }}
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

export default Products;
