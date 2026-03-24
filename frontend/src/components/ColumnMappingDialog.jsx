import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import {
  ArrowRight,
  Check,
  AlertCircle,
  Database,
  FileSpreadsheet,
  RefreshCw,
  X
} from "lucide-react";

// Campos del sistema disponibles para mapear
const SYSTEM_FIELDS = [
  { key: "sku", label: "SKU / Referencia", required: true, description: "Código único del producto" },
  { key: "name", label: "Nombre", required: true, description: "Nombre del producto" },
  { key: "description", label: "Descripción", required: false, description: "Descripción larga del producto" },
  { key: "short_description", label: "Descripción corta", required: false, description: "Descripción breve" },
  { key: "price", label: "Precio", required: true, description: "Precio de compra" },
  { key: "price2", label: "Precio 2 (PVP)", required: false, description: "Precio de venta recomendado" },
  { key: "stock", label: "Stock", required: true, description: "Cantidad disponible" },
  { key: "category", label: "Categoría", required: false, description: "Categoría principal" },
  { key: "subcategory", label: "Subcategoría", required: false, description: "Subcategoría" },
  { key: "subcategory2", label: "Subcategoría 2", required: false, description: "Subcategoría nivel 2" },
  { key: "brand", label: "Marca", required: false, description: "Marca o fabricante" },
  { key: "ean", label: "EAN / Código de barras", required: false, critical: true, description: "Requerido para ver productos en 'Productos'" },
  { key: "weight", label: "Peso (kg)", required: false, description: "Peso en kilogramos" },
  { key: "image_url", label: "URL Imagen 1", required: false, description: "URL de la imagen principal" },
  { key: "image_url2", label: "URL Imagen 2", required: false, description: "URL de imagen secundaria" },
  { key: "image_url3", label: "URL Imagen 3", required: false, description: "URL de imagen adicional" },
];

const ColumnMappingDialog = ({ 
  open, 
  onOpenChange, 
  detectedColumns = [], 
  currentMapping = null,
  suggestedMapping = null,
  onSave,
  saving = false 
}) => {
  const [mapping, setMapping] = useState({});

  useEffect(() => {
    if (currentMapping) {
      setMapping(currentMapping);
    } else if (suggestedMapping) {
      // Use server-side suggested mapping
      setMapping(suggestedMapping);
    } else {
      // Auto-detectar mapeo basado en nombres similares
      const autoMapping = {};
      detectedColumns.forEach(col => {
        const colLower = col.toLowerCase().trim();
        const matchedField = SYSTEM_FIELDS.find(f => {
          const fieldLower = f.key.toLowerCase();
          return colLower === fieldLower || 
                 colLower.includes(fieldLower) || 
                 fieldLower.includes(colLower) ||
                 // Mapeos comunes en español
                 (fieldLower === 'name' && (colLower.includes('nombre') || colLower.includes('title'))) ||
                 (fieldLower === 'sku' && (colLower.includes('codigo') || colLower.includes('referencia') || colLower.includes('ref'))) ||
                 (fieldLower === 'price' && (colLower.includes('precio') || colLower.includes('pvp') || colLower.includes('cost'))) ||
                 (fieldLower === 'stock' && (colLower.includes('cantidad') || colLower.includes('qty') || colLower.includes('inventory'))) ||
                 (fieldLower === 'category' && (colLower.includes('categoria') || colLower.includes('tipo'))) ||
                 (fieldLower === 'brand' && (colLower.includes('marca') || colLower.includes('fabricante'))) ||
                 (fieldLower === 'ean' && (colLower.includes('barcode') || colLower.includes('upc') || colLower.includes('ean13'))) ||
                 (fieldLower === 'weight' && (colLower.includes('peso') || colLower.includes('kg'))) ||
                 (fieldLower === 'image_url' && (colLower.includes('imagen') || colLower.includes('image') || colLower.includes('foto'))) ||
                 (fieldLower === 'description' && (colLower.includes('descripcion') || colLower.includes('desc')));
        });
        if (matchedField && !autoMapping[matchedField.key]) {
          autoMapping[matchedField.key] = col;
        }
      });
      setMapping(autoMapping);
    }
  }, [detectedColumns, currentMapping, open, suggestedMapping]);

  const handleMappingChange = (systemField, supplierColumn) => {
    setMapping(prev => {
      const newMapping = { ...prev };
      if (supplierColumn === "none") {
        delete newMapping[systemField];
      } else {
        newMapping[systemField] = supplierColumn;
      }
      return newMapping;
    });
  };

  const handleSave = () => {
    onSave(mapping);
  };

  const handleAutoDetect = () => {
    const autoMapping = {};
    detectedColumns.forEach(col => {
      const colLower = col.toLowerCase().trim();
      const matchedField = SYSTEM_FIELDS.find(f => {
        const fieldLower = f.key.toLowerCase();
        return colLower === fieldLower || 
               colLower.includes(fieldLower) || 
               fieldLower.includes(colLower) ||
               (fieldLower === 'name' && (colLower.includes('nombre') || colLower.includes('title'))) ||
               (fieldLower === 'sku' && (colLower.includes('codigo') || colLower.includes('referencia') || colLower.includes('ref'))) ||
               (fieldLower === 'price' && (colLower.includes('precio') || colLower.includes('pvp') || colLower.includes('cost'))) ||
               (fieldLower === 'stock' && (colLower.includes('cantidad') || colLower.includes('qty') || colLower.includes('inventory'))) ||
               (fieldLower === 'category' && (colLower.includes('categoria') || colLower.includes('tipo'))) ||
               (fieldLower === 'brand' && (colLower.includes('marca') || colLower.includes('fabricante'))) ||
               (fieldLower === 'ean' && (colLower.includes('barcode') || colLower.includes('upc') || colLower.includes('ean13'))) ||
               (fieldLower === 'weight' && (colLower.includes('peso') || colLower.includes('kg'))) ||
               (fieldLower === 'image_url' && (colLower.includes('imagen') || colLower.includes('image') || colLower.includes('foto'))) ||
               (fieldLower === 'description' && (colLower.includes('descripcion') || colLower.includes('desc')));
      });
      if (matchedField && !autoMapping[matchedField.key]) {
        autoMapping[matchedField.key] = col;
      }
    });
    setMapping(autoMapping);
  };

  const handleClearAll = () => {
    setMapping({});
  };

  const requiredFieldsMapped = SYSTEM_FIELDS.filter(f => f.required).every(f => mapping[f.key]);
  const mappedCount = Object.keys(mapping).length;
  const eanMapped = !!mapping.ean;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <Database className="w-5 h-5 text-indigo-600" />
            Mapeo de Columnas
          </DialogTitle>
          <DialogDescription>
            Asigna las columnas del archivo del proveedor a los campos del sistema
          </DialogDescription>
        </DialogHeader>

        {/* Info Banner */}
        <Card className="border-amber-200 bg-amber-50 shrink-0">
          <CardContent className="p-3 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-800">
              Los campos marcados con <span className="font-semibold">*</span> son obligatorios. 
              Mapea al menos SKU, Nombre, Precio y Stock para una importación correcta.
            </p>
          </CardContent>
        </Card>

        {/* EAN Warning Banner */}
        {!eanMapped && (
          <Card className="border-rose-300 bg-rose-50 shrink-0" data-testid="ean-warning-banner">
            <CardContent className="p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-rose-800">
                  ¡Importante! El campo EAN no está mapeado
                </p>
                <p className="text-xs text-rose-700 mt-1">
                  Sin el EAN, los productos <strong>no aparecerán</strong> en la sección "Productos". 
                  El EAN es necesario para unificar productos de diferentes proveedores y compararlos.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between shrink-0 py-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">
              {mappedCount} campos mapeados
            </Badge>
            {requiredFieldsMapped ? (
              <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">
                <Check className="w-3 h-3 mr-1" />
                Campos requeridos OK
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-rose-100 text-rose-700">
                <X className="w-3 h-3 mr-1" />
                Faltan campos requeridos
              </Badge>
            )}
            {eanMapped ? (
              <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">
                <Check className="w-3 h-3 mr-1" />
                EAN mapeado
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-rose-100 text-rose-700">
                <AlertCircle className="w-3 h-3 mr-1" />
                EAN sin mapear
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleClearAll} className="text-slate-600">
              Limpiar todo
            </Button>
            <Button variant="outline" size="sm" onClick={handleAutoDetect} className="text-indigo-600">
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Auto-detectar
            </Button>
          </div>
        </div>

        {/* Mapping Grid */}
        <div className="flex-1 overflow-y-auto pr-2">
          {detectedColumns.length === 0 ? (
            <div className="text-center py-8">
              <FileSpreadsheet className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">
                No se han detectado columnas. Sincroniza primero el archivo del proveedor.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {SYSTEM_FIELDS.map(field => (
                <div 
                  key={field.key} 
                  className={`flex items-center gap-4 p-3 rounded-lg border ${
                    mapping[field.key] 
                      ? 'bg-emerald-50 border-emerald-200' 
                      : field.required 
                        ? 'bg-rose-50 border-rose-200' 
                        : field.critical
                          ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-200'
                          : 'bg-slate-50 border-slate-200'
                  }`}
                  data-testid={`mapping-row-${field.key}`}
                >
                  {/* System Field */}
                  <div className="w-1/3 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-sm text-slate-900">
                        {field.label}
                        {field.required && <span className="text-rose-500 ml-0.5">*</span>}
                        {field.critical && !field.required && <span className="text-amber-500 ml-0.5">⚠</span>}
                      </span>
                    </div>
                    <p className={`text-xs truncate ${field.critical && !mapping[field.key] ? 'text-amber-700 font-medium' : 'text-slate-500'}`}>
                      {field.description}
                    </p>
                  </div>

                  {/* Arrow */}
                  <ArrowRight className={`w-4 h-4 shrink-0 ${mapping[field.key] ? 'text-emerald-500' : 'text-slate-300'}`} />

                  {/* Supplier Column Selector */}
                  <div className="flex-1">
                    <Select
                      value={mapping[field.key] || "none"}
                      onValueChange={(value) => handleMappingChange(field.key, value)}
                    >
                      <SelectTrigger 
                        className={`w-full ${mapping[field.key] ? 'border-emerald-300 bg-white' : ''}`}
                        data-testid={`mapping-${field.key}`}
                      >
                        <SelectValue placeholder="Seleccionar columna del proveedor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">
                          <span className="text-slate-400">-- Sin mapear --</span>
                        </SelectItem>
                        {detectedColumns.filter(Boolean).map(col => (
                          <SelectItem key={col} value={col}>
                            <span className="font-mono text-sm">{col}</span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Status Icon */}
                  <div className="w-6 shrink-0">
                    {mapping[field.key] && (
                      <Check className="w-5 h-5 text-emerald-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter className="shrink-0 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="btn-secondary">
            Cancelar
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving || !requiredFieldsMapped}
            className="btn-primary"
            data-testid="save-mapping-btn"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Guardando...
              </>
            ) : (
              'Guardar Mapeo'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ColumnMappingDialog;
