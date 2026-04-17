import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";

export function useProductSelectionHandlers(supplierId, filteredProducts, fetchData) {
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [selectingProducts, setSelectingProducts] = useState(false);

  const toggleProductSelection = useCallback((productId) => {
    setSelectedProducts((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) next.delete(productId);
      else next.add(productId);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelectedProducts((prev) =>
      prev.size === filteredProducts.length
        ? new Set()
        : new Set(filteredProducts.map((p) => p.id))
    );
  }, [filteredProducts]);

  const handleSelectProductsForMain = useCallback(async () => {
    if (selectedProducts.size === 0) { toast.error("Selecciona al menos un producto"); return; }
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select", { product_ids: Array.from(selectedProducts) });
      toast.success(`${res.data.selected} productos añadidos a la sección Productos`);
      setSelectedProducts(new Set());
      fetchData();
    } catch { toast.error("Error al seleccionar productos"); }
    finally { setSelectingProducts(false); }
  }, [selectedProducts, fetchData]);

  const handleDeselectProductsFromMain = useCallback(async () => {
    if (selectedProducts.size === 0) { toast.error("Selecciona al menos un producto"); return; }
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/deselect", { product_ids: Array.from(selectedProducts) });
      toast.success(`${res.data.deselected} productos quitados de la sección Productos`);
      setSelectedProducts(new Set());
      fetchData();
    } catch { toast.error("Error al deseleccionar productos"); }
    finally { setSelectingProducts(false); }
  }, [selectedProducts, fetchData]);

  const handleSelectByCategory = useCallback(async (category, subcategory = null, subcategory2 = null, selectAll = true) => {
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select-by-supplier", {
        supplier_id: supplierId,
        category: category || null,
        subcategory: subcategory || null,
        subcategory2: subcategory2 || null,
        select_all: selectAll,
      });
      toast.success(res.data.message);
      fetchData();
    } catch { toast.error("Error al seleccionar productos"); }
    finally { setSelectingProducts(false); }
  }, [supplierId, fetchData]);

  const handleDeselectByCategory = useCallback(async (category, subcategory = null, subcategory2 = null) => {
    return handleSelectByCategory(category, subcategory, subcategory2, false);
  }, [handleSelectByCategory]);

  const handleSelectAllFromSupplier = useCallback(async (selectAll = true) => {
    setSelectingProducts(true);
    try {
      const res = await api.post("/products/select-by-supplier", { supplier_id: supplierId, select_all: selectAll });
      toast.success(res.data.message);
      fetchData();
    } catch { toast.error("Error al seleccionar productos"); }
    finally { setSelectingProducts(false); }
  }, [supplierId, fetchData]);

  return {
    selectedProducts, setSelectedProducts, selectingProducts,
    toggleProductSelection, toggleSelectAll,
    handleSelectProductsForMain, handleDeselectProductsFromMain,
    handleSelectByCategory, handleDeselectByCategory, handleSelectAllFromSupplier,
  };
}
