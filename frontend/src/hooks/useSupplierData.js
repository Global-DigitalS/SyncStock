import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { api } from "../App";

const PAGE_SIZE = 50;

export function useSupplierData(supplierId, filters, navigate) {
  const [supplier, setSupplier] = useState(null);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncStatus, setSyncStatus] = useState(null);
  const [catalogs, setCatalogs] = useState([]);
  const [categoryHierarchy, setCategoryHierarchy] = useState([]);
  const [selectionStats, setSelectionStats] = useState({ selected: 0, total: 0 });
  const [brands, setBrands] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);

  const fetchData = useCallback(async (page = 1) => {
    try {
      const productParams = new URLSearchParams();
      productParams.append("skip", String((page - 1) * PAGE_SIZE));
      productParams.append("limit", String(PAGE_SIZE));
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
        api.get("/products/brands", { params: { supplier_id: supplierId } }).catch(() => ({ data: [] })),
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
    } catch {
      toast.error("Error al cargar los datos del proveedor");
      navigate("/suppliers");
    } finally {
      setLoading(false);
    }
  }, [supplierId, filters, navigate]);

  useEffect(() => {
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supplierId]);

  useEffect(() => {
    if (!loading) fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.category, filters.subcategory, filters.subcategory2, filters.selection]);

  return {
    supplier, products, categories, loading, syncStatus, catalogs,
    categoryHierarchy, selectionStats, brands, currentPage, totalProducts,
    pageSize: PAGE_SIZE, fetchData,
  };
}
