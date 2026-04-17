import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";

export function useCatalogHandlers(catalogs, selectedProducts, fetchData) {
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [addingToCatalog, setAddingToCatalog] = useState(false);

  const openCatalogSelector = useCallback((productIds) => {
    if (catalogs.length === 0) {
      toast.error("No hay catálogos creados. Crea uno primero en la sección Catálogos.");
      return;
    }
    setProductsToAdd(productIds);
    setShowCatalogDialog(true);
  }, [catalogs]);

  const handleAddSelectedToCatalog = useCallback(() => {
    if (selectedProducts.size === 0) { toast.error("Selecciona al menos un producto"); return; }
    openCatalogSelector(Array.from(selectedProducts));
  }, [selectedProducts, openCatalogSelector]);

  const handleAddSingleToCatalog = useCallback((productId) => {
    openCatalogSelector([productId]);
  }, [openCatalogSelector]);

  const handleConfirmAddToCatalogs = useCallback(async (selectedCatalogs) => {
    if (selectedCatalogs.size === 0) { toast.error("Selecciona al menos un catálogo"); return; }
    setAddingToCatalog(true);
    let totalAdded = 0;
    for (const catalogId of selectedCatalogs) {
      try {
        const res = await api.post(`/catalogs/${catalogId}/products`, { product_ids: productsToAdd });
        totalAdded += res.data.added || 0;
      } catch { /* handled silently */ }
    }
    setAddingToCatalog(false);
    setShowCatalogDialog(false);
    setProductsToAdd([]);
    const catalogNames = catalogs.filter(c => selectedCatalogs.has(c.id)).map(c => c.name).join(", ");
    if (totalAdded > 0) {
      toast.success(`Productos añadidos a: ${catalogNames}`);
    } else {
      toast.info("Los productos ya estaban en los catálogos seleccionados");
    }
    fetchData();
  }, [catalogs, productsToAdd, fetchData]);

  return {
    showCatalogDialog, setShowCatalogDialog,
    productsToAdd, addingToCatalog,
    handleAddSelectedToCatalog, handleAddSingleToCatalog, handleConfirmAddToCatalogs,
  };
}
