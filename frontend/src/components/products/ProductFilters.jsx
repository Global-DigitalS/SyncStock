import { useState } from "react";
import { Search, Filter, RefreshCw, Plus, CheckSquare, Upload, ChevronDown, ChevronUp, X } from "lucide-react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Label } from "../ui/label";

const ProductFilters = ({
  filters,
  onFiltersChange,
  onSearch,
  onRefresh,
  categories,
  brands = [],
  selectedCount,
  onAddSelected,
  onOpenUpload,
  loading
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSearchKeyPress = (e) => {
    if (e.key === "Enter") onSearch();
  };

  const hasAdvancedFilters = filters.brand || filters.part_number ||
    filters.min_price || filters.max_price || filters.min_stock;

  const clearAdvancedFilters = () => {
    onFiltersChange({
      ...filters,
      brand: "",
      part_number: "",
      min_price: "",
      max_price: "",
      min_stock: ""
    });
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Fila principal de filtros */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Buscar por nombre, SKU, EAN..."
              className="pl-10 w-64"
              value={filters.search}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              onKeyPress={handleSearchKeyPress}
              data-testid="product-search-input"
            />
          </div>

          <Select
            value={filters.category}
            onValueChange={(value) => onFiltersChange({ ...filters, category: value })}
          >
            <SelectTrigger className="w-48" data-testid="category-filter">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Categoría" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las categorías</SelectItem>
              {categories.filter(Boolean).map((cat) => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={filters.stock}
            onValueChange={(value) => onFiltersChange({ ...filters, stock: value })}
          >
            <SelectTrigger className="w-36" data-testid="stock-filter">
              <SelectValue placeholder="Stock" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todo el stock</SelectItem>
              <SelectItem value="available">Con stock</SelectItem>
              <SelectItem value="low">Stock bajo</SelectItem>
              <SelectItem value="out">Sin stock</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={onSearch} data-testid="search-btn">
            <Search className="w-4 h-4 mr-2" />
            Buscar
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced((v) => !v)}
            className={`text-slate-500 hover:text-slate-700 ${hasAdvancedFilters ? "text-indigo-600 font-medium" : ""}`}
            data-testid="toggle-advanced-filters"
          >
            {showAdvanced ? <ChevronUp className="w-4 h-4 mr-1" /> : <ChevronDown className="w-4 h-4 mr-1" />}
            Filtros avanzados
            {hasAdvancedFilters && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                activos
              </span>
            )}
          </Button>
        </div>

        <div className="flex gap-2">
          {selectedCount > 0 && (
            <Button onClick={onAddSelected} data-testid="add-selected-to-catalog">
              <CheckSquare className="w-4 h-4 mr-2" />
              Añadir {selectedCount} a catálogo
            </Button>
          )}

          <Button variant="outline" onClick={onOpenUpload} data-testid="upload-products-btn">
            <Upload className="w-4 h-4 mr-2" />
            Subir
          </Button>

          <Button variant="outline" onClick={onRefresh} disabled={loading} data-testid="refresh-products">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Panel de filtros avanzados */}
      {showAdvanced && (
        <div className="border border-slate-200 rounded-sm bg-slate-50 p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-slate-700">Filtros avanzados</p>
            {hasAdvancedFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAdvancedFilters}
                className="text-xs text-slate-500 hover:text-rose-600 h-7"
              >
                <X className="w-3 h-3 mr-1" />
                Limpiar filtros avanzados
              </Button>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* Part Number */}
            <div className="space-y-1">
              <Label className="text-xs text-slate-600">Part Number / Ref.</Label>
              <Input
                placeholder="Ej. ABC-1234"
                value={filters.part_number || ""}
                onChange={(e) => onFiltersChange({ ...filters, part_number: e.target.value })}
                onKeyPress={handleSearchKeyPress}
                className="h-9 text-sm"
                data-testid="part-number-filter"
              />
            </div>

            {/* Marca */}
            <div className="space-y-1">
              <Label className="text-xs text-slate-600">Marca</Label>
              {brands.length > 0 ? (
                <Select
                  value={filters.brand || ""}
                  onValueChange={(value) => onFiltersChange({ ...filters, brand: value === "all" ? "" : value })}
                >
                  <SelectTrigger className="h-9 text-sm" data-testid="brand-filter">
                    <SelectValue placeholder="Todas las marcas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas las marcas</SelectItem>
                    {brands.map((b) => (
                      <SelectItem key={b} value={b}>{b}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  placeholder="Ej. Samsung"
                  value={filters.brand || ""}
                  onChange={(e) => onFiltersChange({ ...filters, brand: e.target.value })}
                  onKeyPress={handleSearchKeyPress}
                  className="h-9 text-sm"
                  data-testid="brand-filter"
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
                value={filters.min_price || ""}
                onChange={(e) => onFiltersChange({ ...filters, min_price: e.target.value })}
                onKeyPress={handleSearchKeyPress}
                className="h-9 text-sm"
                data-testid="min-price-filter"
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
                value={filters.max_price || ""}
                onChange={(e) => onFiltersChange({ ...filters, max_price: e.target.value })}
                onKeyPress={handleSearchKeyPress}
                className="h-9 text-sm"
                data-testid="max-price-filter"
              />
            </div>

            {/* Stock mínimo */}
            <div className="space-y-1">
              <Label className="text-xs text-slate-600">Stock mínimo</Label>
              <Input
                type="number"
                placeholder="1"
                min="0"
                value={filters.min_stock || ""}
                onChange={(e) => onFiltersChange({ ...filters, min_stock: e.target.value })}
                onKeyPress={handleSearchKeyPress}
                className="h-9 text-sm"
                data-testid="min-stock-filter"
              />
            </div>
          </div>

          <p className="text-xs text-slate-400 mt-3">
            Los filtros avanzados se combinan entre sí (AND lógico). Pulsa <strong>Buscar</strong> para aplicarlos.
          </p>
        </div>
      )}
    </div>
  );
};

export default ProductFilters;
