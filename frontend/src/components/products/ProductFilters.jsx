import { useState } from "react";
import { Search, Filter, RefreshCw, Plus, CheckSquare, Upload } from "lucide-react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

const ProductFilters = ({
  filters,
  onFiltersChange,
  onSearch,
  onRefresh,
  categories,
  selectedCount,
  onAddSelected,
  onOpenUpload,
  loading
}) => {
  const handleSearchKeyPress = (e) => {
    if (e.key === "Enter") onSearch();
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Buscar productos..."
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
  );
};

export default ProductFilters;
