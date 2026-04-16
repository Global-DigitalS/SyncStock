import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useSyncProgress, SYNC_STEPS } from "../contexts/SyncProgressContext";
import {
  Package,
  Search,
  Eye,
  CheckSquare,
  ShoppingCart,
  CheckCircle,
  XCircle,
  ArrowRight,
  Layers,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  X,
  Upload,
  BookOpen,
} from "lucide-react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent } from "../components/ui/card";
import { Checkbox } from "../components/ui/checkbox";
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
import { CategoryCascadeFilter, CategorySelectionCascade } from "../components/suppliers";
import ProductDetailDialog from "../components/dialogs/ProductDetailDialog";
import {
  SupplierHeader,
  SyncStatusBanner,
  SupplierInfoCard,
  ColumnMappingAlert,
  SelectionActionsBar,
  UploadDialog,
  CatalogSelectionDialog,
} from "../components/supplier";

const SupplierDetail = () => {
  const { supplierId } = useParams();
  const navigate = useNavigate();
  const [supplier, setSupplier] = useState(null);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [selectionStats, setSelectionStats] = useState({ selected: 0, total: 0 });
  const [filters, setFilters] = useState({
    search: "",
    category: "",
    subcategory: "",
    subcategory2: "",
    stock: "all",
    selection: "all",
    brand: "",
    part_number: "",
    min_price: "",
    max_price: "",
    min_stock: ""
  });
  const [categoryHierarchy, setCategoryHierarchy] = useState([]);
  const [brands, setBrands] = useState([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [catalogs, setCatalogs] = useState([]);
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [selectingProducts, setSelectingProducts] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const pageSize = 50;

  const fetchData = useCallback(async (page = currentPage) => {
    try {
      const productParams = new URLSearchParams();
      productParams.append("skip", String((page - 1) * pageSize));
      productParams.append("limit", String(pageSize));
      if (filters.search) productParams.append("search", filters.search);
      if (filters.category) productParams.append("category", filters.category);
      if (filters.subcategory) productParams.append("subcategory", filters.subcategory);
      if (filters.subcategory2) productParams.append("subcategory2", filters.subcategory2);
      if (filters.selection === "selected") productParams.append("is_selected", "true");
      if (filters.selection === "unselected") productParams.append("is_selected", "false");
      if (filters.brand) productParams.append("brand", filters.brand);
      if (filters.part_number) productParams.append("part_number", filters.part_number);
      if (filters.min_price) productParams.append("min_price", filters.min_price);
      if (filters.max_price) productParams.append("max_price", filters.max_price);
      if (filters.min_stock) productParams.append("min_stock", filters.min_stock);

      const [supplierRes, productsRes, countRes, categoriesRes, syncStatusRes, catalogsRes, hierarchyRes, selectionStatsRes, brandsRes] = await Promise.all([
        api.get(`/suppliers/${supplierId}`),
        api.get(`/supplier/${supplierId}/products?${productParams.toString()}`),
        api.get(`/supplier/${supplierId}/products/count?${productParams.toString()}`),
        api.get("/products/categories"),
        api.get(`/suppliers/${supplierId}/sync-status`).catch(() => ({ data: null })),
        api.get("/catalogs"),
        api.get(`/products/category-hierarchy?supplier_id=${supplierId}`).catch(() => ({ data: [] })),
        api.get("/products/selected-count", { params: { supplier_id: supplierId } }).catch(() => ({ data: { selected: 0, total: 0 } })),
        api.get("/products/brands", { params: { supplier_id: supplierId } }).catch(() => ({ data: [] }))
      ]);
      setSupplier(supplierRes.data);
      setProducts(productsRes.data);
      setTotalProducts(countRes.data?.total || 0);
      setCategories(categoriesRes.data);
      setSyncStatus(syncStatusRes.data);
      setCatalogs(catalogsRes.data);
      setCategoryHierarchy(hierarchyRes.data || []);
      setSelectionStats(selectionStatsRes.data);
      setBrands(brandsRes.data || []);
      setCurrentPage(page);
    } catch (error) {
      toast.error("Error al cargar los datos del proveedor");
      navigate("/suppliers");
    } finally {
      setLoading(false);
    }
  }, [supplierId, navigate, filters, currentPage]);

  useEffect(() => {
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supplierId]);

  useEffect(() => {
    if (!loading) {
      fetchData(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.category, filters.subcategory, filters.subcategory2, filters.selection]);

  const handleSearch = () => {
    fetchData(1);
  };

  const handlePageChange = (newPage) => {
    const totalPages = Math.ceil(totalProducts / pageSize);
    if (newPage >= 1 && newPage <= totalPages) {
      setSelectedProducts(new Set());
      fetchData(newPage);
    }
  };

  const handleApplyPreset = async () => {
    if (!supplier?.preset_id) return;
    setSyncing(true);
    try {
      await api.post(`/suppliers/${supplierId}/apply-preset`, { preset_id: supplier.preset_id });
      const syncRes = await api.post(`/suppliers/${supplierId}/sync`);
      if (syncRes.data.status === "queued") {
        toast.info("Plantilla aplicada. Sincronización iniciada en segundo plano...");
        toast.success("Sincronización completada");
      } else if (syncRes.data.imported + syncRes.data.updated > 0) {
        toast.success(`Plantilla aplicada y sincronización completada: ${syncRes.data.imported} nuevos, ${syncRes.data.updated} actualizados`);
      } else {
        toast.warning(syncRes.data.message || "Plantilla aplicada pero no se importaron productos.");
      }
      fetchData(1);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al aplicar la plantilla");
    } finally {
      setSyncing(false);
    }
  };

  const { startSync, completeSync, failSync } = useSyncProgress();

  const handleSync = async () => {
    const syncTitle = `Sincronizando ${supplier?.name || "Proveedor"}`;
    startSync(supplierId, syncTitle, SYNC_STEPS.supplier);
    setSyncing(true);

    try {
      const res = await api.post(`/suppliers/${supplierId}/sync`);

      if (res.data.status === "queued") {
        return;
      }

      if (res.data.needs_mapping) {
        toast.warning(res.data.message || "Se necesita configurar el mapeo de columnas", {
          duration: 8000,
          description: `Columnas detectadas: ${(res.data.detected_columns || []).slice(0, 5).join(", ")}...`
        });
        completeSync(supplierId, "Requiere mapeo de columnas");
      } else if (res.data.status === "success" && res.data.imported + res.data.updated > 0) {
        const summary = `${res.data.imported} nuevos, ${res.data.updated} actualizados`;
        completeSync(supplierId, summary);
      } else if (res.data.errors > 0 && res.data.imported + res.data.updated === 0) {
        toast.warning("Archivo descargado pero no se importaron productos. Verifica el mapeo de columnas.", {
          duration: 6000
        });
        completeSync(supplierId, "Sin importaciones");
      } else {
        completeSync(supplierId, "Completado sin cambios");
      }

      fetchData();
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.response?.data?.detail || "Error en la sincronización";
      failSync(supplierId, errorMsg);
      toast.error(errorMsg);
    } finally {
      setSyncing(false);
    }
  };

  const filteredProducts = products.filter((product) => {
    if (filters.stock === "low" && (product.stock <= 0 || product.stock > 5)) return false;
    if (filters.stock === "out" && product.stock > 0) return false;
    if (filters.stock === "in" && product.stock <= 0) return false;
    return true;
  });

  const totalPages = Math.ceil(totalProducts / pageSize);

  const handleSelectProductsForMain = async () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select", { product_ids: Array.from(selectedProducts) });
      toast.success(`${res.data.selected} productos añadidos a la sección Productos`);
      setSelectedProducts(new Set());
      fetchData();
    } catch (error) {
      toast.error("Error al seleccionar productos");
    } finally {
      setSelectingProducts(false);
    }
  };

  const handleDeselectProductsFromMain = async () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/deselect", { product_ids: Array.from(selectedProducts) });
      toast.success(`${res.data.deselected} productos quitados de la sección Productos`);
      setSelectedProducts(new Set());
      fetchData();
    } catch (error) {
      toast.error("Error al deseleccionar productos");
    } finally {
      setSelectingProducts(false);
    }
  };

  const handleSelectByCategory = async (category, subcategory = null, subcategory2 = null, selectAll = true) => {
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select-by-supplier", {
        supplier_id: supplierId,
        category: category || null,
        subcategory: subcategory || null,
        subcategory2: subcategory2 || null,
        select_all: selectAll
      });
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error("Error al seleccionar productos");
    } finally {
      setSelectingProducts(false);
    }
  };

  const handleDeselectByCategory = async (category, subcategory = null, subcategory2 = null) => {
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select-by-supplier", {
        supplier_id: supplierId,
        category: category || null,
        subcategory: subcategory || null,
        subcategory2: subcategory2 || null,
        select_all: false
      });
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error("Error al deseleccionar productos");
    } finally {
      setSelectingProducts(false);
    }
  };

  const handleSelectAllFromSupplier = async (selectAll = true) => {
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select-by-supplier", {
        supplier_id: supplierId,
        select_all: selectAll
      });
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error("Error al seleccionar productos");
    } finally {
      setSelectingProducts(false);
    }
  };

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

  const toggleProductSelection = (productId) => {
    setSelectedProducts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) newSet.delete(productId);
      else newSet.add(productId);
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

  const openCatalogSelector = (productIds) => {
    if (catalogs.length === 0) {
      toast.error("No hay catálogos creados. Crea uno primero en la sección Catálogos.");
      return;
    }
    setProductsToAdd(productIds);
    setShowCatalogDialog(true);
  };

  const handleAddSelectedToCatalog = () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    openCatalogSelector(Array.from(selectedProducts));
  };

  const handleAddSingleToCatalog = (productId) => {
    openCatalogSelector([productId]);
  };

  const handleConfirmAddToCatalogs = async (selectedCatalogs) => {
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
      } catch (error) {
        // handled silently
      }
    }

    setAddingToCatalog(false);
    setShowCatalogDialog(false);
    setSelectedProducts(new Set());
    setProductsToAdd([]);

    const catalogNames = catalogs
      .filter(c => selectedCatalogs.has(c.id))
      .map(c => c.name)
      .join(", ");

    if (totalAdded > 0) {
      toast.success(`Productos añadidos a: ${catalogNames}`);
    } else {
      toast.info("Los productos ya estaban en los catálogos seleccionados");
    }
  };

  const getStockBadge = (stock) => {
    if (stock <= 0) return <span className="badge-error">Sin stock</span>;
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
      <SupplierHeader
        supplier={supplier}
        syncing={syncing}
        onBack={() => navigate("/suppliers")}
        onSync={handleSync}
        onUpload={() => setShowUploadDialog(true)}
      />

      <SyncStatusBanner
        syncStatus={syncStatus}
        supplier={supplier}
        formatDate={formatDate}
      />

      <SupplierInfoCard
        supplier={supplier}
        totalProducts={totalProducts}
        productsLength={products.length}
        formatDate={formatDate}
      />

      {products.length === 0 && (
        <ColumnMappingAlert
          supplier={supplier}
          syncing={syncing}
          onApplyPreset={handleApplyPreset}
          onConfigureMapping={() => navigate("/suppliers")}
        />
      )}

      {/* Product Selection Stats Banner */}
      {products.length > 0 && (
        <Card className="border-emerald-200 bg-emerald-50 mb-6">
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <Layers className="w-6 h-6 text-emerald-600" strokeWidth={1.5} />
                </div>
                <div>
                  <p className="font-semibold text-emerald-900">Flujo de Productos</p>
                  <p className="text-sm text-emerald-700">
                    <span className="font-bold">{selectionStats.selected}</span> de <span className="font-bold">{selectionStats.total}</span> productos
                    están en la sección <span className="font-medium">Productos</span>
                    {selectionStats.total > 0 && (
                      <span className="ml-2 text-xs bg-emerald-200 px-2 py-0.5 rounded-full">
                        {selectionStats.percentage}%
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleSelectAllFromSupplier(true)}
                  disabled={selectingProducts}
                  className="border-emerald-300 text-emerald-700 hover:bg-emerald-100"
                  data-testid="select-all-products-btn"
                >
                  <CheckCircle className="w-4 h-4 mr-1.5" />
                  Seleccionar Todos
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleSelectAllFromSupplier(false)}
                  disabled={selectingProducts}
                  className="border-slate-300 text-slate-600 hover:bg-slate-100"
                  data-testid="deselect-all-products-btn"
                >
                  <XCircle className="w-4 h-4 mr-1.5" />
                  Quitar Todos
                </Button>
                <Button
                  size="sm"
                  onClick={() => navigate("/products")}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  data-testid="go-to-products-btn"
                >
                  <ArrowRight className="w-4 h-4 mr-1.5" />
                  Ir a Productos
                </Button>
              </div>
            </div>

            {categoryHierarchy.length > 0 && (
              <div className="mt-4 pt-4 border-t border-emerald-200">
                <p className="text-sm font-medium text-emerald-800 mb-3">Seleccionar por categoría:</p>
                <CategorySelectionCascade
                  hierarchy={categoryHierarchy}
                  onSelectCategory={(cat, subcat, subcat2) => handleSelectByCategory(cat, subcat, subcat2, true)}
                  onDeselectCategory={(cat, subcat, subcat2) => handleDeselectByCategory(cat, subcat, subcat2)}
                  disabled={selectingProducts}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <SelectionActionsBar
        count={selectedProducts.size}
        selectingProducts={selectingProducts}
        addingToCatalog={addingToCatalog}
        onClear={() => setSelectedProducts(new Set())}
        onAddToProducts={handleSelectProductsForMain}
        onRemoveFromProducts={handleDeselectProductsFromMain}
        onAddToCatalogs={handleAddSelectedToCatalog}
      />

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col gap-4">
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
              <Select
                value={filters.selection}
                onValueChange={(value) => setFilters({ ...filters, selection: value })}
              >
                <SelectTrigger className="w-full lg:w-[180px] input-base" data-testid="filter-selection">
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="selected">En Productos</SelectItem>
                  <SelectItem value="unselected">No en Productos</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-slate-600">Filtrar por categoría:</span>
              <CategoryCascadeFilter
                hierarchy={categoryHierarchy}
                selectedCategory={filters.category}
                selectedSubcategory={filters.subcategory}
                selectedSubcategory2={filters.subcategory2}
                onFilterChange={({ category, subcategory, subcategory2 }) => {
                  setFilters(prev => ({ ...prev, category, subcategory, subcategory2 }));
                }}
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setShowAdvancedFilters((v) => !v)}
                className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border transition-colors ${
                  (filters.brand || filters.part_number || filters.min_price || filters.max_price || filters.min_stock)
                    ? "border-indigo-300 bg-indigo-50 text-indigo-700 font-medium"
                    : "border-slate-200 bg-white text-slate-500 hover:text-slate-700 hover:border-slate-300"
                }`}
                data-testid="toggle-advanced-filters"
              >
                {showAdvancedFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                Filtros avanzados
                {(filters.brand || filters.part_number || filters.min_price || filters.max_price || filters.min_stock) && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">activos</span>
                )}
              </button>
              {(filters.brand || filters.part_number || filters.min_price || filters.max_price || filters.min_stock) && (
                <button
                  type="button"
                  onClick={() => {
                    setFilters(prev => ({ ...prev, brand: "", part_number: "", min_price: "", max_price: "", min_stock: "" }));
                    setTimeout(() => handleSearch(), 0);
                  }}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-600 transition-colors"
                >
                  <X className="w-3 h-3" />
                  Limpiar avanzados
                </button>
              )}
            </div>

            {showAdvancedFilters && (
              <div className="border border-slate-200 rounded-sm bg-slate-50 p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Part Number / Ref.</Label>
                    <Input
                      placeholder="Ej. ABC-1234"
                      value={filters.part_number}
                      onChange={(e) => setFilters(prev => ({ ...prev, part_number: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      className="h-9 text-sm input-base"
                      data-testid="part-number-filter"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Marca</Label>
                    {brands.length > 0 ? (
                      <Select
                        value={filters.brand || "all"}
                        onValueChange={(v) => setFilters(prev => ({ ...prev, brand: v === "all" ? "" : v }))}
                      >
                        <SelectTrigger className="h-9 text-sm input-base" data-testid="brand-filter">
                          <SelectValue placeholder="Todas las marcas" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Todas las marcas</SelectItem>
                          {brands.map((b) => (
                            <SelectItem key={b} value={b}>{b}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        placeholder="Ej. Samsung"
                        value={filters.brand}
                        onChange={(e) => setFilters(prev => ({ ...prev, brand: e.target.value }))}
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                        className="h-9 text-sm input-base"
                        data-testid="brand-filter"
                      />
                    )}
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Precio mín. (€)</Label>
                    <Input
                      type="number"
                      placeholder="0"
                      min="0"
                      step="0.01"
                      value={filters.min_price}
                      onChange={(e) => setFilters(prev => ({ ...prev, min_price: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      className="h-9 text-sm input-base"
                      data-testid="min-price-filter"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Precio máx. (€)</Label>
                    <Input
                      type="number"
                      placeholder="9999"
                      min="0"
                      step="0.01"
                      value={filters.max_price}
                      onChange={(e) => setFilters(prev => ({ ...prev, max_price: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      className="h-9 text-sm input-base"
                      data-testid="max-price-filter"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Stock mínimo</Label>
                    <Input
                      type="number"
                      placeholder="1"
                      min="0"
                      value={filters.min_stock}
                      onChange={(e) => setFilters(prev => ({ ...prev, min_stock: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      className="h-9 text-sm input-base"
                      data-testid="min-stock-filter"
                    />
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-3">
                  Los filtros avanzados se combinan entre sí (AND lógico). Pulsa <strong>Buscar</strong> o Enter para aplicarlos.
                </p>
              </div>
            )}

            <div>
              <Button onClick={handleSearch} className="btn-primary" data-testid="search-btn">
                <Search className="w-4 h-4 mr-2" strokeWidth={1.5} />
                Buscar
              </Button>
            </div>
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
                  <TableHead className="text-center">En Productos</TableHead>
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
                    <TableCell className="text-center">
                      {product.is_selected ? (
                        <Badge className="bg-emerald-100 text-emerald-700 border-0">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Sí
                        </Badge>
                      ) : (
                        <Badge className="bg-slate-100 text-slate-500 border-0">
                          <XCircle className="w-3 h-3 mr-1" />
                          No
                        </Badge>
                      )}
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
                          <BookOpen className="w-4 h-4" strokeWidth={1.5} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200" data-testid="pagination">
              <p className="text-sm text-slate-500">
                Mostrando {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalProducts)} de {totalProducts.toLocaleString()} productos
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  data-testid="prev-page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-slate-600 px-2">
                  Página {currentPage} de {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  data-testid="next-page"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      <UploadDialog
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        supplierName={supplier?.name}
        uploading={uploading}
        onUpload={handleFileUpload}
      />

      <ProductDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        product={selectedProduct}
        onProductUpdate={() => fetchData(currentPage)}
      />

      <CatalogSelectionDialog
        open={showCatalogDialog}
        onOpenChange={setShowCatalogDialog}
        catalogs={catalogs}
        productsCount={productsToAdd.length}
        addingToCatalog={addingToCatalog}
        onConfirm={handleConfirmAddToCatalogs}
        onNavigateToCatalogs={() => { setShowCatalogDialog(false); navigate("/catalogs"); }}
      />
    </div>
  );
};

export default SupplierDetail;
