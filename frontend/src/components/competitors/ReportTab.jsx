import { BarChart3, Loader2, Search, Download, ArrowDown, ArrowUp, Equal } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

export function ReportTab({
  report,
  reportLoading,
  reportCategory,
  reportSupplier,
  onCategoryChange,
  onSupplierChange,
  onFetch,
  onExport,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Input
            placeholder="Filtrar por categoría..."
            value={reportCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-48"
          />
          <Input
            placeholder="ID de proveedor..."
            value={reportSupplier}
            onChange={(e) => onSupplierChange(e.target.value)}
            className="w-48"
          />
          <Button variant="outline" onClick={onFetch} disabled={reportLoading}>
            {reportLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={onExport} disabled={!report}>
          <Download className="h-4 w-4 mr-2" />
          Exportar Informe
        </Button>
      </div>

      {reportLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !report ? (
        <div className="text-center py-12 text-muted-foreground">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">Informe de posicionamiento competitivo</p>
          <p className="text-sm">Pulsa el botón de búsqueda para generar el informe</p>
          <Button className="mt-4" onClick={onFetch}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Generar Informe
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">{report.summary?.total || 0}</p>
              <p className="text-xs text-muted-foreground">Analizados</p>
            </div>
            <div className="border rounded-lg p-4 text-center bg-green-50 dark:bg-green-950">
              <p className="text-2xl font-bold text-green-600">{report.summary?.cheaper || 0}</p>
              <p className="text-xs text-green-600">Más baratos</p>
            </div>
            <div className="border rounded-lg p-4 text-center bg-blue-50 dark:bg-blue-950">
              <p className="text-2xl font-bold text-blue-600">{report.summary?.equal || 0}</p>
              <p className="text-xs text-blue-600">Igual precio</p>
            </div>
            <div className="border rounded-lg p-4 text-center bg-red-50 dark:bg-red-950">
              <p className="text-2xl font-bold text-red-600">{report.summary?.expensive || 0}</p>
              <p className="text-xs text-red-600">Más caros</p>
            </div>
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-muted-foreground">{report.summary?.no_data || 0}</p>
              <p className="text-xs text-muted-foreground">Sin datos</p>
            </div>
          </div>

          {report.items?.length > 0 ? (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead>Mi precio</TableHead>
                    <TableHead>Mejor competidor</TableHead>
                    <TableHead>Posición</TableHead>
                    <TableHead>Diferencia</TableHead>
                    <TableHead>Comp.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.items.slice(0, 100).map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <div>
                          <span className="font-medium text-sm">{item.product_name}</span>
                          <p className="text-xs text-muted-foreground font-mono">{item.sku || item.ean}</p>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{item.my_price?.toFixed(2)}€</TableCell>
                      <TableCell>
                        <div>
                          <span className="font-medium">{item.best_competitor_price?.toFixed(2)}€</span>
                          <p className="text-xs text-muted-foreground">{item.best_competitor_name}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        {item.position === "cheaper" && (
                          <Badge className="bg-green-100 text-green-700 gap-1">
                            <ArrowDown className="h-3 w-3" />Más barato
                          </Badge>
                        )}
                        {item.position === "equal" && (
                          <Badge variant="secondary" className="gap-1">
                            <Equal className="h-3 w-3" />Igual
                          </Badge>
                        )}
                        {item.position === "expensive" && (
                          <Badge variant="destructive" className="gap-1">
                            <ArrowUp className="h-3 w-3" />Más caro
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.price_difference != null && (
                          <span className={item.price_difference > 0 ? "text-red-600" : "text-green-600"}>
                            {item.price_difference > 0 ? "+" : ""}{item.price_difference?.toFixed(2)}€
                            <span className="text-xs ml-1">
                              ({item.price_difference_percent > 0 ? "+" : ""}{item.price_difference_percent?.toFixed(1)}%)
                            </span>
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">{item.competitors_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-center py-8 text-muted-foreground">
              No hay datos de posicionamiento disponibles
            </p>
          )}
        </>
      )}
    </div>
  );
}
