import { useState, useCallback } from "react";
import { Search, ChevronDown, ChevronUp, Package, X, Filter, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "../../App";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

const ProductRow = ({ product }) => (
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
  </div>
);

const SupplierGroup = ({ group, limitPerSupplier }) => {
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
            <ProductRow key={product.id} product={product} />
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

  const hasExtraFilters = searchParams.category || searchParams.brand ||
    searchParams.min_price || searchParams.max_price || searchParams.in_stock;

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
    </div>
  );
};

export default GlobalProductSearch;
