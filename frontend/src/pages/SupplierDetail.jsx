import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useSupplierData } from "../hooks/useSupplierData";
import { useProductSelectionHandlers } from "../hooks/useProductSelectionHandlers";
import { useSupplierSyncHandlers } from "../hooks/useSupplierSyncHandlers";
import { useCatalogHandlers } from "../hooks/useCatalogHandlers";
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

const defaultFilters = {
  search: "", category: "", subcategory: "", subcategory2: "",
  stock: "all", selection: "all", brand: "", part_number: "",
  min_price: "", max_price: "", min_stock: "",
};

const SupplierDetail = () => {
  const { supplierId } = useParams();
  const navigate = useNavigate();

  const [filters, setFilters] = useState(defaultFilters);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  const {
    supplier, products, categories, loading, syncStatus, catalogs,
    categoryHierarchy, selectionStats, brands, currentPage, totalProducts,
    pageSize, fetchData,
  } = useSupplierData(supplierId, filters, navigate);

  const filteredProducts = products.filter((p) => {
    if (filters.stock === "low" && (p.stock <= 0 || p.stock > 5)) return false;
    if (filters.stock === "out" && p.stock > 0) return false;
    if (filters.stock === "in" && p.stock <= 0) return false;
    return true;
  });

  const {
    selectedProducts, setSelectedProducts, selectingProducts,
    toggleProductSelection, toggleSelectAll,
    handleSelectProductsForMain, handleDeselectProductsFromMain,
    handleSelectByCategory, handleDeselectByCategory, handleSelectAllFromSupplier,
  } = useProductSelectionHandlers(supplierId, filteredProducts, fetchData);

  const { syncing, uploading, handleSync, handleApplyPreset, handleFileUpload } =
    useSupplierSyncHandlers(supplierId, supplier, fetchData);

  const {
    showCatalogDialog, setShowCatalogDialog,
    productsToAdd, addingToCatalog,
    handleAddSelectedToCatalog, handleAddSingleToCatalog, handleConfirmAddToCatalogs,
  } = useCatalogHandlers(catalogs, selectedProducts, fetchData);

  const totalPages = Math.ceil(totalProducts / pageSize);

  const handleSearch = () => fetchData(1);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setSelectedProducts(new Set());
      fetchData(newPage);
    }
  };

  const handleUpload = async (file) => {
    const ok = await handleFileUpload(file);
    if (ok) setShowUploadDialog(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
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

      <SyncStatusBanner syncStatus={syncStatus} supplier={supplier} formatDate={formatDate} />

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
        onUpload={handleUpload}
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
