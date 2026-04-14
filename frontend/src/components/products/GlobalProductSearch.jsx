import { useState, useCallback, useEffect } from "react";
import { Search, ChevronDown, ChevronUp, Package, X, Filter, Loader2, BookOpen, PackagePlus, Check } from "lucide-react";
import { toast } from "sonner";
import { api } from "../../App";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../ui/dialog";
import { Checkbox } from "../ui/checkbox";

const ProductRow = ({ product, onSelectProduct, onAddToCatalog, isSelecting, isSelected }) => (
  <div className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
    {product.image_url ? (
      <img
        src={product.image_url}
        alt={product.name}
        className="w-9 h-9 object-cover rounded-sm border border-slate-200 shrink-0"
      />
    ) : (
      <div className="w-9 h-9 bg-slate-100 rounded-sm flex items-center justify-center shrink-0">
        <Package className="w-4 h-4 text-slate-400" />
      </div>
    )}
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-slate-800 truncate">{product.name}</p>
      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
        {product.brand && <span className="text-xs text-slate-400">{product.brand}</span>}
        {product.sku && <span className="text-xs font-mono text-slate-400">SKU: {product.sku}</span>}
        {product.part_number && <span className="text-xs font-mono text-slate-400">PN: {product.part_number}</span>}
        {product.ean && <span className="text-xs font-mono text-slate-400">EAN: {product.ean}</span>}
      </div>
    </div>
    <div className="text-right shrink-0">
      <p className="text-sm font-semibold text-slate-800">
        {product.price != null ? `${Number(product.price).toFixed(2)} €` : "—"}
      </p>
      <span className={`text-xs font-medium ${
        product.stock > 5 ? "text-emerald-600" :
        product.stock > 0 ? "text-amber-600" : "text-rose-500"
      }`}>
        {product.stock > 0 ? `${product.stock} uds` : "Sin stock"}
      </span>
    </div>
    {product.category && (
      <Badge variant="outline" className="text-xs shrink-0 hidden md:flex">
        {product.category}
      </Badge>
    )}

    {/* Botones de acción */}
    <div className="flex items-center gap-1 shrink-0">
      {/* Añadir a Productos */}
      <button
        onClick={() => onSelectProduct(product)}
        disabled={isSelecting || isSelected}
        title={isSelected ? "Ya en Productos" : "Añadir a Productos"}
        className={`p-1.5 rounded-sm transition-colors ${
          isSelected
            ? "text-emerald-600 bg-emerald-50 cursor-default"
            : isSelecting
            ? "text-slate-300 cursor-wait"
            : "text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
        }`}
      >
        {isSelecting ? <Loader2 className="w-4 h-4 animate-spin" />
          : isSelected ? <Check className="w-4 h-4" />
          : <PackagePlus className="w-4 h-4" />}
      </button>

      {/* Añadir a Catálogo(s) */}
      <button
        onClick={() => onAddToCatalog(product)}
        title="Añadir a catálogo(s)"
        className="p-1.5 rounded-sm text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
      >
        <BookOpen className="w-4 h-4" />
      </button>
    </div>
  </div>
);

const SupplierGroup = ({ group, limitPerSupplier, onSelectProduct, onAddToCatalog, selectingIds, selectedIds }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <Card className="border-slate-200">
      <CardHeader
        className="py-3 px-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-base font-semibold text-slate-800">
              {group.supplier?.name || "Proveedor desconocido"}
            </CardTitle>
            <Badge className="bg-indigo-100 text-indigo-700 border-indigo-200 text-xs">
              {group.count} {group.count === 1 ? "resultado" : "resultados"}
            </Badge>
            {group.count > limitPerSupplier && (
              <span className="text-xs text-slate-400">
                (mostrando {Math.min(group.products.length, limitPerSupplier)} de {group.count})
              </span>
            )}
          </div>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-0 px-4 pb-3">
          {group.products.map((product) => (
            <ProductRow
              key={product.id}
              product={product}
              onSelectProduct={onSelectProduct}
              onAddToCatalog={onAddToCatalog}
              isSelecting={selectingIds.has(product.id)}
              isSelected={selectedIds.has(product.id)}
            />
          ))}
          {group.count > limitPerSupplier && (
            <p className="text-xs text-slate-400 mt-2 text-center">
              {group.count - limitPerSupplier} productos más en este proveedor — refina la búsqueda para verlos
            </p>
          )}
        </CardContent>
      )}
    </Card>
  );
};

const GlobalProductSearch = ({ allCategories = [], allBrands = [] }) => {
  const LIMIT_PER_SUPPLIER = 15;

  const [searchParams, setSearchParams] = useState({
    q: "",
    category: "",
    brand: "",
    min_price: "",
    max_price: "",
    in_stock: false
  });
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null); // null = sin búsqueda aún

  // Estado para acciones de productos
  const [catalogs, setCatalogs] = useState([]);
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [productToAdd, setProductToAdd] = useState(null);
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [catalogCategories, setCatalogCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [addingToCatalog, setAddingToCatalog] = useState(false);
  const [selectingIds, setSelectingIds] = useState(new Set());
  const [selectedIds, setSelectedIds] = useState(new Set());

  const hasExtraFilters = searchParams.category || searchParams.brand ||
    searchParams.min_price || searchParams.max_price || searchParams.in_stock;

  // Cargar catálogos al montar
  useEffect(() => {
    api.get("/catalogs")
      .then(r => setCatalogs(r.data || []))
      .catch(() => setCatalogs([]));
  }, []);

  // Funciones de acción
  const handleSelectProduct = async (product) => {
    if (selectingIds.has(product.id) || selectedIds.has(product.id)) return;
    setSelectingIds(prev => new Set([...prev, product.id]));
    try {
      await api.post("/products/select", { product_ids: [product.id] });
      setSelectedIds(prev => new Set([...prev, product.id]));
      toast.success(`"${product.name.slice(0, 40)}" añadido a Productos`);
    } catch {
      toast.error("Error al añadir a Productos");
    } finally {
      setSelectingIds(prev => { const s = new Set(prev); s.delete(product.id); return s; });
    }
  };

  const handleOpenCatalogSelector = (product) => {
    if (catalogs.length === 0) {
      toast.error("No hay catálogos creados. Crea uno primero.");
      return;
    }
    setProductToAdd(product);
    const def = catalogs.find(c => c.is_default);
    setSelectedCatalogs(def ? new Set([def.id]) : new Set());
    setSelectedCategoryId("");
    setCatalogCategories([]);
    setShowCatalogDialog(true);
  };

  const toggleCatalogSelection = async (catalogId) => {
    const newSet = new Set(selectedCatalogs);
    if (newSet.has(catalogId)) {
      newSet.delete(catalogId);
    } else {
      newSet.add(catalogId);
      await loadCatalogCategories(catalogId);
    }
    setSelectedCatalogs(newSet);
  };

  const loadCatalogCategories = async (catalogId) => {
    setLoadingCategories(true);
    try {
      const res = await api.get(`/catalogs/${catalogId}/categories`);
      setCatalogCategories(res.data || []);
    } catch {
      setCatalogCategories([]);
    }
    setLoadingCategories(false);
  };

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
          product_ids: [productToAdd.id]
        };
        if (selectedCategoryId) {
          payload.category_ids = [selectedCategoryId];
        }
        const res = await api.post(`/catalogs/${catalogId}/products`, payload);
        totalAdded += res.data.added || 0;
      } catch {
        // error handled via toast below
      }
    }

    setAddingToCatalog(false);
    setShowCatalogDialog(false);
    setProductToAdd(null);
    setSelectedCategoryId("");
    setCatalogCategories([]);

    if (totalAdded > 0) {
      toast.success(`Producto añadido a los catálogos`);
    } else {
      toast.info("El producto ya estaba en los catálogos");
    }
  };

  const search = useCallback(async () => {
    if (!searchParams.q && !hasExtraFilters) {
      toast.info("Escribe algo para buscar");
      return;
    }
    setLoading(true);
    try {
      const params = {};
      if (searchParams.q) params.q = searchParams.q;
      if (searchParams.category) params.category = searchParams.category;
      if (searchParams.brand) params.brand = searchParams.brand;
      if (searchParams.min_price) params.min_price = searchParams.min_price;
      if (searchParams.max_price) params.max_price = searchParams.max_price;
      if (searchParams.in_stock) params.in_stock = "true";
      params.limit_per_supplier = LIMIT_PER_SUPPLIER;

      const res = await api.get("/products/search/global", { params });
      setResults(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al buscar productos");
    } finally {
      setLoading(false);
    }
  }, [searchParams, hasExtraFilters]);

  const clearSearch = () => {
    setSearchParams({ q: "", category: "", brand: "", min_price: "", max_price: "", in_stock: false });
    setResults(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") search();
  };

  return (
    <div className="space-y-4">
      {/* Barra de búsqueda principal */}
      <Card className="border-slate-200">
        <CardContent className="p-4">
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Buscar en todos los proveedores (nombre, SKU, EAN, marca, part number...)"
                  value={searchParams.q}
                  onChange={(e) => setSearchParams((p) => ({ ...p, q: e.target.value }))}
                  onKeyDown={handleKeyDown}
                  className="pl-10 input-base"
                  data-testid="global-search-input"
                />
                {searchParams.q && (
                  <button
                    onClick={() => setSearchParams((p) => ({ ...p, q: "" }))}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              <Button onClick={search} disabled={loading} className="btn-primary shrink-0" data-testid="global-search-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                {!loading && "Buscar"}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowFilters((v) => !v)}
                className={hasExtraFilters ? "border-indigo-300 text-indigo-700" : ""}
                data-testid="toggle-global-filters"
              >
                <Filter className="w-4 h-4 mr-2" />
                Filtros
                {hasExtraFilters && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                    activos
                  </span>
                )}
              </Button>
            </div>

            {/* Filtros opcionales */}
            {showFilters && (
              <div className="border border-slate-200 rounded-sm bg-slate-50 p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">
                  {/* Categoría */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Categoría</Label>
                    <Select
                      value={searchParams.category || "all"}
                      onValueChange={(v) => setSearchParams((p) => ({ ...p, category: v === "all" ? "" : v }))}
                    >
                      <SelectTrigger className="h-9 text-sm">
                        <SelectValue placeholder="Todas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas las categorías</SelectItem>
                        {allCategories.filter(Boolean).map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Marca */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Marca</Label>
                    {allBrands.length > 0 ? (
                      <Select
                        value={searchParams.brand || "all"}
                        onValueChange={(v) => setSearchParams((p) => ({ ...p, brand: v === "all" ? "" : v }))}
                      >
                        <SelectTrigger className="h-9 text-sm">
                          <SelectValue placeholder="Todas las marcas" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Todas las marcas</SelectItem>
                          {allBrands.map((b) => (
                            <SelectItem key={b} value={b}>{b}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        placeholder="Ej. Samsung"
                        value={searchParams.brand}
                        onChange={(e) => setSearchParams((p) => ({ ...p, brand: e.target.value }))}
                        onKeyDown={handleKeyDown}
                        className="h-9 text-sm"
                      />
                    )}
                  </div>

                  {/* Precio mínimo */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Precio mín. (€)</Label>
                    <Input
                      type="number"
                      placeholder="0"
                      min="0"
                      step="0.01"
                      value={searchParams.min_price}
                      onChange={(e) => setSearchParams((p) => ({ ...p, min_price: e.target.value }))}
                      onKeyDown={handleKeyDown}
                      className="h-9 text-sm"
                    />
                  </div>

                  {/* Precio máximo */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Precio máx. (€)</Label>
                    <Input
                      type="number"
                      placeholder="9999"
                      min="0"
                      step="0.01"
                      value={searchParams.max_price}
                      onChange={(e) => setSearchParams((p) => ({ ...p, max_price: e.target.value }))}
                      onKeyDown={handleKeyDown}
                      className="h-9 text-sm"
                    />
                  </div>

                  {/* Con stock */}
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-600">Disponibilidad</Label>
                    <Select
                      value={searchParams.in_stock ? "yes" : "all"}
                      onValueChange={(v) => setSearchParams((p) => ({ ...p, in_stock: v === "yes" }))}
                    >
                      <SelectTrigger className="h-9 text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="yes">Solo con stock</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {hasExtraFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSearchParams((p) => ({ ...p, category: "", brand: "", min_price: "", max_price: "", in_stock: false }))}
                    className="mt-3 text-xs text-slate-400 hover:text-rose-600 h-7"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Limpiar filtros
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Resultados */}
      {loading && (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin mr-3" />
          <span>Buscando en todos los proveedores...</span>
        </div>
      )}

      {!loading && results !== null && (
        <>
          {/* Resumen de resultados */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <p className="text-sm font-medium text-slate-700">
                {results.total > 0 ? (
                  <>
                    <span className="text-indigo-600 font-semibold">{results.total.toLocaleString()}</span>
                    {" "}producto{results.total !== 1 ? "s" : ""} encontrado{results.total !== 1 ? "s" : ""} en{" "}
                    <span className="text-indigo-600 font-semibold">{results.results.length}</span>
                    {" "}proveedor{results.results.length !== 1 ? "es" : ""}
                  </>
                ) : (
                  "Sin resultados"
                )}
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={clearSearch} className="text-xs text-slate-400 hover:text-slate-600">
              <X className="w-3 h-3 mr-1" />
              Nueva búsqueda
            </Button>
          </div>

          {/* Lista de grupos por proveedor */}
          {results.total === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <Search className="w-10 h-10" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: "Manrope, sans-serif" }}>
                Sin resultados
              </h3>
              <p className="text-slate-500">
                No se encontraron productos con los filtros aplicados. Prueba con otros términos o amplía los criterios.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.results.map((group) => (
                <SupplierGroup
                  key={group.supplier?.id || Math.random()}
                  group={group}
                  limitPerSupplier={LIMIT_PER_SUPPLIER}
                  onSelectProduct={handleSelectProduct}
                  onAddToCatalog={handleOpenCatalogSelector}
                  selectingIds={selectingIds}
                  selectedIds={selectedIds}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Estado inicial (sin búsqueda) */}
      {!loading && results === null && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400 gap-3">
          <Search className="w-10 h-10 text-slate-200" />
          <p className="text-sm">Escribe un término de búsqueda y pulsa <strong className="text-slate-500">Buscar</strong></p>
        </div>
      )}

      {/* Modal de selección de catálogos */}
      <Dialog open={showCatalogDialog} onOpenChange={(open) => {
        if (!open) {
          setProductToAdd(null);
          setSelectedCatalogs(new Set());
          setSelectedCategoryId("");
          setCatalogCategories([]);
        }
        setShowCatalogDialog(open);
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Añadir a catálogo(s)</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            {/* Lista de catálogos */}
            <div className="space-y-2">
              {catalogs.map((catalog) => (
                <div key={catalog.id} className="space-y-2">
                  <div className="flex items-center gap-3 p-3 border border-slate-200 rounded-sm hover:border-slate-300 transition-colors cursor-pointer"
                    onClick={() => toggleCatalogSelection(catalog.id)}>
                    <Checkbox checked={selectedCatalogs.has(catalog.id)} onChange={() => {}} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800">{catalog.name}</p>
                      {catalog.description && <p className="text-xs text-slate-500">{catalog.description}</p>}
                    </div>
                  </div>

                  {/* Selector de categoría si el catálogo está seleccionado */}
                  {selectedCatalogs.has(catalog.id) && (
                    <div className="ml-6 space-y-1">
                      <Label className="text-xs text-slate-600">Categoría (opcional)</Label>
                      <Select value={selectedCategoryId} onValueChange={setSelectedCategoryId}>
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue placeholder="Selecciona categoría..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">Sin categoría</SelectItem>
                          {flattenCategories(catalogCategories).map((cat) => (
                            <SelectItem key={cat.id} value={cat.id}>{cat.displayName}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {catalogs.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-4">No hay catálogos disponibles</p>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCatalogDialog(false);
                setProductToAdd(null);
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleConfirmAddToCatalogs}
              disabled={addingToCatalog || selectedCatalogs.size === 0}
              className="btn-primary"
            >
              {addingToCatalog ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Añadiendo...
                </>
              ) : (
                `Añadir`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GlobalProductSearch;
