import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
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
  Save,
  Pencil,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";

const Products = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: "",
    category: "",
    stock: searchParams.get("stock") || ""
  });
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productsToAdd, setProductsToAdd] = useState([]);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const [uploadSupplierId, setUploadSupplierId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const [editForm, setEditForm] = useState({});
  const [savingProduct, setSavingProduct] = useState(false);
  const [activeTab, setActiveTab] = useState("proveedores");
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  
  // Sorting state
  const [sortBy, setSortBy] = useState(null);
  const [sortOrder, setSortOrder] = useState("asc");

  const buildQueryParams = useCallback((page = currentPage, limit = pageSize) => {
    const params = { skip: (page - 1) * limit, limit };
    if (filters.search) params.search = filters.search;
    if (filters.category) params.category = filters.category;
    if (filters.stock === "available") {
      params.min_stock = 1;
    }
    if (sortBy) {
      params.sort_by = sortBy;
      params.sort_order = sortOrder;
    }
    return params;
  }, [filters, currentPage, pageSize, sortBy, sortOrder]);

  const fetchData = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const queryParams = buildQueryParams(page, pageSize);
      const countParams = { ...queryParams };
      delete countParams.skip;
      delete countParams.limit;
      
      const [productsRes, countRes, categoriesRes, suppliersRes, catalogsRes] = await Promise.all([
        api.get("/products-unified", { params: queryParams }),
        api.get("/products-unified/count", { params: countParams }),
        api.get("/products/categories"),
        api.get("/suppliers"),
        api.get("/catalogs")
      ]);
      setProducts(productsRes.data);
      setTotalProducts(countRes.data.total);
      setCategories(categoriesRes.data);
      setSuppliers(suppliersRes.data);
      setCatalogs(catalogsRes.data);
      setCurrentPage(page);
    } catch (error) {
      toast.error("Error al cargar los productos");
    } finally {
      setLoading(false);
    }
  }, [buildQueryParams, pageSize]);

  useEffect(() => {
    fetchData(1);
  }, []);

  const handleSearch = async () => {
    setCurrentPage(1);
    fetchData(1);
  };

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages) return;
    setSelectedProducts(new Set());
    fetchData(newPage);
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("asc");
    }
    setCurrentPage(1);
    setTimeout(() => fetchData(1), 0);
  };

  const totalPages = Math.ceil(totalProducts / pageSize);

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

  // Selection handlers
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedProducts(new Set(products.map(p => p.ean)));
    } else {
      setSelectedProducts(new Set());
    }
  };

  const handleSelectProduct = (ean, checked) => {
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(ean);
      } else {
        newSet.delete(ean);
      }
      return newSet;
    });
  };

  // Get best product_ids for selected EANs
  const getBestProductIds = (eans) => {
    const productIds = [];
    for (const ean of eans) {
      const product = products.find(p => p.ean === ean);
      if (product) {
        const bestOffer = product.suppliers.find(s => s.is_best_offer);
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
      toast.error("No hay catálogos creados. Crea uno primero en la sección Catálogos.");
      return;
    }
    const productIds = getBestProductIds(eans);
    setProductsToAdd(productIds);
    const defaultCatalog = catalogs.find(c => c.is_default);
    if (defaultCatalog) {
      setSelectedCatalogs(new Set([defaultCatalog.id]));
    } else {
      setSelectedCatalogs(new Set());
    }
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

  const openProductDetail = async (product) => {
    setSelectedProduct(product);
    setActiveTab("proveedores");
    setShowDetailDialog(true);
    // Load full product data for the best offer to populate edit form
    const bestOffer = product.suppliers.find(s => s.is_best_offer);
    if (bestOffer) {
      try {
        const res = await api.get(`/products/${bestOffer.product_id}`);
        const p = res.data;
        setEditForm({
          name: p.name || "", ean: p.ean || "", sku: p.sku || "",
          description: p.description || "", price: p.price || 0,
          stock: p.stock || 0, category: p.category || "",
          brand: p.brand || "", weight: p.weight || 0,
          image_url: p.image_url || "",
          referencia: p.referencia || "", part_number: p.part_number || "",
          asin: p.asin || "", upc: p.upc || "", gtin: p.gtin || p.ean || "",
          oem: p.oem || "", id_erp: p.id_erp || "",
          activado: p.activado !== false, descatalogado: p.descatalogado || false,
          condicion: p.condicion || "", activar_pos: p.activar_pos || false,
          tipo_pack: p.tipo_pack || false,
          vender_sin_stock: p.vender_sin_stock || false,
          nuevo: p.nuevo || "", fecha_disponibilidad: p.fecha_disponibilidad || "",
          stock_disponible: p.stock_disponible ?? p.stock ?? 0,
          stock_fantasma: p.stock_fantasma ?? 0, stock_market: p.stock_market ?? 0,
          unid_caja: p.unid_caja ?? 0, cantidad_minima: p.cantidad_minima ?? 0,
          dias_entrega: p.dias_entrega ?? 0,
          cantidad_maxima_carrito: p.cantidad_maxima_carrito ?? 0,
          resto_stock: p.resto_stock !== false,
          requiere_envio: p.requiere_envio !== false,
          envio_gratis: p.envio_gratis || false,
          gastos_envio: p.gastos_envio ?? 0,
          largo: p.largo ?? 0, ancho: p.ancho ?? 0, alto: p.alto ?? 0,
          tipo_peso: p.tipo_peso || "kilogram",
          formas_pago: p.formas_pago || "todas",
          formas_envio: p.formas_envio || "todas",
          permite_actualizar_coste: p.permite_actualizar_coste !== false,
          permite_actualizar_stock: p.permite_actualizar_stock !== false,
          tipo_cheque_regalo: p.tipo_cheque_regalo || false,
          _product_id: bestOffer.product_id
        });
      } catch (error) {
        console.error("Error loading product data:", error);
      }
    }
  };

  const handleSaveProduct = async () => {
    if (!editForm._product_id) return;
    setSavingProduct(true);
    try {
      const { _product_id, ...payload } = editForm;
      await api.put(`/products/${_product_id}`, payload);
      toast.success("Producto actualizado correctamente");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar el producto");
    } finally {
      setSavingProduct(false);
    }
  };

  const updateEditField = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  const getStockBadge = (stock) => {
    if (stock === 0) return <Badge className="bg-rose-100 text-rose-700 border-0">Sin stock</Badge>;
    if (stock <= 5) return <Badge className="bg-amber-100 text-amber-700 border-0">{stock} uds</Badge>;
    return <Badge className="bg-emerald-100 text-emerald-700 border-0">{stock} uds</Badge>;
  };

  if (loading && products.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
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
            {products.length.toLocaleString()} productos únicos de tus proveedores
          </p>
        </div>
        <Button onClick={() => setShowUploadDialog(true)} className="btn-primary">
          <Upload className="w-4 h-4 mr-2" />
          Importar Productos
        </Button>
      </div>

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
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
              value={filters.category || "all"}
              onValueChange={(value) => setFilters({ ...filters, category: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full lg:w-[200px] input-base">
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
              <SelectTrigger className="w-full lg:w-[150px] input-base">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="available">Con stock</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} className="btn-secondary">
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedProducts(new Set())}
                  className="btn-secondary"
                >
                  Limpiar selección
                </Button>
                <Button
                  size="sm"
                  onClick={handleAddSelectedToCatalogs}
                  disabled={addingToCatalog}
                  className="btn-primary"
                  data-testid="add-selected-to-catalogs"
                >
                  {addingToCatalog ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <BookOpen className="w-4 h-4 mr-2" />
                  )}
                  Añadir a Catálogos
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Products Table */}
      {products.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Package className="w-10 h-10" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            No hay productos
          </h3>
          <p className="text-slate-500 mb-4">
            {filters.search || filters.category ? "Prueba con otros filtros de búsqueda" : "Importa productos desde tus proveedores para comenzar"}
          </p>
          {!filters.search && !filters.category && (
            <Button onClick={() => setShowUploadDialog(true)} className="btn-primary">
              <Upload className="w-4 h-4 mr-2" />
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
                      checked={selectedProducts.size === products.length && products.length > 0}
                      onCheckedChange={handleSelectAll}
                      data-testid="select-all-products"
                    />
                  </TableHead>
                  <TableHead>
                    <button
                      onClick={() => handleSort("name")}
                      className="flex items-center gap-1 hover:text-indigo-600 transition-colors"
                      data-testid="sort-name"
                    >
                      Producto
                      {sortBy === "name" ? (
                        sortOrder === "asc" ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />
                      ) : (
                        <ArrowUpDown className="w-4 h-4 opacity-40" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead>EAN</TableHead>
                  <TableHead>Mejor Proveedor</TableHead>
                  <TableHead className="text-right">
                    <button
                      onClick={() => handleSort("price")}
                      className="flex items-center gap-1 ml-auto hover:text-indigo-600 transition-colors"
                      data-testid="sort-price"
                    >
                      Mejor Precio
                      {sortBy === "price" ? (
                        sortOrder === "asc" ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />
                      ) : (
                        <ArrowUpDown className="w-4 h-4 opacity-40" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead className="text-right">
                    <button
                      onClick={() => handleSort("stock")}
                      className="flex items-center gap-1 ml-auto hover:text-indigo-600 transition-colors"
                      data-testid="sort-stock"
                    >
                      Stock Total
                      {sortBy === "stock" ? (
                        sortOrder === "asc" ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />
                      ) : (
                        <ArrowUpDown className="w-4 h-4 opacity-40" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead className="text-center">
                    <button
                      onClick={() => handleSort("suppliers")}
                      className="flex items-center gap-1 mx-auto hover:text-indigo-600 transition-colors"
                      data-testid="sort-suppliers"
                    >
                      Proveedores
                      {sortBy === "suppliers" ? (
                        sortOrder === "asc" ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />
                      ) : (
                        <ArrowUpDown className="w-4 h-4 opacity-40" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow 
                    key={product.ean} 
                    className={`table-row ${selectedProducts.has(product.ean) ? 'bg-indigo-50' : ''}`}
                    data-testid={`product-row-${product.ean}`}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedProducts.has(product.ean)}
                        onCheckedChange={(checked) => handleSelectProduct(product.ean, checked)}
                        data-testid={`select-product-${product.ean}`}
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
                            <Package className="w-5 h-5 text-slate-400" />
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
                      <span className="font-mono text-sm text-slate-600">{product.ean}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <TrendingDown className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm font-medium text-slate-900">{product.best_supplier}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono font-semibold text-emerald-600">
                        {product.best_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openProductDetail(product)}
                          className="h-8 w-8 p-0"
                          data-testid={`view-product-${product.ean}`}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openCatalogSelector([product.ean])}
                          className="h-8 w-8 p-0 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                          data-testid={`add-to-catalog-${product.ean}`}
                        >
                          <BookOpen className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          
          {/* Pagination Controls */}
          {totalProducts > 0 && (
            <div className="px-6 py-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-500">
                  Mostrando {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalProducts)} de {totalProducts.toLocaleString()} productos
                </span>
                <Select
                  value={String(pageSize)}
                  onValueChange={(v) => {
                    setPageSize(Number(v));
                    setCurrentPage(1);
                    setTimeout(() => fetchData(1), 0);
                  }}
                >
                  <SelectTrigger className="w-[100px] h-8" data-testid="page-size-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 / pág</SelectItem>
                    <SelectItem value="25">25 / pág</SelectItem>
                    <SelectItem value="50">50 / pág</SelectItem>
                    <SelectItem value="100">100 / pág</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1 || loading}
                  data-testid="pagination-first"
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || loading}
                  data-testid="pagination-prev"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                {/* Page numbers */}
                <div className="flex items-center gap-1 mx-2">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        className={`h-8 w-8 p-0 ${currentPage === pageNum ? "bg-indigo-600" : ""}`}
                        onClick={() => handlePageChange(pageNum)}
                        disabled={loading}
                        data-testid={`pagination-page-${pageNum}`}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages || loading}
                  data-testid="pagination-next"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages || loading}
                  data-testid="pagination-last"
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Product Detail Dialog with Tabs */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-0">
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Ficha del Producto
            </DialogTitle>
            <DialogDescription>
              {selectedProduct?.name}
            </DialogDescription>
          </DialogHeader>
          
          {selectedProduct && (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
              <div className="px-6 pt-2">
                <TabsList className="w-full grid grid-cols-2" data-testid="product-detail-tabs">
                  <TabsTrigger value="proveedores" data-testid="tab-proveedores">
                    <Truck className="w-4 h-4 mr-2" />
                    Proveedores
                  </TabsTrigger>
                  <TabsTrigger value="datos" data-testid="tab-datos">
                    <Pencil className="w-4 h-4 mr-2" />
                    Datos del Producto
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* TAB 1: Proveedores */}
              <TabsContent value="proveedores" className="flex-1 overflow-y-auto px-6 pb-4 mt-0">
                <div className="space-y-5 pt-4">
                  {/* Product Info Header */}
                  <div className="flex gap-5">
                    <div className="w-24 h-24 flex-shrink-0">
                      {selectedProduct.image_url ? (
                        <img src={selectedProduct.image_url} alt={selectedProduct.name}
                          className="w-full h-full object-cover rounded-lg border border-slate-200" />
                      ) : (
                        <div className="w-full h-full bg-slate-100 rounded-lg flex items-center justify-center">
                          <Package className="w-10 h-10 text-slate-300" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 space-y-2">
                      <h3 className="text-lg font-semibold text-slate-900">{selectedProduct.name}</h3>
                      <div className="flex flex-wrap gap-2">
                        <Badge className="bg-slate-100 text-slate-700 border-0 font-mono text-xs">EAN: {selectedProduct.ean}</Badge>
                        {selectedProduct.brand && <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">{selectedProduct.brand}</Badge>}
                        {selectedProduct.category && <Badge className="bg-slate-100 text-slate-600 border-0 text-xs">{selectedProduct.category}</Badge>}
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
                            {selectedProduct.best_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                          </p>
                          <p className="text-sm text-emerald-600">Stock total: {selectedProduct.total_stock} uds</p>
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
                      {selectedProduct.suppliers.map((supplier, idx) => (
                        <div key={idx} className={`flex items-center justify-between p-3 rounded-lg border ${
                          supplier.is_best_offer ? "bg-emerald-50 border-emerald-200" :
                          supplier.stock > 0 ? "bg-white border-slate-200" : "bg-slate-50 border-slate-200 opacity-60"
                        }`}>
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${supplier.is_best_offer ? "bg-emerald-100" : "bg-slate-100"}`}>
                              <Truck className={`w-4 h-4 ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-500"}`} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-slate-900">{supplier.supplier_name}</p>
                                {supplier.is_best_offer && (
                                  <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs"><Star className="w-3 h-3 mr-1" />Mejor</Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 font-mono">SKU: {supplier.sku}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={`font-bold ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-900"}`}>
                              {supplier.price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                            </p>
                            {supplier.stock > 0 ? (
                              <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">{supplier.stock} uds</Badge>
                            ) : (
                              <Badge className="bg-rose-100 text-rose-700 border-0 text-xs"><AlertTriangle className="w-3 h-3 mr-1" />Sin stock</Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* TAB 2: Datos del Producto */}
              <TabsContent value="datos" className="flex-1 overflow-y-auto px-6 pb-4 mt-0">
                <div className="space-y-6 pt-4">
                  {/* Section: Nombre */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold text-slate-800">Nombre del Producto</Label>
                    <Input value={editForm.name || ""} onChange={(e) => updateEditField("name", e.target.value)}
                      className="input-base" data-testid="edit-name" />
                  </div>

                  {/* Section: Estado */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Estado</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
                      <ToggleField label="Activado" value={editForm.activado} onChange={(v) => updateEditField("activado", v)} testId="edit-activado" />
                      <ToggleField label="Descatalogado" value={editForm.descatalogado} onChange={(v) => updateEditField("descatalogado", v)} testId="edit-descatalogado" />
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Condición</Label>
                        <Input value={editForm.condicion || ""} onChange={(e) => updateEditField("condicion", e.target.value)}
                          className="input-base text-sm h-9" placeholder="Nuevo / Usado" />
                      </div>
                      <ToggleField label="Activar en POS" value={editForm.activar_pos} onChange={(v) => updateEditField("activar_pos", v)} testId="edit-activar-pos" />
                      <ToggleField label="De tipo Pack" value={editForm.tipo_pack} onChange={(v) => updateEditField("tipo_pack", v)} testId="edit-tipo-pack" />
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">ID ERP</Label>
                        <Input value={editForm.id_erp || ""} onChange={(e) => updateEditField("id_erp", e.target.value)}
                          className="input-base text-sm h-9" />
                      </div>
                    </div>
                  </div>

                  {/* Section: Identificadores */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Identificadores</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
                      {[
                        { field: "referencia", label: "Referencia" },
                        { field: "part_number", label: "Part Number" },
                        { field: "ean", label: "EAN" },
                        { field: "asin", label: "ASIN" },
                        { field: "upc", label: "UPC" },
                        { field: "gtin", label: "GTIN" },
                        { field: "oem", label: "OEM" },
                      ].map(({ field, label }) => (
                        <div key={field} className="space-y-1">
                          <Label className="text-xs text-slate-500">{label}</Label>
                          <Input value={editForm[field] || ""} onChange={(e) => updateEditField(field, e.target.value)}
                            className="input-base text-sm h-9 font-mono" data-testid={`edit-${field}`} />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Section: Marca, Proveedor, Opciones */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Marca y Opciones</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Marca</Label>
                        <Input value={editForm.brand || ""} onChange={(e) => updateEditField("brand", e.target.value)}
                          className="input-base text-sm h-9" data-testid="edit-brand" />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Categoría</Label>
                        <Input value={editForm.category || ""} onChange={(e) => updateEditField("category", e.target.value)}
                          className="input-base text-sm h-9" />
                      </div>
                      <ToggleField label="Vender sin stock" value={editForm.vender_sin_stock} onChange={(v) => updateEditField("vender_sin_stock", v)} testId="edit-vender-sin-stock" />
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Nuevo</Label>
                        <Input value={editForm.nuevo || ""} onChange={(e) => updateEditField("nuevo", e.target.value)}
                          className="input-base text-sm h-9" placeholder="Decidir por fecha" />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Fecha disponibilidad</Label>
                        <Input type="date" value={editForm.fecha_disponibilidad || ""} onChange={(e) => updateEditField("fecha_disponibilidad", e.target.value)}
                          className="input-base text-sm h-9" />
                      </div>
                    </div>
                  </div>

                  {/* Section: Stock */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Stock</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
                      {[
                        { field: "stock_disponible", label: "Stock disponible" },
                        { field: "stock", label: "Stock proveedor" },
                        { field: "stock_fantasma", label: "Stock Fantasma" },
                        { field: "stock_market", label: "Stock Market" },
                        { field: "unid_caja", label: "Unid. caja" },
                        { field: "cantidad_minima", label: "Cantidad mínima" },
                        { field: "dias_entrega", label: "Días de entrega" },
                        { field: "cantidad_maxima_carrito", label: "Cant. máx. carrito" },
                      ].map(({ field, label }) => (
                        <div key={field} className="space-y-1">
                          <Label className="text-xs text-slate-500">{label}</Label>
                          <Input type="number" value={editForm[field] ?? 0}
                            onChange={(e) => updateEditField(field, parseInt(e.target.value) || 0)}
                            className="input-base text-sm h-9 font-mono" data-testid={`edit-${field}`} />
                        </div>
                      ))}
                    </div>
                    <div className="mt-3">
                      <ToggleField label="Resto de Stock" value={editForm.resto_stock} onChange={(v) => updateEditField("resto_stock", v)} testId="edit-resto-stock" />
                    </div>
                  </div>

                  {/* Section: Envío */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Envío</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                      <ToggleField label="Requiere Envío" value={editForm.requiere_envio} onChange={(v) => updateEditField("requiere_envio", v)} testId="edit-requiere-envio" />
                      <ToggleField label="Envío gratis" value={editForm.envio_gratis} onChange={(v) => updateEditField("envio_gratis", v)} testId="edit-envio-gratis" />
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Gastos de envío</Label>
                        <Input type="number" step="0.01" value={editForm.gastos_envio ?? 0}
                          onChange={(e) => updateEditField("gastos_envio", parseFloat(e.target.value) || 0)}
                          className="input-base text-sm h-9 font-mono" />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Precio</Label>
                        <Input type="number" step="0.01" value={editForm.price ?? 0}
                          onChange={(e) => updateEditField("price", parseFloat(e.target.value) || 0)}
                          className="input-base text-sm h-9 font-mono" data-testid="edit-price" />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Imagen URL</Label>
                        <Input value={editForm.image_url || ""} onChange={(e) => updateEditField("image_url", e.target.value)}
                          className="input-base text-sm h-9" />
                      </div>
                    </div>
                  </div>

                  {/* Section: Dimensiones */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Dimensiones y Peso</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                      {[
                        { field: "largo", label: "Largo" },
                        { field: "ancho", label: "Ancho" },
                        { field: "alto", label: "Alto" },
                        { field: "weight", label: "Peso" },
                      ].map(({ field, label }) => (
                        <div key={field} className="space-y-1">
                          <Label className="text-xs text-slate-500">{label}</Label>
                          <Input type="number" step="0.01" value={editForm[field] ?? 0}
                            onChange={(e) => updateEditField(field, parseFloat(e.target.value) || 0)}
                            className="input-base text-sm h-9 font-mono" data-testid={`edit-${field}`} />
                        </div>
                      ))}
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Tipo peso</Label>
                        <div className="flex rounded-lg border border-slate-200 overflow-hidden h-9">
                          {["gram", "kilogram", "ounce", "pound"].map((unit) => (
                            <button key={unit} type="button"
                              onClick={() => updateEditField("tipo_peso", unit)}
                              className={`flex-1 text-xs font-medium transition-colors ${
                                editForm.tipo_peso === unit
                                  ? "bg-slate-900 text-white"
                                  : "bg-white text-slate-500 hover:bg-slate-50"
                              }`}
                              data-testid={`peso-${unit}`}
                            >
                              {unit === "gram" ? "Gram" : unit === "kilogram" ? "Kg" : unit === "ounce" ? "Oz" : "Lb"}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Section: Formas de pago y envío */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Formas de pago y envío</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Formas de pago disponibles</Label>
                        <div className="flex rounded-lg border border-slate-200 overflow-hidden h-9">
                          {["todas", "especificas"].map((opt) => (
                            <button key={opt} type="button"
                              onClick={() => updateEditField("formas_pago", opt)}
                              className={`flex-1 text-xs font-medium transition-colors capitalize ${
                                editForm.formas_pago === opt ? "bg-emerald-500 text-white" : "bg-white text-slate-500 hover:bg-slate-50"
                              }`}>
                              {opt === "todas" ? "Todas" : "Específicas"}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs text-slate-500">Formas de envío disponibles</Label>
                        <div className="flex rounded-lg border border-slate-200 overflow-hidden h-9">
                          {["todas", "especificas"].map((opt) => (
                            <button key={opt} type="button"
                              onClick={() => updateEditField("formas_envio", opt)}
                              className={`flex-1 text-xs font-medium transition-colors capitalize ${
                                editForm.formas_envio === opt ? "bg-emerald-500 text-white" : "bg-white text-slate-500 hover:bg-slate-50"
                              }`}>
                              {opt === "todas" ? "Todas" : "Específicas"}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Section: Permisos */}
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-3">Permisos de Proveedor</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      <ToggleField label="Permite actualizar coste" value={editForm.permite_actualizar_coste} onChange={(v) => updateEditField("permite_actualizar_coste", v)} testId="edit-permite-coste" />
                      <ToggleField label="Permite actualizar stock" value={editForm.permite_actualizar_stock} onChange={(v) => updateEditField("permite_actualizar_stock", v)} testId="edit-permite-stock" />
                      <ToggleField label="De tipo cheque regalo" value={editForm.tipo_cheque_regalo} onChange={(v) => updateEditField("tipo_cheque_regalo", v)} testId="edit-cheque-regalo" />
                    </div>
                  </div>

                  {/* Description */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-500">Descripción</Label>
                    <textarea value={editForm.description || ""} onChange={(e) => updateEditField("description", e.target.value)}
                      className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[80px] resize-y"
                      data-testid="edit-description" />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}
          
          <div className="border-t px-6 py-4 flex items-center justify-between">
            <Button variant="outline" onClick={() => setShowDetailDialog(false)} className="btn-secondary">
              Cerrar
            </Button>
            <div className="flex items-center gap-2">
              {activeTab === "datos" && (
                <Button onClick={handleSaveProduct} disabled={savingProduct} className="btn-primary" data-testid="save-product-btn">
                  {savingProduct ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Guardar Cambios
                </Button>
              )}
              <Button onClick={() => {
                if (selectedProduct) {
                  openCatalogSelector([selectedProduct.ean]);
                  setShowDetailDialog(false);
                }
              }} className="btn-primary" variant={activeTab === "datos" ? "outline" : "default"}>
                <BookOpen className="w-4 h-4 mr-2" />
                Añadir a Catálogos
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Catalog Selection Dialog */}
      <Dialog open={showCatalogDialog} onOpenChange={setShowCatalogDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Añadir a Catálogos
            </DialogTitle>
            <DialogDescription>
              Se añadirá la mejor oferta de cada producto seleccionado
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

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Upload className="w-5 h-5 text-indigo-600" />
              Importar Productos
            </DialogTitle>
            <DialogDescription>
              Sube un archivo CSV, Excel o XML con tus productos
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Selecciona el proveedor</label>
              <Select value={uploadSupplierId} onValueChange={setUploadSupplierId}>
                <SelectTrigger className="input-base">
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
                dragActive ? "border-indigo-400 bg-indigo-50" : "border-slate-300 hover:border-slate-400"
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
                Arrastra tu archivo aquí o{" "}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  selecciona uno
                </button>
              </p>
              <p className="text-xs text-slate-500">CSV, Excel (.xlsx, .xls) o XML</p>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadDialog(false)} className="btn-secondary">
              Cancelar
            </Button>
            <Button 
              onClick={() => fileInputRef.current?.click()} 
              disabled={uploading || !uploadSupplierId}
              className="btn-primary"
            >
              {uploading ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Upload className="w-4 h-4 mr-2" />
              )}
              Importar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Toggle field component for No/Sí switches
const ToggleField = ({ label, value, onChange, testId }) => (
  <div className="space-y-1">
    <Label className="text-xs text-slate-500">{label}</Label>
    <div className="flex rounded-lg border border-slate-200 overflow-hidden h-9">
      <button type="button" onClick={() => onChange(false)}
        className={`flex-1 text-xs font-medium transition-colors ${!value ? "bg-slate-200 text-slate-700" : "bg-white text-slate-400 hover:bg-slate-50"}`}
        data-testid={testId ? `${testId}-no` : undefined}>
        No
      </button>
      <button type="button" onClick={() => onChange(true)}
        className={`flex-1 text-xs font-medium transition-colors ${value ? "bg-emerald-500 text-white" : "bg-white text-slate-400 hover:bg-slate-50"}`}
        data-testid={testId ? `${testId}-si` : undefined}>
        Sí
      </button>
    </div>
  </div>
);

export default Products;
