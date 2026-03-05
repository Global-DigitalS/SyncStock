import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
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
  DialogFooter,
} from "../components/ui/dialog";
import {
  Package,
  Search,
  Filter,
  Eye,
  BookOpen,
  Star,
  RefreshCw,
  Plus,
  CheckSquare,
  Truck,
  TrendingDown,
  AlertTriangle,
  Upload,
  FileUp,
  ChevronLeft,
  ChevronRight,
  Pencil,
} from "lucide-react";
import ProductDetailDialog from "../components/dialogs/ProductDetailDialog";

const Products = () => {
  const navigate = useNavigate();
  
  // Data states
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  
  // UI states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [stockFilter, setStockFilter] = useState("");
  
  // Selection states
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());
  
  // Dialog states
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [editProduct, setEditProduct] = useState(null);
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  
  // Upload states
  const [uploadSupplierId, setUploadSupplierId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const pageSize = 25;
  const totalPages = Math.ceil(totalProducts / pageSize);

  // Fetch products from API
  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      params.append("skip", String((currentPage - 1) * pageSize));
      params.append("limit", String(pageSize));
      
      if (searchTerm) params.append("search", searchTerm);
      if (categoryFilter) params.append("category", categoryFilter);
      if (stockFilter === "available") params.append("min_stock", "1");

      const url = `/products-unified?${params.toString()}`;
      console.log("[Products] Fetching:", url);
      
      const response = await api.get(url);
      console.log("[Products] Response:", response.data?.length || 0, "items");
      
      if (Array.isArray(response.data)) {
        setProducts(response.data);
      } else {
        console.error("[Products] Response is not an array:", response.data);
        setProducts([]);
      }
    } catch (err) {
      console.error("[Products] Fetch error:", err);
      setError(err.response?.data?.detail || err.message || "Error al cargar productos");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch count for pagination
  const fetchCount = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append("search", searchTerm);
      if (categoryFilter) params.append("category", categoryFilter);
      if (stockFilter === "available") params.append("min_stock", "1");

      const response = await api.get(`/products-unified/count?${params.toString()}`);
      setTotalProducts(response.data?.total || 0);
    } catch (err) {
      console.error("[Products] Count error:", err);
      setTotalProducts(0);
    }
  };

  // Fetch auxiliary data
  const fetchAuxiliaryData = async () => {
    try {
      const [catRes, supRes, catalogRes] = await Promise.all([
        api.get("/products/categories"),
        api.get("/suppliers"),
        api.get("/catalogs")
      ]);
      setCategories(catRes.data || []);
      setSuppliers(supRes.data || []);
      setCatalogs(catalogRes.data || []);
    } catch (err) {
      console.error("[Products] Auxiliary data error:", err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchAuxiliaryData();
  }, []);

  // Fetch products when filters or page change
  useEffect(() => {
    fetchProducts();
    fetchCount();
  }, [currentPage, searchTerm, categoryFilter, stockFilter]);

  // Handle search
  const handleSearch = () => {
    setCurrentPage(1);
    fetchProducts();
    fetchCount();
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      setSelectedProducts(new Set());
    }
  };

  // Selection handlers
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedProducts(new Set(products.map(p => p.ean)));
    } else {
      setSelectedProducts(new Set());
    }
  };

  const handleSelectProduct = (ean, checked) => {
    const newSet = new Set(selectedProducts);
    if (checked) {
      newSet.add(ean);
    } else {
      newSet.delete(ean);
    }
    setSelectedProducts(newSet);
  };

  // Get best product_ids for selected EANs
  const getBestProductIds = (eans) => {
    const productIds = [];
    for (const ean of eans) {
      const product = products.find(p => p.ean === ean);
      if (product) {
        const bestOffer = product.suppliers?.find(s => s.is_best_offer);
        if (bestOffer) {
          productIds.push(bestOffer.product_id);
        }
      }
    }
    return productIds;
  };

  // Catalog handlers
  const openCatalogSelector = (eans) => {
    if (catalogs.length === 0) {
      toast.error("No hay catálogos creados. Crea uno primero.");
      return;
    }
    const productIds = getBestProductIds(eans);
    setProductsToAdd(productIds);
    const defaultCatalog = catalogs.find(c => c.is_default);
    setSelectedCatalogs(defaultCatalog ? new Set([defaultCatalog.id]) : new Set());
    setShowCatalogDialog(true);
  };

  const handleAddSelectedToCatalogs = () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    openCatalogSelector(Array.from(selectedProducts));
  };

  const toggleCatalogSelection = (catalogId) => {
    const newSet = new Set(selectedCatalogs);
    if (newSet.has(catalogId)) {
      newSet.delete(catalogId);
    } else {
      newSet.add(catalogId);
    }
    setSelectedCatalogs(newSet);
  };

  const handleConfirmAddToCatalogs = async () => {
    if (selectedCatalogs.size === 0) {
      toast.error("Selecciona al menos un catálogo");
      return;
    }

    setAddingToCatalog(true);
    let totalAdded = 0;

    for (const catalogId of selectedCatalogs) {
      try {
        const res = await api.post(`/catalogs/${catalogId}/products`, {
          product_ids: productsToAdd
        });
        totalAdded += res.data.added || 0;
      } catch (err) {
        console.error("Error adding to catalog:", err);
      }
    }

    setAddingToCatalog(false);
    setShowCatalogDialog(false);
    setSelectedProducts(new Set());
    setProductsToAdd([]);

    if (totalAdded > 0) {
      toast.success(`${totalAdded} productos añadidos a los catálogos`);
    } else {
      toast.info("Los productos ya estaban en los catálogos");
    }
  };

  // Product detail
  const openProductDetail = (product) => {
    setSelectedProduct(product);
    setShowDetailDialog(true);
  };

  // File upload handlers
  const handleFileUpload = async (file) => {
    if (!uploadSupplierId) {
      toast.error("Selecciona un proveedor primero");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      const res = await api.post(`/suppliers/${uploadSupplierId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(`${res.data.imported} productos importados`);
      setShowUploadDialog(false);
      setUploadSupplierId("");
      fetchProducts();
      fetchCount();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al importar");
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Stock badge helper
  const getStockBadge = (stock) => {
    if (stock === 0) return <Badge className="bg-rose-100 text-rose-700 border-0">Sin stock</Badge>;
    if (stock <= 5) return <Badge className="bg-amber-100 text-amber-700 border-0">{stock} uds</Badge>;
    return <Badge className="bg-emerald-100 text-emerald-700 border-0">{stock} uds</Badge>;
  };

  // Loading state
  if (loading && products.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" data-testid="loading-state">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
        <p className="text-slate-500">Cargando productos...</p>
      </div>
    );
  }

  // Error state
  if (error && products.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" data-testid="error-state">
        <AlertTriangle className="w-12 h-12 text-rose-500" />
        <h2 className="text-xl font-semibold text-slate-900">Error al cargar productos</h2>
        <p className="text-slate-500">{error}</p>
        <Button onClick={() => { fetchProducts(); fetchCount(); }} className="mt-4">
          <RefreshCw className="w-4 h-4 mr-2" />
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Productos
          </h1>
          <p className="text-slate-500" data-testid="products-count-text">
            {totalProducts > 0 
              ? `${totalProducts.toLocaleString()} productos seleccionados`
              : "No hay productos seleccionados"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => navigate("/suppliers")} data-testid="go-to-suppliers-btn">
            <Truck className="w-4 h-4 mr-2" />
            Ir a Proveedores
          </Button>
          <Button onClick={() => setShowUploadDialog(true)} data-testid="import-csv-btn">
            <Upload className="w-4 h-4 mr-2" />
            Importar CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar por nombre, SKU o EAN..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-9"
                data-testid="search-input"
              />
            </div>
            <Select value={categoryFilter || "all"} onValueChange={(v) => { setCategoryFilter(v === "all" ? "" : v); setCurrentPage(1); }}>
              <SelectTrigger className="w-full lg:w-[200px]" data-testid="category-filter">
                <SelectValue placeholder="Todas las categorías" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las categorías</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={stockFilter || "all"} onValueChange={(v) => { setStockFilter(v === "all" ? "" : v); setCurrentPage(1); }}>
              <SelectTrigger className="w-full lg:w-[150px]" data-testid="stock-filter">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="available">Con stock</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} variant="outline" data-testid="filter-btn">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Selection Banner */}
      {selectedProducts.size > 0 && (
        <Card className="border-indigo-200 bg-indigo-50 mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckSquare className="w-5 h-5 text-indigo-600" />
                <span className="font-medium text-indigo-900">
                  {selectedProducts.size} producto{selectedProducts.size !== 1 ? "s" : ""} seleccionado{selectedProducts.size !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setSelectedProducts(new Set())}>
                  Limpiar
                </Button>
                <Button size="sm" onClick={handleAddSelectedToCatalogs} disabled={addingToCatalog} data-testid="add-to-catalogs-btn">
                  {addingToCatalog ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <BookOpen className="w-4 h-4 mr-2" />}
                  Añadir a Catálogos
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Products Table or Empty State */}
      {products.length === 0 ? (
        <div className="text-center py-16" data-testid="empty-state">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
            <Package className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No hay productos</h3>
          <p className="text-slate-500 mb-6 max-w-md mx-auto">
            {searchTerm || categoryFilter 
              ? "Prueba con otros filtros de búsqueda" 
              : "Selecciona productos desde Proveedores para verlos aquí"}
          </p>
          {!searchTerm && !categoryFilter && (
            <Button onClick={() => navigate("/suppliers")} data-testid="empty-go-suppliers">
              <Truck className="w-4 h-4 mr-2" />
              Ir a Proveedores
            </Button>
          )}
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table data-testid="products-table">
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="w-[50px]">
                    <Checkbox
                      checked={selectedProducts.size === products.length && products.length > 0}
                      onCheckedChange={handleSelectAll}
                      data-testid="select-all-checkbox"
                    />
                  </TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>EAN</TableHead>
                  <TableHead>Mejor Proveedor</TableHead>
                  <TableHead className="text-right">Mejor Precio</TableHead>
                  <TableHead className="text-right">Stock Total</TableHead>
                  <TableHead className="text-center">Proveedores</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow 
                    key={product.ean} 
                    className={selectedProducts.has(product.ean) ? 'bg-indigo-50' : ''}
                    data-testid={`product-row-${product.ean}`}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedProducts.has(product.ean)}
                        onCheckedChange={(checked) => handleSelectProduct(product.ean, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3 max-w-[300px]">
                        {product.image_url ? (
                          <img src={product.image_url} alt={product.name} className="w-10 h-10 object-cover rounded border" />
                        ) : (
                          <div className="w-10 h-10 bg-slate-100 rounded flex items-center justify-center">
                            <Package className="w-5 h-5 text-slate-400" />
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900 truncate">{product.name}</p>
                          {product.brand && <p className="text-xs text-slate-500">{product.brand}</p>}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-sm text-slate-600">{product.ean}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <TrendingDown className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm font-medium">{product.best_supplier}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono font-semibold text-emerald-600">
                        {product.best_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {getStockBadge(product.total_stock)}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge className="bg-slate-100 text-slate-700 border-0">
                        <Truck className="w-3 h-3 mr-1" />
                        {product.supplier_count}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => openProductDetail(product)} className="h-8 w-8 p-0" data-testid={`view-${product.ean}`}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => openCatalogSelector([product.ean])} className="h-8 w-8 p-0 text-indigo-600" data-testid={`catalog-${product.ean}`}>
                          <BookOpen className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t" data-testid="pagination">
              <p className="text-sm text-slate-500">
                Página {currentPage} de {totalPages} ({totalProducts} productos)
              </p>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Product Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Detalle del Producto</DialogTitle>
            <DialogDescription>{selectedProduct?.name}</DialogDescription>
          </DialogHeader>
          
          {selectedProduct && (
            <div className="space-y-6 py-4">
              {/* Product Info */}
              <div className="flex gap-4">
                <div className="w-20 h-20 flex-shrink-0">
                  {selectedProduct.image_url ? (
                    <img src={selectedProduct.image_url} alt={selectedProduct.name} className="w-full h-full object-cover rounded-lg border" />
                  ) : (
                    <div className="w-full h-full bg-slate-100 rounded-lg flex items-center justify-center">
                      <Package className="w-8 h-8 text-slate-300" />
                    </div>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{selectedProduct.name}</h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <Badge className="bg-slate-100 text-slate-700 border-0 font-mono text-xs">EAN: {selectedProduct.ean}</Badge>
                    {selectedProduct.brand && <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">{selectedProduct.brand}</Badge>}
                  </div>
                </div>
              </div>

              {/* Best Offer */}
              <Card className="border-emerald-200 bg-emerald-50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                        <Star className="w-5 h-5 text-emerald-600" />
                      </div>
                      <div>
                        <p className="text-sm text-emerald-600 font-medium">Mejor Oferta</p>
                        <p className="text-lg font-bold text-emerald-700">{selectedProduct.best_supplier}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-700">
                        {selectedProduct.best_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </p>
                      <p className="text-sm text-emerald-600">Stock: {selectedProduct.total_stock} uds</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* All Suppliers */}
              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">
                  Todos los Proveedores ({selectedProduct.supplier_count})
                </h4>
                <div className="space-y-2">
                  {selectedProduct.suppliers?.map((supplier, idx) => (
                    <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                      supplier.is_best_offer ? "bg-emerald-50 border-emerald-200" : "bg-white border-slate-200"
                    }`}>
                      <div className="flex items-center gap-3">
                        <Truck className={`w-4 h-4 ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-500"}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{supplier.supplier_name}</p>
                            {supplier.is_best_offer && <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">Mejor</Badge>}
                          </div>
                          <p className="text-xs text-slate-500 font-mono">SKU: {supplier.sku}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-900"}`}>
                          {supplier.price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                        </p>
                        {supplier.stock > 0 ? (
                          <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">{supplier.stock} uds</Badge>
                        ) : (
                          <Badge className="bg-rose-100 text-rose-700 border-0 text-xs">Sin stock</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Cerrar</Button>
            <Button 
              variant="outline"
              onClick={async () => { 
                if (selectedProduct && selectedProduct.best_supplier_id) { 
                  // Find the best supplier's product_id from suppliers array
                  const bestSupplier = selectedProduct.suppliers?.find(s => s.is_best_offer);
                  if (bestSupplier?.product_id) {
                    try {
                      const res = await api.get(`/products/${bestSupplier.product_id}`);
                      setEditProduct(res.data);
                      setShowEditDialog(true);
                      setShowDetailDialog(false);
                    } catch (err) {
                      toast.error("Error al cargar el producto para editar");
                    }
                  }
                } 
              }}
              data-testid="edit-product-btn"
            >
              <Pencil className="w-4 h-4 mr-2" />
              Editar
            </Button>
            <Button onClick={() => { if (selectedProduct) { openCatalogSelector([selectedProduct.ean]); setShowDetailDialog(false); } }}>
              <BookOpen className="w-4 h-4 mr-2" />
              Añadir a Catálogo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Product Edit Dialog */}
      <ProductDetailDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        product={editProduct}
        onProductUpdate={() => fetchProducts()}
      />

      {/* Catalog Selection Dialog */}
      <Dialog open={showCatalogDialog} onOpenChange={setShowCatalogDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Añadir a Catálogos
            </DialogTitle>
            <DialogDescription>Selecciona los catálogos donde añadir los productos</DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-2 max-h-[300px] overflow-y-auto">
            {catalogs.length === 0 ? (
              <div className="text-center py-6">
                <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">No hay catálogos</p>
                <Button variant="link" onClick={() => { setShowCatalogDialog(false); navigate("/catalogs"); }}>
                  Crear catálogo
                </Button>
              </div>
            ) : (
              catalogs.map((catalog) => (
                <div
                  key={catalog.id}
                  onClick={() => toggleCatalogSelection(catalog.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedCatalogs.has(catalog.id) ? "bg-indigo-50 border-indigo-300" : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                  data-testid={`catalog-option-${catalog.id}`}
                >
                  <Checkbox checked={selectedCatalogs.has(catalog.id)} onCheckedChange={() => toggleCatalogSelection(catalog.id)} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{catalog.name}</span>
                      {catalog.is_default && <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs"><Star className="w-3 h-3 mr-1" />Defecto</Badge>}
                    </div>
                    <p className="text-xs text-slate-500">{catalog.product_count} productos</p>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCatalogDialog(false)}>Cancelar</Button>
            <Button onClick={handleConfirmAddToCatalogs} disabled={addingToCatalog || selectedCatalogs.size === 0}>
              {addingToCatalog ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              Añadir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-indigo-600" />
              Importar Productos
            </DialogTitle>
            <DialogDescription>Sube un archivo CSV con tus productos</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Proveedor</label>
              <Select value={uploadSupplierId} onValueChange={setUploadSupplierId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona un proveedor" />
                </SelectTrigger>
                <SelectContent>
                  {suppliers.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? "border-indigo-400 bg-indigo-50" : "border-slate-300"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.xml"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              />
              <FileUp className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-600 mb-2">
                Arrastra tu archivo o{" "}
                <button type="button" onClick={() => fileInputRef.current?.click()} className="text-indigo-600 hover:underline font-medium">
                  selecciona
                </button>
              </p>
              <p className="text-xs text-slate-500">CSV, Excel o XML</p>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadDialog(false)}>Cancelar</Button>
            <Button onClick={() => fileInputRef.current?.click()} disabled={uploading || !uploadSupplierId}>
              {uploading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
              Importar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Products;
