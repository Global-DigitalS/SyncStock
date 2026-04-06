import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  FileSpreadsheet, RefreshCw, Check, AlertTriangle, ArrowRight, Save, Eye, Wand2
} from "lucide-react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";

const FIELD_LABELS = {
  sku: { label: "SKU / Código", required: true },
  name: { label: "Nombre", required: true },
  price: { label: "Precio", required: true },
  stock: { label: "Stock", required: false },
  category: { label: "Categoría", required: false },
  brand: { label: "Marca", required: false },
  ean: { label: "EAN / Código de barras", required: false },
  weight: { label: "Peso", required: false },
  image_url: { label: "URL de imagen", required: false },
  description: { label: "Descripción", required: false }
};

const ColumnMappingWizard = ({ open, onOpenChange, supplier, onSave }) => {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && supplier) {
      loadPreview();
    }
  }, [open, supplier]);

  const loadPreview = async () => {
    if (!supplier?.id) return;
    setLoading(true);
    try {
      const res = await api.post(`/suppliers/${supplier.id}/preview-file`);
      setPreview(res.data);
      // Apply suggested mapping
      if (res.data.suggested_mapping) {
        setMapping(res.data.suggested_mapping);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cargar vista previa");
    } finally {
      setLoading(false);
    }
  };

  const updateMapping = (field, column) => {
    setMapping(prev => {
      const newMapping = { ...prev };
      if (column === "none") {
        delete newMapping[field];
      } else {
        newMapping[field] = column;
      }
      return newMapping;
    });
  };

  const handleSave = async () => {
    // Validate required fields
    const missingRequired = Object.entries(FIELD_LABELS)
      .filter(([field, config]) => config.required && !mapping[field])
      .map(([field]) => FIELD_LABELS[field].label);
    
    if (missingRequired.length > 0) {
      toast.error(`Faltan campos obligatorios: ${missingRequired.join(", ")}`);
      return;
    }

    setSaving(true);
    try {
      await api.put(`/suppliers/${supplier.id}`, {
        column_mapping: mapping
      });
      toast.success("Mapeo de columnas guardado correctamente");
      onSave?.();
      onOpenChange(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar mapeo");
    } finally {
      setSaving(false);
    }
  };

  const getMappingStatus = () => {
    const required = Object.entries(FIELD_LABELS).filter(([, c]) => c.required);
    const mappedRequired = required.filter(([f]) => mapping[f]);
    const optional = Object.entries(FIELD_LABELS).filter(([, c]) => !c.required);
    const mappedOptional = optional.filter(([f]) => mapping[f]);
    
    return {
      requiredMapped: mappedRequired.length,
      requiredTotal: required.length,
      optionalMapped: mappedOptional.length,
      optionalTotal: optional.length,
      isComplete: mappedRequired.length === required.length
    };
  };

  const status = getMappingStatus();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <Wand2 className="w-5 h-5 text-indigo-600" />
            Asistente de Mapeo de Columnas
          </DialogTitle>
          <DialogDescription>
            Configura qué columna del archivo corresponde a cada campo del sistema para {supplier?.name}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
          </div>
        ) : preview ? (
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Status Bar */}
            <div className="px-6 py-3 bg-slate-50 border-b flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Badge className={status.isComplete ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}>
                  {status.isComplete ? <Check className="w-3 h-3 mr-1" /> : <AlertTriangle className="w-3 h-3 mr-1" />}
                  {status.requiredMapped}/{status.requiredTotal} obligatorios
                </Badge>
                <Badge className="bg-slate-100 text-slate-600">
                  {status.optionalMapped}/{status.optionalTotal} opcionales
                </Badge>
                <span className="text-sm text-slate-500">
                  {preview.total_rows.toLocaleString()} filas detectadas
                </span>
              </div>
              <Button variant="outline" size="sm" onClick={loadPreview}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Recargar
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Field Mapping */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {Object.entries(FIELD_LABELS).map(([field, config]) => (
                  <div key={field} className="space-y-1">
                    <Label className={`text-sm ${config.required ? "font-semibold" : ""}`}>
                      {config.label}
                      {config.required && <span className="text-rose-500 ml-1">*</span>}
                    </Label>
                    <Select
                      value={mapping[field] || "none"}
                      onValueChange={(v) => updateMapping(field, v)}
                    >
                      <SelectTrigger className={`input-base ${mapping[field] ? "border-emerald-300 bg-emerald-50" : config.required ? "border-rose-200" : ""}`}>
                        <SelectValue placeholder="Sin asignar" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">— Sin asignar —</SelectItem>
                        {preview.columns.filter(Boolean).map((col) => (
                          <SelectItem key={col} value={col}>
                            {col}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ))}
              </div>

              {/* Preview Table */}
              <Card className="border-slate-200">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    Vista previa de datos (primeras 5 filas)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50">
                        {preview.columns.slice(0, 8).map((col) => {
                          const mappedTo = Object.entries(mapping).find(([, v]) => v === col)?.[0];
                          return (
                            <TableHead key={col} className="text-xs">
                              <div className="flex flex-col gap-1">
                                <span className="truncate max-w-[120px]" title={col}>{col}</span>
                                {mappedTo && (
                                  <Badge className="bg-indigo-100 text-indigo-700 text-[10px] w-fit">
                                    → {FIELD_LABELS[mappedTo]?.label}
                                  </Badge>
                                )}
                              </div>
                            </TableHead>
                          );
                        })}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.sample_data.map((row, idx) => (
                        <TableRow key={idx}>
                          {preview.columns.slice(0, 8).map((col) => (
                            <TableCell key={col} className="text-xs py-2">
                              <span className="truncate block max-w-[120px]" title={row[col]}>
                                {row[col] || "-"}
                              </span>
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {preview.columns.length > 8 && (
                    <div className="px-4 py-2 text-xs text-slate-500 bg-slate-50 border-t">
                      +{preview.columns.length - 8} columnas más no mostradas
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-20 text-slate-500">
            <FileSpreadsheet className="w-10 h-10 mr-3 opacity-50" />
            <p>No se pudo cargar la vista previa</p>
          </div>
        )}

        <DialogFooter className="px-6 py-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !status.isComplete}
            className="btn-primary"
            data-testid="save-mapping-btn"
          >
            {saving ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Guardar Mapeo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ColumnMappingWizard;
