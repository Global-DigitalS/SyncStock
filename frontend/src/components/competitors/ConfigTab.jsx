import { Loader2, CheckCircle2 } from "lucide-react";
import { Badge } from "../ui/badge";

export function ConfigTab({
  monitoringCatalog,
  availableCatalogs,
  configLoading,
  savingConfig,
  onSelect,
}) {
  return (
    <div className="space-y-6">
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-900 dark:text-blue-300">
          <strong>Catálogo de Monitoreo:</strong> Este catálogo se usa para obtener los "Precios Finales" (con márgenes aplicados) que se comparan con los precios de los competidores.
        </p>
      </div>

      {configLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-6">
          {monitoringCatalog && monitoringCatalog.catalog_id && (
            <div className="border rounded-lg p-6 space-y-4">
              <h3 className="font-semibold">Catálogo Actual</h3>
              <div className="flex items-center justify-between p-4 bg-muted rounded">
                <div>
                  <p className="font-medium">{monitoringCatalog.catalog_name}</p>
                  {monitoringCatalog.is_default && (
                    <Badge variant="secondary" className="mt-2">Predeterminado</Badge>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="border rounded-lg p-6 space-y-4">
            <h3 className="font-semibold">Seleccionar Catálogo</h3>
            {availableCatalogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No hay catálogos disponibles</p>
                <p className="text-sm mt-2">Crea un catálogo primero para poder usarlo en el monitoreo de precios.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {availableCatalogs.map((catalog) => (
                  <button
                    key={catalog.catalog_id}
                    onClick={() => onSelect(catalog.catalog_id)}
                    disabled={savingConfig || catalog.is_selected}
                    className={`w-full text-left p-4 border rounded-lg transition-colors ${
                      catalog.is_selected
                        ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                        : "hover:bg-muted cursor-pointer"
                    } ${savingConfig ? "opacity-50" : ""}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{catalog.catalog_name}</p>
                        {catalog.is_default && (
                          <Badge variant="secondary" className="mt-2">Predeterminado</Badge>
                        )}
                      </div>
                      {catalog.is_selected && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p className="text-sm text-amber-900 dark:text-amber-300">
              <strong>Nota:</strong> El cambio de catálogo afectará a los próximos monitoreos de precios. Los precios históricos seguirán siendo válidos.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
