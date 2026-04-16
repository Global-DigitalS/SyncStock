import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Card, CardContent } from "../ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Search, ChevronDown, ChevronUp, X } from "lucide-react";
import { CategoryCascadeFilter } from "../suppliers";

const hasAdvancedFilters = (filters) =>
  !!(filters.brand || filters.part_number || filters.min_price || filters.max_price || filters.min_stock);

export function ProductFiltersCard({
  filters,
  brands,
  categoryHierarchy,
  showAdvancedFilters,
  onFiltersChange,
  onSearch,
  onToggleAdvancedFilters,
}) {
  const activeAdvanced = hasAdvancedFilters(filters);

  const clearAdvancedFilters = () => {
    onFiltersChange({ ...filters, brand: "", part_number: "", min_price: "", max_price: "", min_stock: "" });
    setTimeout(() => onSearch(), 0);
  };

  return (
    <Card className="border-slate-200 mb-6">
      <CardContent className="p-4">
        <div className="flex flex-col gap-4">
          {/* Main filters row */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
                strokeWidth={1.5}
              />
              <Input
                placeholder="Buscar por nombre, SKU o EAN..."
                value={filters.search}
                onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
                className="pl-9 input-base"
                data-testid="search-products"
              />
            </div>
            <Select
              value={filters.stock}
              onValueChange={(value) => onFiltersChange({ ...filters, stock: value })}
            >
              <SelectTrigger className="w-full lg:w-[150px] input-base" data-testid="filter-stock">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo el stock</SelectItem>
                <SelectItem value="in">Con stock</SelectItem>
                <SelectItem value="low">Stock bajo</SelectItem>
                <SelectItem value="out">Sin stock</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.selection}
              onValueChange={(value) => onFiltersChange({ ...filters, selection: value })}
            >
              <SelectTrigger className="w-full lg:w-[180px] input-base" data-testid="filter-selection">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="selected">En Productos</SelectItem>
                <SelectItem value="unselected">No en Productos</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Category filter */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-slate-600">Filtrar por categoría:</span>
            <CategoryCascadeFilter
              hierarchy={categoryHierarchy}
              selectedCategory={filters.category}
              selectedSubcategory={filters.subcategory}
              selectedSubcategory2={filters.subcategory2}
              onFilterChange={({ category, subcategory, subcategory2 }) => {
                onFiltersChange({ ...filters, category, subcategory, subcategory2 });
              }}
            />
          </div>

          {/* Advanced filters toggle */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onToggleAdvancedFilters}
              className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border transition-colors ${
                activeAdvanced
                  ? "border-indigo-300 bg-indigo-50 text-indigo-700 font-medium"
                  : "border-slate-200 bg-white text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
              data-testid="toggle-advanced-filters"
            >
              {showAdvancedFilters ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              Filtros avanzados
              {activeAdvanced && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                  activos
                </span>
              )}
            </button>
            {activeAdvanced && (
              <button
                type="button"
                onClick={clearAdvancedFilters}
                className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-600 transition-colors"
              >
                <X className="w-3 h-3" />
                Limpiar avanzados
              </button>
            )}
          </div>

          {/* Advanced filters panel */}
          {showAdvancedFilters && (
            <div className="border border-slate-200 rounded-sm bg-slate-50 p-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Part Number / Ref.</Label>
                  <Input
                    placeholder="Ej. ABC-1234"
                    value={filters.part_number}
                    onChange={(e) => onFiltersChange({ ...filters, part_number: e.target.value })}
                    onKeyDown={(e) => e.key === "Enter" && onSearch()}
                    className="h-9 text-sm input-base"
                    data-testid="part-number-filter"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Marca</Label>
                  {brands.length > 0 ? (
                    <Select
                      value={filters.brand || "all"}
                      onValueChange={(v) =>
                        onFiltersChange({ ...filters, brand: v === "all" ? "" : v })
                      }
                    >
                      <SelectTrigger className="h-9 text-sm input-base" data-testid="brand-filter">
                        <SelectValue placeholder="Todas las marcas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas las marcas</SelectItem>
                        {brands.map((b) => (
                          <SelectItem key={b} value={b}>
                            {b}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input
                      placeholder="Ej. Samsung"
                      value={filters.brand}
                      onChange={(e) => onFiltersChange({ ...filters, brand: e.target.value })}
                      onKeyDown={(e) => e.key === "Enter" && onSearch()}
                      className="h-9 text-sm input-base"
                      data-testid="brand-filter"
                    />
                  )}
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Precio mín. (€)</Label>
                  <Input
                    type="number"
                    placeholder="0"
                    min="0"
                    step="0.01"
                    value={filters.min_price}
                    onChange={(e) => onFiltersChange({ ...filters, min_price: e.target.value })}
                    onKeyDown={(e) => e.key === "Enter" && onSearch()}
                    className="h-9 text-sm input-base"
                    data-testid="min-price-filter"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Precio máx. (€)</Label>
                  <Input
                    type="number"
                    placeholder="9999"
                    min="0"
                    step="0.01"
                    value={filters.max_price}
                    onChange={(e) => onFiltersChange({ ...filters, max_price: e.target.value })}
                    onKeyDown={(e) => e.key === "Enter" && onSearch()}
                    className="h-9 text-sm input-base"
                    data-testid="max-price-filter"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-slate-600">Stock mínimo</Label>
                  <Input
                    type="number"
                    placeholder="1"
                    min="0"
                    value={filters.min_stock}
                    onChange={(e) => onFiltersChange({ ...filters, min_stock: e.target.value })}
                    onKeyDown={(e) => e.key === "Enter" && onSearch()}
                    className="h-9 text-sm input-base"
                    data-testid="min-stock-filter"
                  />
                </div>
              </div>
              <p className="text-xs text-slate-400 mt-3">
                Los filtros avanzados se combinan entre sí (AND lógico). Pulsa <strong>Buscar</strong>{" "}
                o Enter para aplicarlos.
              </p>
            </div>
          )}

          <div>
            <Button onClick={onSearch} className="btn-primary" data-testid="search-btn">
              <Search className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Buscar
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
