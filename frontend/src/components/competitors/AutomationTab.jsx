import {
  Plus, Loader2, FlaskConical, Rocket, Zap, Pencil, Trash2, MoreHorizontal,
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../ui/dropdown-menu";

const AUTOMATION_STRATEGIES = [
  { value: "match_cheapest", label: "Igualar al más barato" },
  { value: "undercut_by_amount", label: "Rebajar importe fijo" },
  { value: "undercut_by_percent", label: "Rebajar porcentaje" },
  { value: "margin_above_cost", label: "Margen sobre coste" },
  { value: "price_cap", label: "Techo de precio" },
];

const APPLY_TO_OPTIONS = [
  { value: "all", label: "Todos los productos" },
  { value: "category", label: "Categoría" },
  { value: "supplier", label: "Proveedor" },
  { value: "product", label: "Producto específico" },
];

export function AutomationTab({
  automationRules,
  automationLoading,
  simulation,
  simulating,
  applying,
  onAdd,
  onEdit,
  onDelete,
  onSimulate,
  onApply,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button onClick={onAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Nueva Regla
          </Button>
          <Button
            variant="outline"
            onClick={() => onSimulate()}
            disabled={simulating || automationRules.length === 0}
          >
            {simulating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FlaskConical className="h-4 w-4 mr-2" />}
            Simular
          </Button>
          <Button
            onClick={() => {
              if (window.confirm("¿Aplicar todas las reglas activas? Los precios se actualizarán.")) {
                onApply();
              }
            }}
            disabled={applying || automationRules.length === 0}
          >
            {applying ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Rocket className="h-4 w-4 mr-2" />}
            Aplicar
          </Button>
        </div>
      </div>

      {simulation && (
        <div className="border rounded-lg p-4 bg-amber-50 dark:bg-amber-950 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <FlaskConical className="h-4 w-4" />
              Resultado de la simulación
            </h3>
            <Badge variant="outline">
              {simulation.total_changes} cambios · {simulation.rules_evaluated} reglas
            </Badge>
          </div>
          {simulation.changes?.length > 0 ? (
            <div className="border rounded-lg bg-background">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead>Precio actual</TableHead>
                    <TableHead>Nuevo precio</TableHead>
                    <TableHead>Cambio</TableHead>
                    <TableHead>Regla</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {simulation.changes.slice(0, 50).map((ch, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <span className="text-sm">{ch.product_name}</span>
                        <p className="text-xs text-muted-foreground font-mono">{ch.sku || ch.ean}</p>
                      </TableCell>
                      <TableCell>{ch.current_price?.toFixed(2)}€</TableCell>
                      <TableCell className="font-medium">{ch.new_price?.toFixed(2)}€</TableCell>
                      <TableCell>
                        <span className={ch.change_amount < 0 ? "text-green-600" : "text-red-600"}>
                          {ch.change_amount > 0 ? "+" : ""}{ch.change_amount?.toFixed(2)}€
                          <span className="text-xs ml-1">({ch.change_percent > 0 ? "+" : ""}{ch.change_percent?.toFixed(1)}%)</span>
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">{ch.rule_name}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No hay cambios que aplicar con las reglas actuales</p>
          )}
        </div>
      )}

      {automationLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : automationRules.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No hay reglas de automatización</p>
          <p className="text-sm">Crea reglas para ajustar precios automáticamente según la competencia</p>
          <Button className="mt-4" onClick={onAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Nueva Regla
          </Button>
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Estrategia</TableHead>
                <TableHead>Valor</TableHead>
                <TableHead>Aplica a</TableHead>
                <TableHead>Prioridad</TableHead>
                <TableHead>Último uso</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="w-[70px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {automationRules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell className="font-medium">{rule.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {AUTOMATION_STRATEGIES.find((s) => s.value === rule.strategy)?.label || rule.strategy}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {rule.strategy === "price_cap" || rule.strategy === "undercut_by_amount"
                      ? `${rule.value}€`
                      : `${rule.value}%`}
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">
                      {APPLY_TO_OPTIONS.find((a) => a.value === rule.apply_to)?.label || rule.apply_to}
                      {rule.apply_to_value && (
                        <span className="text-xs text-muted-foreground ml-1">({rule.apply_to_value})</span>
                      )}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">{rule.priority}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {rule.last_applied_at ? new Date(rule.last_applied_at).toLocaleString("es-ES") : "Nunca"}
                    {rule.products_affected > 0 && (
                      <p className="text-xs">{rule.products_affected} productos</p>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={rule.active ? "default" : "secondary"}>
                      {rule.active ? "Activa" : "Inactiva"}
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
                        <DropdownMenuItem onClick={() => onSimulate(rule.id)}>
                          <FlaskConical className="h-4 w-4 mr-2" />
                          Simular esta regla
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onEdit(rule)}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive" onClick={() => onDelete(rule)}>
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
