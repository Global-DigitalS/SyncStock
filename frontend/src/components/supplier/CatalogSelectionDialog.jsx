import { useState } from "react";
import { BookOpen, Star, RefreshCw, Plus } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Checkbox } from "../ui/checkbox";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "../ui/dialog";

export function CatalogSelectionDialog({
  open,
  onOpenChange,
  catalogs,
  productsCount,
  addingToCatalog,
  onConfirm,
  onNavigateToCatalogs,
}) {
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());

  const toggle = (catalogId) => {
    setSelectedCatalogs((prev) => {
      const next = new Set(prev);
      if (next.has(catalogId)) next.delete(catalogId);
      else next.add(catalogId);
      return next;
    });
  };

  const handleConfirm = () => {
    onConfirm(selectedCatalogs);
    setSelectedCatalogs(new Set());
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) setSelectedCatalogs(new Set()); onOpenChange(v); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: "Manrope, sans-serif" }}>
            <BookOpen className="w-5 h-5 text-indigo-600" />
            Añadir a Catálogos
          </DialogTitle>
          <DialogDescription>
            Selecciona los catálogos donde quieres añadir {productsCount} producto{productsCount !== 1 ? "s" : ""}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-2 max-h-[300px] overflow-y-auto">
          {catalogs.length === 0 ? (
            <div className="text-center py-6">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500">No hay catálogos creados</p>
              <Button variant="link" onClick={onNavigateToCatalogs} className="mt-2">
                Crear catálogo
              </Button>
            </div>
          ) : (
            catalogs.map((catalog) => (
              <div
                key={catalog.id}
                onClick={() => toggle(catalog.id)}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedCatalogs.has(catalog.id)
                    ? "bg-indigo-50 border-indigo-300"
                    : "bg-white border-slate-200 hover:border-slate-300"
                }`}
                data-testid={`catalog-option-${catalog.id}`}
              >
                <Checkbox
                  checked={selectedCatalogs.has(catalog.id)}
                  onCheckedChange={() => toggle(catalog.id)}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{catalog.name}</span>
                    {catalog.is_default && (
                      <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">
                        <Star className="w-3 h-3 mr-1" />Defecto
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {catalog.product_count} productos · {catalog.margin_rules_count} reglas
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="btn-secondary">
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
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
  );
}
