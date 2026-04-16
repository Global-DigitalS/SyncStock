import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useSyncProgress, SYNC_STEPS } from "../contexts/SyncProgressContext";
import { api } from "../App";
import ProductDetailDialog from "../components/dialogs/ProductDetailDialog";
import {
  SupplierHeader,
  SyncStatusBanner,
  SupplierInfoCard,
  ColumnMappingAlert,
  SelectionActionsBar,
  UploadDialog,
  CatalogSelectionDialog,
  ProductSelectionStats,
  ProductFiltersCard,
  ProductsTable,
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

      {products.length > 0 && (
        <ProductSelectionStats
          selectionStats={selectionStats}
          categoryHierarchy={categoryHierarchy}
          selectingProducts={selectingProducts}
          onSelectAll={() => handleSelectAllFromSupplier(true)}
          onDeselectAll={() => handleSelectAllFromSupplier(false)}
          onNavigateToProducts={() => navigate("/products")}
          onSelectCategory={(cat, subcat, subcat2) => handleSelectByCategory(cat, subcat, subcat2, true)}
          onDeselectCategory={(cat, subcat, subcat2) => handleDeselectByCategory(cat, subcat, subcat2)}
        />
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

      <ProductFiltersCard
        filters={filters}
        brands={brands}
        categoryHierarchy={categoryHierarchy}
        showAdvancedFilters={showAdvancedFilters}
        onFiltersChange={setFilters}
        onSearch={handleSearch}
        onToggleAdvancedFilters={() => setShowAdvancedFilters((v) => !v)}
      />

      <ProductsTable
        filteredProducts={filteredProducts}
        totalProductsCount={products.length}
        selectedProducts={selectedProducts}
        currentPage={currentPage}
        totalProducts={totalProducts}
        totalPages={totalPages}
        pageSize={pageSize}
        onToggleSelection={toggleProductSelection}
        onToggleSelectAll={toggleSelectAll}
        onPageChange={handlePageChange}
        onViewProduct={(product) => { setSelectedProduct(product); setShowDetailDialog(true); }}
        onAddToCatalog={handleAddSingleToCatalog}
        onImport={() => setShowUploadDialog(true)}
      />

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
