import { useState, useEffect } from "react";
import { ChevronRight } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

const CategoryCascadeFilter = ({ 
  hierarchy = [], 
  selectedCategory,
  selectedSubcategory,
  selectedSubcategory2,
  onCategoryChange,
  onSubcategoryChange,
  onSubcategory2Change,
  onFilterChange
}) => {
  const [localCategory, setLocalCategory] = useState(selectedCategory || "");
  const [localSubcategory, setLocalSubcategory] = useState(selectedSubcategory || "");
  const [localSubcategory2, setLocalSubcategory2] = useState(selectedSubcategory2 || "");

  // Get subcategories for selected category
  const currentCategoryData = hierarchy.find(c => c.name === localCategory);
  const subcategories = currentCategoryData?.subcategories || [];
  
  // Get subcategory2 for selected subcategory
  const currentSubcategoryData = subcategories.find(s => s.name === localSubcategory);
  const subcategories2 = currentSubcategoryData?.subcategories || [];

  // Sync with props
  useEffect(() => {
    setLocalCategory(selectedCategory || "");
  }, [selectedCategory]);

  useEffect(() => {
    setLocalSubcategory(selectedSubcategory || "");
  }, [selectedSubcategory]);

  useEffect(() => {
    setLocalSubcategory2(selectedSubcategory2 || "");
  }, [selectedSubcategory2]);

  const handleCategoryChange = (value) => {
    const newValue = value === "all" ? "" : value;
    setLocalCategory(newValue);
    setLocalSubcategory("");
    setLocalSubcategory2("");
    
    if (onCategoryChange) onCategoryChange(newValue);
    if (onFilterChange) {
      onFilterChange({
        category: newValue,
        subcategory: "",
        subcategory2: ""
      });
    }
  };

  const handleSubcategoryChange = (value) => {
    const newValue = value === "all" ? "" : value;
    setLocalSubcategory(newValue);
    setLocalSubcategory2("");
    
    if (onSubcategoryChange) onSubcategoryChange(newValue);
    if (onFilterChange) {
      onFilterChange({
        category: localCategory,
        subcategory: newValue,
        subcategory2: ""
      });
    }
  };

  const handleSubcategory2Change = (value) => {
    const newValue = value === "all" ? "" : value;
    setLocalSubcategory2(newValue);
    
    if (onSubcategory2Change) onSubcategory2Change(newValue);
    if (onFilterChange) {
      onFilterChange({
        category: localCategory,
        subcategory: localSubcategory,
        subcategory2: newValue
      });
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap" data-testid="category-cascade-filter">
      {/* Category Select */}
      <Select value={localCategory || "all"} onValueChange={handleCategoryChange}>
        <SelectTrigger className="w-[180px] input-base" data-testid="filter-category">
          <SelectValue placeholder="Categoría" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todas las categorías</SelectItem>
          {hierarchy.filter(cat => cat.name).map((cat) => (
            <SelectItem key={cat.name} value={cat.name}>
              <div className="flex items-center justify-between w-full gap-2">
                <span>{cat.name}</span>
                <span className="text-xs text-slate-400">({cat.count})</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Subcategory Select - Only show if category selected and has subcategories */}
      {localCategory && subcategories.length > 0 && (
        <>
          <ChevronRight className="w-4 h-4 text-slate-400" />
          <Select value={localSubcategory || "all"} onValueChange={handleSubcategoryChange}>
            <SelectTrigger className="w-[180px] input-base" data-testid="filter-subcategory">
              <SelectValue placeholder="Subcategoría" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              {subcategories.filter(subcat => subcat.name).map((subcat) => (
                <SelectItem key={subcat.name} value={subcat.name}>
                  <div className="flex items-center justify-between w-full gap-2">
                    <span>{subcat.name}</span>
                    <span className="text-xs text-slate-400">({subcat.count})</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </>
      )}

      {/* Subcategory2 Select - Only show if subcategory selected and has more levels */}
      {localSubcategory && subcategories2.length > 0 && (
        <>
          <ChevronRight className="w-4 h-4 text-slate-400" />
          <Select value={localSubcategory2 || "all"} onValueChange={handleSubcategory2Change}>
            <SelectTrigger className="w-[180px] input-base" data-testid="filter-subcategory2">
              <SelectValue placeholder="Sub-subcategoría" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              {subcategories2.filter(subcat2 => subcat2.name).map((subcat2) => (
                <SelectItem key={subcat2.name} value={subcat2.name}>
                  <div className="flex items-center justify-between w-full gap-2">
                    <span>{subcat2.name}</span>
                    <span className="text-xs text-slate-400">({subcat2.count})</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </>
      )}
    </div>
  );
};

export default CategoryCascadeFilter;
