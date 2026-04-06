import { useState } from "react";
import { RefreshCw, BookOpen, Star, Plus } from "lucide-react";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { Badge } from "../components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";

const CatalogSelectorDialog = ({
  open,
  onOpenChange,
  catalogs,
  productIds,
  onConfirm
}) => {
  const [selectedCatalogs, setSelectedCatalogs] = useState(new Set());
  const [adding, setAdding] = useState(false);

  const toggleCatalogSelection = (catalogId) => {
    setSelectedCatalogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(catalogId)) {
        newSet.delete(catalogId);
      } else {
        newSet.add(catalogId);
      }
      return newSet;
    });
  };

  const handleConfirm = async () => {
    if (selectedCatalogs.size === 0) return;
    setAdding(true);
    await onConfirm(Array.from(selectedCatalogs), productIds);
    setAdding(false);
    setSelectedCatalogs(new Set());
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <BookOpen className="w-5 h-5 text-indigo-600" />
            Añadir a Catálogos
          </DialogTitle>
          <DialogDescription>
            Se añadirá la mejor oferta de cada producto seleccionado
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4 space-y-2 max-h-[300px] overflow-y-auto">
          {catalogs.length === 0 ? (
            <div className="text-center py-6">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500">No hay catálogos creados</p>
            </div>
          ) : (
            catalogs.map((catalog) => (
              <div
                key={catalog.id}
                onClick={() => toggleCatalogSelection(catalog.id)}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedCatalogs.has(catalog.id)
                    ? "bg-indigo-50 border-indigo-300"
                    : "bg-white border-slate-200 hover:border-slate-300"
                }`}
                data-testid={`catalog-option-${catalog.id}`}
              >
                <Checkbox
                  checked={selectedCatalogs.has(catalog.id)}
                  onCheckedChange={() => toggleCatalogSelection(catalog.id)}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{catalog.name}</span>
                    {catalog.is_default && (
                      <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">
                        <Star className="w-3 h-3 mr-1" />
                        Defecto
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {catalog.product_count} productos • {catalog.margin_rules_count} reglas
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
            disabled={adding || selectedCatalogs.size === 0}
            className="btn-primary"
            data-testid="confirm-add-to-catalogs"
          >
            {adding ? (
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
};

export default CatalogSelectorDialog;
