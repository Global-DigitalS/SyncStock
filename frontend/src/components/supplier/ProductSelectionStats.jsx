import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { CheckCircle, XCircle, ArrowRight, Layers } from "lucide-react";
import { CategorySelectionCascade } from "../suppliers";

export function ProductSelectionStats({
  selectionStats,
  categoryHierarchy,
  selectingProducts,
  onSelectAll,
  onDeselectAll,
  onNavigateToProducts,
  onSelectCategory,
  onDeselectCategory,
}) {
  return (
    <Card className="border-emerald-200 bg-emerald-50 mb-6">
      <CardContent className="p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
              <Layers className="w-6 h-6 text-emerald-600" strokeWidth={1.5} />
            </div>
            <div>
              <p className="font-semibold text-emerald-900">Flujo de Productos</p>
              <p className="text-sm text-emerald-700">
                <span className="font-bold">{selectionStats.selected}</span> de{" "}
                <span className="font-bold">{selectionStats.total}</span> productos están en la
                sección <span className="font-medium">Productos</span>
                {selectionStats.total > 0 && (
                  <span className="ml-2 text-xs bg-emerald-200 px-2 py-0.5 rounded-full">
                    {selectionStats.percentage}%
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              size="sm"
              variant="outline"
              onClick={onSelectAll}
              disabled={selectingProducts}
              className="border-emerald-300 text-emerald-700 hover:bg-emerald-100"
              data-testid="select-all-products-btn"
            >
              <CheckCircle className="w-4 h-4 mr-1.5" />
              Seleccionar Todos
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onDeselectAll}
              disabled={selectingProducts}
              className="border-slate-300 text-slate-600 hover:bg-slate-100"
              data-testid="deselect-all-products-btn"
            >
              <XCircle className="w-4 h-4 mr-1.5" />
              Quitar Todos
            </Button>
            <Button
              size="sm"
              onClick={onNavigateToProducts}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              data-testid="go-to-products-btn"
            >
              <ArrowRight className="w-4 h-4 mr-1.5" />
              Ir a Productos
            </Button>
          </div>
        </div>

        {categoryHierarchy.length > 0 && (
          <div className="mt-4 pt-4 border-t border-emerald-200">
            <p className="text-sm font-medium text-emerald-800 mb-3">Seleccionar por categoría:</p>
            <CategorySelectionCascade
              hierarchy={categoryHierarchy}
              onSelectCategory={(cat, subcat, subcat2) => onSelectCategory(cat, subcat, subcat2)}
              onDeselectCategory={(cat, subcat, subcat2) => onDeselectCategory(cat, subcat, subcat2)}
              disabled={selectingProducts}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
