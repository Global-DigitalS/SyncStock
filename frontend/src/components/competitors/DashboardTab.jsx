import {
  BarChart3, Loader2, Search, Bell, TrendingUp, TrendingDown, Equal, ArrowUp, ArrowDown,
} from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

export function DashboardTab({
  dashboardOverview,
  dashboardTable,
  dashboardLoading,
  dashboardSearch,
  dashboardPage,
  dashboardTotal,
  enrichedAlerts,
  onSearchChange,
  onPageChange,
}) {
  const totalPages = Math.ceil(dashboardTotal / 20);

  return (
    <div className="space-y-6">
      {dashboardOverview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="border rounded-lg p-4 space-y-2">
            <p className="text-sm text-muted-foreground">Competidores Activos</p>
            <p className="text-3xl font-bold">{dashboardOverview.active_competitors || 0}</p>
          </div>
          <div className="border rounded-lg p-4 space-y-2">
            <p className="text-sm text-muted-foreground">Alertas Activas</p>
            <p className="text-3xl font-bold text-amber-600">{dashboardOverview.active_alerts || 0}</p>
          </div>
          <div className="border rounded-lg p-4 space-y-2">
            <p className="text-sm text-muted-foreground">SKUs Monitorizados</p>
            <p className="text-3xl font-bold">{dashboardOverview.monitored_skus || 0}</p>
          </div>
          <div className="border rounded-lg p-4 space-y-2">
            <p className="text-sm text-muted-foreground">Snapshots (7d)</p>
            <p className="text-3xl font-bold">{dashboardOverview.snapshots_last_7d || 0}</p>
          </div>
          <div className="border rounded-lg p-4 space-y-2">
            <p className="text-sm text-muted-foreground">Más Baratos (24h)</p>
            <p className="text-3xl font-bold text-red-600">{dashboardOverview.competitors_cheaper_24h || 0}</p>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Comparativa de Precios</h3>
          <Input
            placeholder="Buscar por SKU o nombre..."
            value={dashboardSearch}
            onChange={(e) => onSearchChange(e.target.value)}
            className="max-w-xs"
          />
        </div>

        {dashboardLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : dashboardTable.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">No hay datos de precios disponibles</p>
            <p className="text-sm">Ejecuta un scraping para cargar datos de competidores</p>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU / Nombre</TableHead>
                  <TableHead>EAN</TableHead>
                  <TableHead className="text-right">Mi Precio</TableHead>
                  <TableHead className="text-right">Mejor Competencia</TableHead>
                  <TableHead className="text-center">Brecha (€)</TableHead>
                  <TableHead className="text-center">Brecha (%)</TableHead>
                  <TableHead className="text-center">Margen %</TableHead>
                  <TableHead className="text-center">Cambio 24h</TableHead>
                  <TableHead className="text-center">Competidores</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboardTable.map((item) => (
                  <TableRow key={item.sku}>
                    <TableCell>
                      <div>
                        <span className="font-medium">{item.sku}</span>
                        <p className="text-xs text-muted-foreground truncate max-w-[250px]">{item.name}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{item.ean || "-"}</TableCell>
                    <TableCell className="text-right font-medium">€{item.my_price?.toFixed(2) || "-"}</TableCell>
                    <TableCell className="text-right font-medium text-red-600">
                      €{item.best_competitor_price?.toFixed(2) || "-"}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={item.gap_eur > 0 ? "default" : item.gap_eur < 0 ? "destructive" : "secondary"}>
                        {item.gap_eur > 0 ? "+" : ""}€{item.gap_eur?.toFixed(2) || "0"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {item.gap_percent > 0 ? (
                        <div className="flex items-center justify-center gap-1 text-green-600">
                          <ArrowUp className="h-3 w-3" />{item.gap_percent.toFixed(1)}%
                        </div>
                      ) : item.gap_percent < 0 ? (
                        <div className="flex items-center justify-center gap-1 text-red-600">
                          <ArrowDown className="h-3 w-3" />{Math.abs(item.gap_percent).toFixed(1)}%
                        </div>
                      ) : (
                        <Equal className="h-4 w-4 mx-auto text-muted-foreground" />
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline">{item.margin_percent?.toFixed(1)}%</Badge>
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {item.price_change_24h_percent > 0 ? (
                        <div className="flex items-center justify-center gap-1 text-green-600">
                          <TrendingUp className="h-3 w-3" />+{item.price_change_24h_percent.toFixed(1)}%
                        </div>
                      ) : item.price_change_24h_percent < 0 ? (
                        <div className="flex items-center justify-center gap-1 text-red-600">
                          <TrendingDown className="h-3 w-3" />{item.price_change_24h_percent.toFixed(1)}%
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center text-sm font-medium">
                      {item.competitors?.length || 0}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {dashboardTable.length > 0 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Mostrando {(dashboardPage - 1) * 20 + 1} a {Math.min(dashboardPage * 20, dashboardTotal)} de {dashboardTotal} productos
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => onPageChange(dashboardPage - 1)} disabled={dashboardPage === 1}>
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(dashboardPage + 1)}
                disabled={dashboardPage >= totalPages}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold">Alertas Enriquecidas Recientes</h3>
        {enrichedAlerts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground border rounded-lg">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No hay alertas recientes</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {enrichedAlerts.map((alert) => (
              <div key={alert.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold">{alert.title}</h4>
                    <p className="text-xs text-muted-foreground">
                      {alert.sku} {alert.ean && `• ${alert.ean}`}
                    </p>
                  </div>
                  <Badge
                    variant={
                      alert.context?.action === "AUTO_REPRICE"
                        ? "default"
                        : alert.context?.action === "MANUAL_REVIEW"
                        ? "secondary"
                        : "outline"
                    }
                  >
                    {alert.context?.action || "INFO"}
                  </Badge>
                </div>
                <p className="text-sm">{alert.message_short}</p>
                {alert.context && (
                  <div className="grid grid-cols-2 gap-2 text-xs border-t pt-2">
                    <div>
                      <p className="text-muted-foreground">Mi Precio</p>
                      <p className="font-semibold">€{alert.context.your_price?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Competencia</p>
                      <p className="font-semibold">€{alert.context.best_competitor_price?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Cambio</p>
                      <p className="font-semibold">
                        {alert.context.delta_percent > 0 ? "+" : ""}
                        {alert.context.delta_percent?.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Posición</p>
                      <p className="font-semibold">{alert.context.your_position || "N/A"}</p>
                    </div>
                    {alert.context.trend && (
                      <div className="col-span-2">
                        <p className="text-muted-foreground">Tendencia</p>
                        <div className="flex items-center gap-1">
                          {alert.context.trend === "UPTREND" ? (
                            <><TrendingUp className="h-3 w-3 text-red-600" /><span className="font-semibold text-red-600">Al alza</span></>
                          ) : alert.context.trend === "DOWNTREND" ? (
                            <><TrendingDown className="h-3 w-3 text-green-600" /><span className="font-semibold text-green-600">A la baja</span></>
                          ) : (
                            <><Equal className="h-3 w-3 text-muted-foreground" /><span className="font-semibold">Estable</span></>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {alert.context?.suggested_price && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                    <p className="text-xs text-muted-foreground">Precio Sugerido</p>
                    <p className="font-semibold text-blue-600">€{alert.context.suggested_price.toFixed(2)}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
