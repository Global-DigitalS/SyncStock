import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { usePagination } from "../hooks/usePagination";
import { useDialogState } from "../hooks/useDialogState";
import { handleApiError } from "../utils/handleApiError";
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
  Trash2,
  FolderTree,
  X,
  Bell,
} from "lucide-react";
import { api } from "../App";
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";
import ProductDetailDialog from "../components/dialogs/ProductDetailDialog";

const COMPLETION_FIELDS = [
  { key: "name", label: "Nombre" },
  { key: "ean", label: "EAN" },
  { key: "description", label: "Descripción" },
  { key: "short_description", label: "Descripción corta" },
  { key: "long_description", label: "Descripción larga" },
  { key: "category", label: "Categoría" },
  { key: "brand", label: "Marca" },
  { key: "image_url", label: "Imagen" },
  { key: "weight", label: "Peso" },
  { key: "best_price", label: "Precio", check: (v) => v != null && v > 0 },
  { key: "total_stock", label: "Stock", check: (v) => v != null && v > 0 },
];

const getProductCompletion = (product) => {
  const results = COMPLETION_FIELDS.map((field) => {
    const value = product[field.key];
    const filled = field.check
      ? field.check(value)
      : value != null && value !== "" && value !== 0;
    return { ...field, filled };
  });
  const filledCount = results.filter((r) => r.filled).length;
  const percentage = Math.round((filledCount / results.length) * 100);
  return { percentage, results };
};

const getCompletionColor = (pct) => {
  if (pct >= 80) return { bar: "bg-emerald-500", text: "text-emerald-700" };
  if (pct >= 50) return { bar: "bg-amber-500", text: "text-amber-700" };
  return { bar: "bg-rose-500", text: "text-rose-700" };
};

const ProductCompletionBar = ({ product }) => {
  const { percentage, results } = getProductCompletion(product);
  const colors = getCompletionColor(percentage);
  const missing = results.filter((r) => !r.filled);

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2 min-w-[100px] cursor-default">
            <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${colors.bar}`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className={`text-xs font-semibold ${colors.text} w-8 text-right`}>
              {percentage}%
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[220px]">
          <p className="font-semibold text-xs mb-1">Completado: {percentage}%</p>
          {missing.length > 0 ? (
            <div className="text-xs">
              <p className="text-slate-400 mb-0.5">Campos vacíos:</p>
              <ul className="list-disc pl-3 space-y-0">
                {missing.map((f) => (
                  <li key={f.key}>{f.label}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-xs text-emerald-400">Todos los campos completos</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

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
  const dialogs = useDialogState(["catalog", "detail", "upload", "edit", "delete"]);
  const [editProduct, setEditProduct] = useState(null);
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const [deletingProducts, setDeletingProducts] = useState(false);
  
  // Category selection for catalog
  const [catalogCategories, setCatalogCategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [loadingCategories, setLoadingCategories] = useState(false);
  
  // Upload states
  const [uploadSupplierId, setUploadSupplierId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  
  // Pagination
  const {
    currentPage,
    pageSize,
    skip,
    total: totalProducts,
    totalPages,
    setTotal: setTotalProducts,
    handlePageChange: paginationHandlePageChange,
    resetPage,
  } = usePagination({ pageSize: 25 });

  // Build query params for current filters
  const buildFilterParams = useCallback(() => {
    const params = new URLSearchParams();
    if (searchTerm) params.append("search", searchTerm);
    if (categoryFilter) params.append("category", categoryFilter);
    if (stockFilter === "available") params.append("min_stock", "1");
    if (stockFilter === "out") params.append("max_stock", "0");
    return params;
  }, [searchTerm, categoryFilter, stockFilter]);

  // Fetch products from API
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = buildFilterParams();
      params.append("skip", String(skip));
      params.append("limit", String(pageSize));

      const response = await api.get(`/products-unified?${params.toString()}`);

      if (Array.isArray(response.data)) {
        setProducts(response.data);
      } else {
        setProducts([]);
      }
    } catch (err) {
      setError(handleApiError(err, "Error al cargar productos", { silent: true }));
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [skip, buildFilterParams]);

  // Fetch count for pagination
  const fetchCount = useCallback(async () => {
    try {
      const params = buildFilterParams();
      const response = await api.get(`/products-unified/count?${params.toString()}`);
      setTotalProducts(response.data?.total || 0);
    } catch (err) {
      setTotalProducts(0);
    }
  }, [buildFilterParams]);

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
      // silently handle auxiliary data errors
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
  }, [fetchProducts, fetchCount]);

  // Handle search — just reset page, the useEffect handles the fetch
  const handleSearch = () => {
    resetPage();
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    paginationHandlePageChange(newPage);
    setSelectedProducts(new Set());
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
    dialogs.open("catalog");
  };

  const handleAddSelectedToCatalogs = () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    openCatalogSelector(Array.from(selectedProducts));
  };

  const toggleCatalogSelection = async (catalogId) => {
    const newSet = new Set(selectedCatalogs);
    if (newSet.has(catalogId)) {
      newSet.delete(catalogId);
    } else {
      newSet.add(catalogId);
      // Load categories for this catalog
      await loadCatalogCategories(catalogId);
    }
    setSelectedCatalogs(newSet);
  };

  // Load categories for selected catalog
  const loadCatalogCategories = async (catalogId) => {
    setLoadingCategories(true);
    try {
      const res = await api.get(`/catalogs/${catalogId}/categories`);
      setCatalogCategories(res.data || []);
    } catch (err) {
      // silently handle category load errors
      setCatalogCategories([]);
    }
    setLoadingCategories(false);
  };

  // Flatten category tree for select dropdown
  const flattenCategories = (categories, level = 0) => {
    let result = [];
    for (const cat of categories) {
      result.push({
        id: cat.id,
        name: cat.name,
        level: level,
        displayName: "─".repeat(level) + (level > 0 ? " " : "") + cat.name
      });
      if (cat.children && cat.children.length > 0) {
        result = result.concat(flattenCategories(cat.children, level + 1));
      }
    }
    return result;
  };

  // Delete products handler
  const handleDeleteProducts = async () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    dialogs.open("delete");
  };

  const confirmDeleteProducts = async () => {
    setDeletingProducts(true);
    try {
      const res = await api.post("/products/delete-bulk", {
        eans: Array.from(selectedProducts)
      });
      toast.success(`${res.data.deleted} productos eliminados`);
      setSelectedProducts(new Set());
      dialogs.close("delete");
      fetchProducts();
    } catch (err) {
      handleApiError(err, "Error al eliminar productos");
    }
    setDeletingProducts(false);
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
        const payload = {
          product_ids: productsToAdd
        };
        // Add category_ids if a category is selected
        if (selectedCategoryId) {
          payload.category_ids = [selectedCategoryId];
        }
        const res = await api.post(`/catalogs/${catalogId}/products`, payload);
        totalAdded += res.data.added || 0;
      } catch (err) {
        // error handled via toast below
      }
    }

    setAddingToCatalog(false);
    dialogs.close("catalog");
    setSelectedProducts(new Set());
    setProductsToAdd([]);
    setSelectedCategoryId("");
    setCatalogCategories([]);

    if (totalAdded > 0) {
      toast.success(`${totalAdded} productos añadidos a los catálogos`);
    } else {
      toast.info("Los productos ya estaban en los catálogos");
    }
  };

  // Product detail
  const openProductDetail = (product) => {
    dialogs.open("detail", product);
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
      dialogs.close("upload");
      setUploadSupplierId("");
      fetchProducts();
      fetchCount();
    } catch (err) {
      handleApiError(err, "Error al importar");
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
    if (stock <= 0) return <Badge className="bg-rose-100 text-rose-700 border-0">Sin stock</Badge>;
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
          <Button onClick={() => dialogs.open("upload")} data-testid="import-csv-btn">
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
            <Select value={categoryFilter || "all"} onValueChange={(v) => { setCategoryFilter(v === "all" ? "" : v); resetPage(); }}>
              <SelectTrigger className="w-full lg:w-[200px]" data-testid="category-filter">
                <SelectValue placeholder="Todas las categorías" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las categorías</SelectItem>
                {categories.filter(Boolean).map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={stockFilter || "all"} onValueChange={(v) => { setStockFilter(v === "all" ? "" : v); resetPage(); }}>
              <SelectTrigger className="w-full lg:w-[150px]" data-testid="stock-filter">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="available">Con stock</SelectItem>
                <SelectItem value="out">Sin stock</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} variant="outline" data-testid="filter-btn">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
            {(searchTerm || categoryFilter || stockFilter) && (
              <Button
                variant="ghost"
                onClick={() => { setSearchTerm(""); setCategoryFilter(""); setStockFilter(""); resetPage(); }}
                className="text-slate-500 hover:text-slate-700"
                data-testid="clear-filters-btn"
              >
                <X className="w-4 h-4 mr-1" />
                Limpiar
              </Button>
            )}
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
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleDeleteProducts}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                  data-testid="delete-products-btn"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Eliminar
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
                  <TableHead className="w-[140px]">Completado</TableHead>
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
                      <ProductCompletionBar product={product} />
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
      <Dialog open={dialogs.isOpen("detail")} onOpenChange={(v) => !v && dialogs.close("detail")}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Detalle del Producto</DialogTitle>
            <DialogDescription>{dialogs.selected?.name}</DialogDescription>
          </DialogHeader>
          
          {dialogs.selected && (
            <div className="space-y-6 py-4">
              {/* Product Info */}
              <div className="flex gap-4">
                <div className="w-20 h-20 flex-shrink-0">
                  {dialogs.selected.image_url ? (
                    <img src={dialogs.selected.image_url} alt={dialogs.selected.name} className="w-full h-full object-cover rounded-lg border" />
                  ) : (
                    <div className="w-full h-full bg-slate-100 rounded-lg flex items-center justify-center">
                      <Package className="w-8 h-8 text-slate-300" />
                    </div>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{dialogs.selected.name}</h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <Badge className="bg-slate-100 text-slate-700 border-0 font-mono text-xs">EAN: {dialogs.selected.ean}</Badge>
                    {dialogs.selected.brand && <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">{dialogs.selected.brand}</Badge>}
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
                        <p className="text-lg font-bold text-emerald-700">{dialogs.selected.best_supplier}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-700">
                        {dialogs.selected.best_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </p>
                      <p className={`text-sm ${dialogs.selected.total_stock <= 0 ? 'text-rose-600 font-semibold' : 'text-emerald-600'}`}>
                        {dialogs.selected.total_stock <= 0 ? 'Sin stock' : `Stock: ${dialogs.selected.total_stock} uds`}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* All Suppliers */}
              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">
                  Todos los Proveedores ({dialogs.selected.supplier_count})
                </h4>
                <div className="space-y-2">
                  {dialogs.selected.suppliers?.map((supplier, idx) => (
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
            <Button variant="outline" onClick={() => dialogs.close("detail")}>Cerrar</Button>
            <Button 
              variant="outline"
              onClick={async () => { 
                if (dialogs.selected && dialogs.selected.best_supplier_id) { 
                  // Find the best supplier's product_id from suppliers array
                  const bestSupplier = dialogs.selected.suppliers?.find(s => s.is_best_offer);
                  if (bestSupplier?.product_id) {
                    try {
                      const res = await api.get(`/products/${bestSupplier.product_id}`);
                      setEditProduct(res.data);
                      dialogs.close("detail");
                      dialogs.open("edit");
                    } catch (err) {
                      handleApiError(err, "Error al cargar el producto para editar");
                    }
                  }
                } 
              }}
              data-testid="edit-product-btn"
            >
              <Pencil className="w-4 h-4 mr-2" />
              Editar
            </Button>
            <Button onClick={() => { if (dialogs.selected) { openCatalogSelector([dialogs.selected.ean]); dialogs.close("detail"); } }}>
              <BookOpen className="w-4 h-4 mr-2" />
              Añadir a Catálogo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Product Edit Dialog */}
      <ProductDetailDialog
        open={dialogs.isOpen("edit")}
        onOpenChange={(v) => !v && dialogs.close("edit")}
        product={editProduct}
        onProductUpdate={() => fetchProducts()}
      />

      {/* Catalog Selection Dialog */}
      <Dialog open={dialogs.isOpen("catalog")} onOpenChange={(open) => {
        if (!open) {
          dialogs.close("catalog");
          setSelectedCategoryId("");
          setCatalogCategories([]);
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Añadir a Catálogos
            </DialogTitle>
            <DialogDescription>Selecciona los catálogos donde añadir los productos</DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            {/* Catalog list */}
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {catalogs.length === 0 ? (
                <div className="text-center py-6">
                  <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-slate-500">No hay catálogos</p>
                  <Button variant="link" onClick={() => { dialogs.close("catalog"); navigate("/catalogs"); }}>
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
            
            {/* Category selector - shown when a catalog is selected */}
            {selectedCatalogs.size > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-200">
                <label className="text-sm font-medium flex items-center gap-2">
                  <FolderTree className="w-4 h-4 text-slate-500" />
                  Categoría del catálogo (opcional)
                </label>
                <Select 
                  value={selectedCategoryId || "none"} 
                  onValueChange={(v) => setSelectedCategoryId(v === "none" ? "" : v)}
                >
                  <SelectTrigger data-testid="category-select">
                    <SelectValue placeholder="Sin categoría específica" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin categoría específica</SelectItem>
                    {loadingCategories ? (
                      <SelectItem value="loading" disabled>Cargando...</SelectItem>
                    ) : (
                      flattenCategories(catalogCategories).map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.displayName}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">
                  Los productos se añadirán a esta categoría dentro del catálogo
                </p>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => dialogs.close("catalog")}>Cancelar</Button>
            <Button onClick={handleConfirmAddToCatalogs} disabled={addingToCatalog || selectedCatalogs.size === 0}>
              {addingToCatalog ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              Añadir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={dialogs.isOpen("delete")} onOpenChange={(v) => !v && dialogs.close("delete")}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <Trash2 className="w-5 h-5" />
              Eliminar Productos
            </DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que deseas eliminar {selectedProducts.size} producto{selectedProducts.size !== 1 ? "s" : ""}?
              Esta acción no se puede deshacer y también los eliminará de todos los catálogos.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => dialogs.close("delete")}>
              Cancelar
            </Button>
            <Button 
              variant="destructive" 
              onClick={confirmDeleteProducts}
              disabled={deletingProducts}
              data-testid="confirm-delete-btn"
            >
              {deletingProducts ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog open={dialogs.isOpen("upload")} onOpenChange={(v) => !v && dialogs.close("upload")}>
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
            <Button variant="outline" onClick={() => dialogs.close("upload")}>Cancelar</Button>
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
