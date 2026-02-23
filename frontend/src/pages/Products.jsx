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
  Pencil
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

  const buildQueryParams = useCallback(() => {
    const params = {};
    if (filters.search) params.search = filters.search;
    if (filters.category) params.category = filters.category;
    if (filters.stock === "available") {
      params.min_stock = 1;
    }
    return params;
  }, [filters]);

  const fetchData = useCallback(async () => {
    try {
      const [productsRes, categoriesRes, suppliersRes, catalogsRes] = await Promise.all([
        api.get("/products-unified", { params: buildQueryParams() }),
        api.get("/products/categories"),
        api.get("/suppliers"),
        api.get("/catalogs")
      ]);
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
      setSuppliers(suppliersRes.data);
      setCatalogs(catalogsRes.data);
    } catch (error) {
      toast.error("Error al cargar los productos");
    } finally {
      setLoading(false);
    }
  }, [buildQueryParams]);

  useEffect(() => {
    fetchData();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await api.get("/products-unified", { params: buildQueryParams() });
      setProducts(res.data);
    } catch (error) {
      toast.error("Error al buscar productos");
    } finally {
      setLoading(false);
    }
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

  const openProductDetail = (product) => {
    setSelectedProduct(product);
    setShowDetailDialog(true);
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
        </Card>
      )}

      {/* Product Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Detalle del Producto
            </DialogTitle>
            <DialogDescription>
              Comparativa de precios entre proveedores
            </DialogDescription>
          </DialogHeader>
          
          {selectedProduct && (
            <div className="flex-1 overflow-y-auto space-y-6 py-4">
              {/* Product Info */}
              <div className="flex gap-6">
                <div className="w-32 h-32 flex-shrink-0">
                  {selectedProduct.image_url ? (
                    <img
                      src={selectedProduct.image_url}
                      alt={selectedProduct.name}
                      className="w-full h-full object-cover rounded-lg border border-slate-200"
                    />
                  ) : (
                    <div className="w-full h-full bg-slate-100 rounded-lg flex items-center justify-center">
                      <Package className="w-12 h-12 text-slate-300" />
                    </div>
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="text-xl font-semibold text-slate-900">{selectedProduct.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-slate-100 text-slate-700 border-0 font-mono">
                      EAN: {selectedProduct.ean}
                    </Badge>
                    {selectedProduct.brand && (
                      <Badge className="bg-indigo-100 text-indigo-700 border-0">
                        {selectedProduct.brand}
                      </Badge>
                    )}
                    {selectedProduct.category && (
                      <Badge className="bg-slate-100 text-slate-600 border-0">
                        {selectedProduct.category}
                      </Badge>
                    )}
                  </div>
                  {selectedProduct.description && (
                    <p className="text-sm text-slate-600 line-clamp-2">{selectedProduct.description}</p>
                  )}
                </div>
              </div>

              {/* Best Offer Highlight */}
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
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        supplier.is_best_offer
                          ? "bg-emerald-50 border-emerald-200"
                          : supplier.stock > 0
                          ? "bg-white border-slate-200"
                          : "bg-slate-50 border-slate-200 opacity-60"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          supplier.is_best_offer ? "bg-emerald-100" : "bg-slate-100"
                        }`}>
                          <Truck className={`w-4 h-4 ${supplier.is_best_offer ? "text-emerald-600" : "text-slate-500"}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-900">{supplier.supplier_name}</p>
                            {supplier.is_best_offer && (
                              <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">
                                <Star className="w-3 h-3 mr-1" />
                                Mejor
                              </Badge>
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
                          <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">
                            {supplier.stock} uds
                          </Badge>
                        ) : (
                          <Badge className="bg-rose-100 text-rose-700 border-0 text-xs">
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            Sin stock
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => setShowDetailDialog(false)} className="btn-secondary">
              Cerrar
            </Button>
            <Button 
              onClick={() => { 
                if (selectedProduct) {
                  openCatalogSelector([selectedProduct.ean]); 
                  setShowDetailDialog(false);
                }
              }}
              className="btn-primary"
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Añadir a Catálogos
            </Button>
          </DialogFooter>
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

export default Products;
