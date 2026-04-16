import { Bell, Plus, Pencil, Trash2, MoreHorizontal } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../ui/dropdown-menu";

const ALERT_TYPES = [
  { value: "price_drop", label: "Bajada de precio (%)" },
  { value: "price_below", label: "Precio por debajo de..." },
  { value: "competitor_cheaper", label: "Competidor más barato" },
  { value: "any_change", label: "Cualquier cambio" },
];

const ALERT_CHANNELS = [
  { value: "app", label: "Notificación en la app" },
  { value: "email", label: "Email" },
  { value: "webhook", label: "Webhook" },
];

export function AlertsTab({ alerts, onAdd, onEdit, onDelete }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={onAdd}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva Alerta
        </Button>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No hay alertas configuradas</p>
          <p className="text-sm">Crea alertas para recibir notificaciones de cambios de precio</p>
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Umbral</TableHead>
                <TableHead>Canal</TableHead>
                <TableHead>Disparos</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="w-[70px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell>
                    <span className="font-mono text-sm">{alert.sku || alert.ean || "—"}</span>
                  </TableCell>
                  <TableCell>
                    {ALERT_TYPES.find((t) => t.value === alert.alert_type)?.label || alert.alert_type}
                  </TableCell>
                  <TableCell>
                    {alert.threshold != null ? (
                      alert.alert_type === "price_below" ? `${alert.threshold}€` : `${alert.threshold}%`
                    ) : "—"}
                  </TableCell>
                  <TableCell>
                    {ALERT_CHANNELS.find((c) => c.value === alert.channel)?.label || alert.channel}
                  </TableCell>
                  <TableCell>{alert.trigger_count}</TableCell>
                  <TableCell>
                    <Badge variant={alert.active ? "default" : "secondary"}>
                      {alert.active ? "Activa" : "Inactiva"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onEdit(alert)}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive" onClick={() => onDelete(alert)}>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
