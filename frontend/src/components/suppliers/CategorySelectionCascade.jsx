import { useState, useEffect } from "react";
import { ChevronRight, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Button } from "../ui/button";

const CategorySelectionCascade = ({ 
  hierarchy = [], 
  onSelectCategory,
  onDeselectCategory,
  disabled = false
}) => {
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedSubcategory, setSelectedSubcategory] = useState("");
  const [selectedSubcategory2, setSelectedSubcategory2] = useState("");

  // Get subcategories for selected category
  const currentCategoryData = hierarchy.find(c => c.name === selectedCategory);
  const subcategories = currentCategoryData?.subcategories || [];
  
  // Get subcategory2 for selected subcategory
  const currentSubcategoryData = subcategories.find(s => s.name === selectedSubcategory);
  const subcategories2 = currentSubcategoryData?.subcategories || [];

  // Get the most specific selection data
  const getSelectionData = () => {
    if (selectedSubcategory2) {
      const subcat2Data = subcategories2.find(s => s.name === selectedSubcategory2);
      return {
        category: selectedCategory,
        subcategory: selectedSubcategory,
        subcategory2: selectedSubcategory2,
        count: subcat2Data?.count || 0,
        selected_count: subcat2Data?.selected_count || 0,
        label: `${selectedCategory} > ${selectedSubcategory} > ${selectedSubcategory2}`
      };
    }
    if (selectedSubcategory) {
      const subcatData = subcategories.find(s => s.name === selectedSubcategory);
      return {
        category: selectedCategory,
        subcategory: selectedSubcategory,
        subcategory2: null,
        count: subcatData?.count || 0,
        selected_count: subcatData?.selected_count || 0,
        label: `${selectedCategory} > ${selectedSubcategory}`
      };
    }
    if (selectedCategory) {
      return {
        category: selectedCategory,
        subcategory: null,
        subcategory2: null,
        count: currentCategoryData?.count || 0,
        selected_count: currentCategoryData?.selected_count || 0,
        label: selectedCategory
      };
    }
    return null;
  };

  const selectionData = getSelectionData();
  const canSelect = selectionData && selectionData.count > selectionData.selected_count;
  const canDeselect = selectionData && selectionData.selected_count > 0;

  const handleCategoryChange = (value) => {
    const newValue = value === "all" ? "" : value;
    setSelectedCategory(newValue);
    setSelectedSubcategory("");
    setSelectedSubcategory2("");
  };

  const handleSubcategoryChange = (value) => {
    const newValue = value === "all" ? "" : value;
    setSelectedSubcategory(newValue);
    setSelectedSubcategory2("");
  };

  const handleSubcategory2Change = (value) => {
    const newValue = value === "all" ? "" : value;
    setSelectedSubcategory2(newValue);
  };

  const handleSelect = () => {
    if (selectionData && onSelectCategory) {
      onSelectCategory(selectionData.category, selectionData.subcategory, selectionData.subcategory2);
    }
  };

  const handleDeselect = () => {
    if (selectionData && onDeselectCategory) {
      onDeselectCategory(selectionData.category, selectionData.subcategory, selectionData.subcategory2);
    }
  };

  return (
    <div className="space-y-3" data-testid="category-selection-cascade">
      {/* Cascade Selectors */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Category Select */}
        <Select value={selectedCategory || "all"} onValueChange={handleCategoryChange} disabled={disabled}>
          <SelectTrigger className="w-[180px] bg-white border-emerald-200" data-testid="select-category-dropdown">
            <SelectValue placeholder="Seleccionar categoría" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Seleccionar categoría</SelectItem>
            {hierarchy.filter(cat => cat.name).map((cat) => (
              <SelectItem key={cat.name} value={cat.name}>
                <div className="flex items-center justify-between w-full gap-2">
                  <span>{cat.name}</span>
                  <span className="text-xs text-emerald-600">
                    ({cat.selected_count}/{cat.count})
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Subcategory Select */}
        {selectedCategory && subcategories.length > 0 && (
          <>
            <ChevronRight className="w-4 h-4 text-emerald-400" />
            <Select value={selectedSubcategory || "all"} onValueChange={handleSubcategoryChange} disabled={disabled}>
              <SelectTrigger className="w-[180px] bg-white border-emerald-200" data-testid="select-subcategory-dropdown">
                <SelectValue placeholder="Subcategoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las subcategorías</SelectItem>
                {subcategories.filter(subcat => subcat.name).map((subcat) => (
                  <SelectItem key={subcat.name} value={subcat.name}>
                    <div className="flex items-center justify-between w-full gap-2">
                      <span>{subcat.name}</span>
                      <span className="text-xs text-emerald-600">
                        ({subcat.selected_count}/{subcat.count})
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        )}

        {/* Subcategory2 Select */}
        {selectedSubcategory && subcategories2.length > 0 && (
          <>
            <ChevronRight className="w-4 h-4 text-emerald-400" />
            <Select value={selectedSubcategory2 || "all"} onValueChange={handleSubcategory2Change} disabled={disabled}>
              <SelectTrigger className="w-[180px] bg-white border-emerald-200" data-testid="select-subcategory2-dropdown">
                <SelectValue placeholder="Sub-subcategoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                {subcategories2.filter(subcat2 => subcat2.name).map((subcat2) => (
                  <SelectItem key={subcat2.name} value={subcat2.name}>
                    <div className="flex items-center justify-between w-full gap-2">
                      <span>{subcat2.name}</span>
                      <span className="text-xs text-emerald-600">
                        ({subcat2.selected_count}/{subcat2.count})
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        )}
      </div>

      {/* Action Buttons - Only show when a category is selected */}
      {selectionData && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-emerald-700 bg-emerald-100 px-2 py-1 rounded">
            {selectionData.label}: {selectionData.selected_count}/{selectionData.count} seleccionados
          </span>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleSelect}
            disabled={disabled || !canSelect}
            className="h-7 text-xs border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            data-testid="select-category-btn"
          >
            {disabled ? (
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <CheckCircle className="w-3 h-3 mr-1" />
            )}
            Seleccionar ({selectionData.count - selectionData.selected_count})
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleDeselect}
            disabled={disabled || !canDeselect}
            className="h-7 text-xs border-rose-300 text-rose-600 hover:bg-rose-50"
            data-testid="deselect-category-btn"
          >
            <XCircle className="w-3 h-3 mr-1" />
            Quitar ({selectionData.selected_count})
          </Button>
        </div>
      )}
    </div>
  );
};

export default CategorySelectionCascade;
