import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
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
  RefreshCw,
  Clock,
  Zap,
  Globe,
  Columns,
  BookOpen,
  Star,
  CheckCircle,
  XCircle,
  ArrowRight,
  Layers,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { CategoryCascadeFilter, CategorySelectionCascade } from "../components/suppliers";
import ProductDetailDialog from "../components/dialogs/ProductDetailDialog";

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
    selection: "all" // all, selected, unselected
  });
  const [categoryHierarchy, setCategoryHierarchy] = useState([]);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [catalogs, setCatalogs] = useState([]);
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [selectingProducts, setSelectingProducts] = useState(false);
  const fileInputRef = useRef(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const pageSize = 50;

  const fetchData = useCallback(async (page = currentPage) => {
    try {
      // Build query params for pagination and filters
      const productParams = new URLSearchParams();
      productParams.append("skip", String((page - 1) * pageSize));
      productParams.append("limit", String(pageSize));
      if (filters.search) productParams.append("search", filters.search);
      if (filters.category) productParams.append("category", filters.category);
      if (filters.subcategory) productParams.append("subcategory", filters.subcategory);
      if (filters.subcategory2) productParams.append("subcategory2", filters.subcategory2);
      if (filters.selection === "selected") productParams.append("is_selected", "true");
      if (filters.selection === "unselected") productParams.append("is_selected", "false");

      const [supplierRes, productsRes, countRes, categoriesRes, syncStatusRes, catalogsRes, hierarchyRes, selectionStatsRes] = await Promise.all([
        api.get(`/suppliers/${supplierId}`),
        api.get(`/supplier/${supplierId}/products?${productParams.toString()}`),
        api.get(`/supplier/${supplierId}/products/count?${productParams.toString()}`),
        api.get("/products/categories"),
        api.get(`/suppliers/${supplierId}/sync-status`).catch(() => ({ data: null })),
        api.get("/catalogs"),
        api.get(`/products/category-hierarchy?supplier_id=${supplierId}`).catch(() => ({ data: [] })),
        api.get("/products/selected-count", { params: { supplier_id: supplierId } }).catch(() => ({ data: { selected: 0, total: 0 } }))
      ]);
      setSupplier(supplierRes.data);
      setProducts(productsRes.data);
      setTotalProducts(countRes.data?.total || 0);
      setCategories(categoriesRes.data);
      setSyncStatus(syncStatusRes.data);
      setCatalogs(catalogsRes.data);
      setCategoryHierarchy(hierarchyRes.data || []);
      setSelectionStats(selectionStatsRes.data);
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
  }, [supplierId]);

  // Refetch when filters change
  useEffect(() => {
    if (!loading) {
      fetchData(1);
    }
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
      // Now sync with the updated config
      const syncRes = await api.post(`/suppliers/${supplierId}/sync`);
      if (syncRes.data.imported + syncRes.data.updated > 0) {
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

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await api.post(`/suppliers/${supplierId}/sync`);
      
      // Check if mapping is needed
      if (res.data.needs_mapping) {
        toast.warning(res.data.message || "Se necesita configurar el mapeo de columnas", {
          duration: 8000,
          description: `Columnas detectadas: ${(res.data.detected_columns || []).slice(0, 5).join(", ")}...`
        });
      } else if (res.data.status === "success" && res.data.imported + res.data.updated > 0) {
        toast.success(`Sincronización completada: ${res.data.imported} nuevos, ${res.data.updated} actualizados`);
      } else if (res.data.errors > 0 && res.data.imported + res.data.updated === 0) {
        toast.warning("Archivo descargado pero no se importaron productos. Verifica el mapeo de columnas.", {
          duration: 6000
        });
      } else {
        toast.info("Sincronización completada sin cambios");
      }
      
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.message || error.response?.data?.detail || "Error en la sincronización");
    } finally {
      setSyncing(false);
    }
  };

  // Local filtering only for stock (search, category, and selection are now server-side)
  const filteredProducts = products.filter((product) => {
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

  const totalPages = Math.ceil(totalProducts / pageSize);

  // ==================== PRODUCT SELECTION HANDLERS ====================
  
  const handleSelectProductsForMain = async () => {
    if (selectedProducts.size === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select", {
        product_ids: Array.from(selectedProducts)
      });
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
      const res = await api.post("/products/deselect", {
        product_ids: Array.from(selectedProducts)
      });
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

  const openCatalogSelector = (productIds) => {
    if (catalogs.length === 0) {
      toast.error("No hay catálogos creados. Crea uno primero en la sección Catálogos.");
      return;
    }
    setProductsToAdd(productIds);
    // Pre-select default catalog
    const defaultCatalog = catalogs.find(c => c.is_default);
    if (defaultCatalog) {
      setSelectedCatalogs(new Set([defaultCatalog.id]));
    } else {
      setSelectedCatalogs(new Set());
    }
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

  const toggleCatalogSelection = (catalogId) => {
    setSelectedCatalogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(catalogId)) {
        newSet.delete(catalogId);
      } else {
        newSet.add(catalogId);
      }
      return newSet;
    });
  };

  const handleConfirmAddToCatalogs = async () => {
    if (selectedCatalogs.size === 0) {
      toast.error("Selecciona al menos un catálogo");
      return;
    }

    setAddingToCatalog(true);
    let totalAdded = 0;
    let totalSkipped = 0;

    for (const catalogId of selectedCatalogs) {
      try {
        const res = await api.post(`/catalogs/${catalogId}/products`, {
          product_ids: productsToAdd
        });
        totalAdded += res.data.added || 0;
      } catch (error) {
        console.error("Error adding to catalog:", error);
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
          <div className="flex items-center gap-3">
            {(syncStatus?.ftp_configured || supplier?.connection_type === "url") && (
              <Button 
                onClick={handleSync} 
                disabled={syncing}
                variant="outline"
                className="btn-secondary"
                data-testid="sync-btn"
              >
                {syncing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
                    Sincronizando...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" strokeWidth={1.5} />
                    {supplier?.connection_type === "url" ? "Sincronizar URL" : "Sincronizar FTP"}
                  </>
                )}
              </Button>
            )}
            <Button onClick={() => setShowUploadDialog(true)} className="btn-primary" data-testid="import-products-btn">
              <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Importar Archivo
            </Button>
          </div>
        </div>
      </div>

      {/* Sync Status Banner */}
      {syncStatus?.ftp_configured && (
        <Card className="border-emerald-200 bg-emerald-50 mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-emerald-600" strokeWidth={1.5} />
                <div>
                  <p className="font-medium text-emerald-900">Sincronización automática activa</p>
                  <p className="text-sm text-emerald-700">
                    Próxima sincronización: {syncStatus.next_scheduled_sync 
                      ? new Date(syncStatus.next_scheduled_sync).toLocaleString("es-ES")
                      : "Programada cada 12 horas"}
                  </p>
                </div>
              </div>
              {supplier?.last_sync && (
                <div className="text-right">
                  <p className="text-xs text-emerald-600">Última sincronización</p>
                  <p className="text-sm font-medium text-emerald-900">{formatDate(supplier.last_sync)}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

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
              <p className="text-sm text-slate-500">Tipo de conexión</p>
              <div className="flex items-center gap-1.5 mt-1">
                {supplier?.connection_type === "url" ? (
                  <>
                    <Globe className={`w-4 h-4 ${supplier?.file_url ? 'text-emerald-500' : 'text-slate-300'}`} strokeWidth={1.5} />
                    <span className="text-sm">URL Directa</span>
                  </>
                ) : (
                  <>
                    <Server className={`w-4 h-4 ${supplier?.ftp_host ? 'text-emerald-500' : 'text-slate-300'}`} strokeWidth={1.5} />
                    <span className="text-sm font-mono">{supplier?.ftp_host || "No configurado"}</span>
                  </>
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-500">Productos</p>
              <p className="font-mono text-xl font-semibold text-slate-900">{totalProducts > 0 ? totalProducts.toLocaleString() : products.length.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Última sincronización</p>
              <p className="text-sm text-slate-700">{formatDate(supplier?.last_sync)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Column Mapping Alert - Show if columns detected but no products */}
      {supplier?.detected_columns?.length > 0 && products.length === 0 && (
        <Card className="border-amber-200 bg-amber-50 mb-6">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Columns className="w-5 h-5 text-amber-600 mt-0.5" strokeWidth={1.5} />
              <div className="flex-1">
                <p className="font-medium text-amber-900 mb-1">Configuración de mapeo necesaria</p>
                {supplier?.preset_id ? (
                  <p className="text-sm text-amber-700 mb-3">
                    El proveedor tiene una plantilla asignada (<span className="font-semibold">{supplier.preset_id}</span>) pero
                    fue creado con una versión anterior. Haz clic en <span className="font-semibold">Re-aplicar plantilla</span> para
                    actualizar la configuración de columnas y sincronizar automáticamente.
                  </p>
                ) : (
                  <p className="text-sm text-amber-700 mb-3">
                    Se descargó el archivo pero no se importaron productos. Las columnas del archivo no coinciden
                    con los campos del sistema. Configura el mapeo de columnas para asignar correctamente los campos.
                  </p>
                )}
                <div className="mb-3">
                  <p className="text-xs text-amber-600 mb-1">Columnas detectadas:</p>
                  <div className="flex flex-wrap gap-1">
                    {supplier.detected_columns.slice(0, 8).map((col, i) => (
                      <span key={i} className="px-2 py-0.5 bg-white rounded text-xs font-mono text-amber-800 border border-amber-200">
                        {col}
                      </span>
                    ))}
                    {supplier.detected_columns.length > 8 && (
                      <span className="px-2 py-0.5 text-xs text-amber-600">
                        +{supplier.detected_columns.length - 8} más
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {supplier?.preset_id && (
                    <Button
                      size="sm"
                      onClick={handleApplyPreset}
                      disabled={syncing}
                      className="bg-amber-600 hover:bg-amber-700 text-white"
                    >
                      <Zap className="w-3.5 h-3.5 mr-1.5" />
                      Re-aplicar plantilla y sincronizar
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/suppliers")}
                    className="border-amber-300 text-amber-700 hover:bg-amber-100"
                  >
                    <Columns className="w-3.5 h-3.5 mr-1.5" />
                    Configurar Mapeo manual
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
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
            
            {/* Category Selection with Cascade */}
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

      {/* Selection Actions */}
      {selectedProducts.size > 0 && (
        <Card className="border-indigo-200 bg-indigo-50 mb-6 animate-slide-up">
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex items-center gap-3">
                <CheckSquare className="w-5 h-5 text-indigo-600" strokeWidth={1.5} />
                <span className="font-medium text-indigo-900">
                  {selectedProducts.size} producto{selectedProducts.size !== 1 ? "s" : ""} seleccionado{selectedProducts.size !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedProducts(new Set())}
                  className="btn-secondary"
                  data-testid="clear-selection"
                >
                  Limpiar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSelectProductsForMain}
                  disabled={selectingProducts}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  data-testid="add-to-products-section"
                >
                  {selectingProducts ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
                  ) : (
                    <CheckCircle className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  )}
                  Añadir a Productos
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDeselectProductsFromMain}
                  disabled={selectingProducts}
                  className="border-rose-300 text-rose-600 hover:bg-rose-50"
                  data-testid="remove-from-products-section"
                >
                  <XCircle className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  Quitar de Productos
                </Button>
                <Button
                  size="sm"
                  onClick={handleAddSelectedToCatalog}
                  disabled={addingToCatalog}
                  className="btn-primary"
                  data-testid="add-selected-to-catalog"
                >
                  {addingToCatalog ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
                  ) : (
                    <BookOpen className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  )}
                  Añadir a Catálogos
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col gap-4">
            {/* Search and basic filters row */}
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
            
            {/* Category cascade filters row */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-600">Filtrar por categoría:</span>
              <CategoryCascadeFilter
                hierarchy={categoryHierarchy}
                selectedCategory={filters.category}
                selectedSubcategory={filters.subcategory}
                selectedSubcategory2={filters.subcategory2}
                onFilterChange={({ category, subcategory, subcategory2 }) => {
                  setFilters(prev => ({
                    ...prev,
                    category,
                    subcategory,
                    subcategory2
                  }));
                }}
              />
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
          
          {/* Pagination */}
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
      <ProductDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        product={selectedProduct}
        onProductUpdate={() => fetchData(currentPage)}
      />

      {/* Catalog Selection Dialog */}
      <Dialog open={showCatalogDialog} onOpenChange={setShowCatalogDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Añadir a Catálogos
            </DialogTitle>
            <DialogDescription>
              Selecciona los catálogos donde quieres añadir {productsToAdd.length} producto{productsToAdd.length !== 1 ? "s" : ""}
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-2 max-h-[300px] overflow-y-auto">
            {catalogs.length === 0 ? (
              <div className="text-center py-6">
                <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">No hay catálogos creados</p>
                <Button 
                  variant="link" 
                  onClick={() => { setShowCatalogDialog(false); navigate("/catalogs"); }}
                  className="mt-2"
                >
                  Crear catálogo
                </Button>
              </div>
            ) : (
              catalogs.map((catalog) => (
                <div
                  key={catalog.id}
                  onClick={() => toggleCatalogSelection(catalog.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedCatalogs.has(catalog.id)
                      ? "bg-indigo-50 border-indigo-300"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                  data-testid={`catalog-option-${catalog.id}`}
                >
                  <Checkbox
                    checked={selectedCatalogs.has(catalog.id)}
                    onCheckedChange={() => toggleCatalogSelection(catalog.id)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{catalog.name}</span>
                      {catalog.is_default && (
                        <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">
                          <Star className="w-3 h-3 mr-1" />
                          Defecto
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      {catalog.product_count} productos • {catalog.margin_rules_count} reglas
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCatalogDialog(false)} className="btn-secondary">
              Cancelar
            </Button>
            <Button 
              onClick={handleConfirmAddToCatalogs} 
              disabled={addingToCatalog || selectedCatalogs.size === 0}
              className="btn-primary"
              data-testid="confirm-add-to-catalogs"
            >
              {addingToCatalog ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Plus className="w-4 h-4 mr-2" />
              )}
              Añadir a {selectedCatalogs.size} catálogo{selectedCatalogs.size !== 1 ? "s" : ""}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SupplierDetail;
