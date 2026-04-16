import { Columns, Zap } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";

export function ColumnMappingAlert({ supplier, syncing, onApplyPreset, onConfigureMapping }) {
  if (!supplier?.detected_columns?.length) return null;

  return (
    <Card className="border-amber-200 bg-amber-50 mb-6">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Columns className="w-5 h-5 text-amber-600 mt-0.5" strokeWidth={1.5} />
          <div className="flex-1">
            <p className="font-medium text-amber-900 mb-1">Configuración de mapeo necesaria</p>
            {supplier?.preset_id ? (
              <p className="text-sm text-amber-700 mb-3">
                El proveedor tiene una plantilla asignada (<span className="font-semibold">{supplier.preset_id}</span>) pero
                fue creado con una versión anterior. Haz clic en <span className="font-semibold">Re-aplicar plantilla</span> para
                actualizar la configuración de columnas y sincronizar automáticamente.
              </p>
            ) : (
              <p className="text-sm text-amber-700 mb-3">
                Se descargó el archivo pero no se importaron productos. Las columnas del archivo no coinciden
                con los campos del sistema. Configura el mapeo de columnas para asignar correctamente los campos.
              </p>
            )}
            <div className="mb-3">
              <p className="text-xs text-amber-600 mb-1">Columnas detectadas:</p>
              <div className="flex flex-wrap gap-1">
                {supplier.detected_columns.slice(0, 8).map((col, i) => (
                  <span key={i} className="px-2 py-0.5 bg-white rounded text-xs font-mono text-amber-800 border border-amber-200">
                    {col}
                  </span>
                ))}
                {supplier.detected_columns.length > 8 && (
                  <span className="px-2 py-0.5 text-xs text-amber-600">
                    +{supplier.detected_columns.length - 8} más
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {supplier?.preset_id && (
                <Button
                  size="sm"
                  onClick={onApplyPreset}
                  disabled={syncing}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  <Zap className="w-3.5 h-3.5 mr-1.5" />
                  Re-aplicar plantilla y sincronizar
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={onConfigureMapping}
                className="border-amber-300 text-amber-700 hover:bg-amber-100"
              >
                <Columns className="w-3.5 h-3.5 mr-1.5" />
                Configurar Mapeo manual
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
