import { CheckSquare, CheckCircle, XCircle, RefreshCw, BookOpen } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";

export function SelectionActionsBar({
  count,
  selectingProducts,
  addingToCatalog,
  onClear,
  onAddToProducts,
  onRemoveFromProducts,
  onAddToCatalogs,
}) {
  if (count === 0) return null;

  return (
    <Card className="border-indigo-200 bg-indigo-50 mb-6 animate-slide-up">
      <CardContent className="p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckSquare className="w-5 h-5 text-indigo-600" strokeWidth={1.5} />
            <span className="font-medium text-indigo-900">
              {count} producto{count !== 1 ? "s" : ""} seleccionado{count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={onClear} className="btn-secondary" data-testid="clear-selection">
              Limpiar
            </Button>
            <Button
              size="sm"
              onClick={onAddToProducts}
              disabled={selectingProducts}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              data-testid="add-to-products-section"
            >
              {selectingProducts ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" strokeWidth={1.5} />
              )}
              Añadir a Productos
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onRemoveFromProducts}
              disabled={selectingProducts}
              className="border-rose-300 text-rose-600 hover:bg-rose-50"
              data-testid="remove-from-products-section"
            >
              <XCircle className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Quitar de Productos
            </Button>
            <Button
              size="sm"
              onClick={onAddToCatalogs}
              disabled={addingToCatalog}
              className="btn-primary"
              data-testid="add-selected-to-catalog"
            >
              {addingToCatalog ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
              ) : (
                <BookOpen className="w-4 h-4 mr-2" strokeWidth={1.5} />
              )}
              Añadir a Catálogos
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
