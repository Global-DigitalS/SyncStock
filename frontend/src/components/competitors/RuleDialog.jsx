import { Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../ui/dialog";

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

export function RuleDialog({ open, onOpenChange, isEdit, form, onChange, onSave, saving }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Regla" : "Nueva Regla de Automatización"}</DialogTitle>
          <DialogDescription>Define cómo se ajustarán los precios automáticamente</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Nombre *</Label>
            <Input
              placeholder="Ej: Igualar Amazon en electrónica"
              value={form.name}
              onChange={(e) => onChange({ ...form, name: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Estrategia *</Label>
              <Select value={form.strategy} onValueChange={(val) => onChange({ ...form, strategy: val })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {AUTOMATION_STRATEGIES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>
                Valor * {form.strategy === "undercut_by_amount" || form.strategy === "price_cap" ? "(€)" : "(%)"}
              </Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder={form.strategy === "match_cheapest" ? "0" : "5"}
                value={form.value}
                onChange={(e) => onChange({ ...form, value: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Aplica a</Label>
              <Select value={form.apply_to} onValueChange={(val) => onChange({ ...form, apply_to: val })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {APPLY_TO_OPTIONS.map((a) => (
                    <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {form.apply_to !== "all" && (
              <div>
                <Label>Valor del filtro</Label>
                <Input
                  placeholder={form.apply_to === "category" ? "Electrónica" : "ID..."}
                  value={form.apply_to_value}
                  onChange={(e) => onChange({ ...form, apply_to_value: e.target.value })}
                />
              </div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Precio mín (€)</Label>
              <Input
                type="number" min="0" step="0.01" placeholder="0"
                value={form.min_price}
                onChange={(e) => onChange({ ...form, min_price: e.target.value })}
              />
            </div>
            <div>
              <Label>Precio máx (€)</Label>
              <Input
                type="number" min="0" step="0.01" placeholder="Sin límite"
                value={form.max_price}
                onChange={(e) => onChange({ ...form, max_price: e.target.value })}
              />
            </div>
            <div>
              <Label>Prioridad</Label>
              <Input
                type="number" min="0" placeholder="0"
                value={form.priority}
                onChange={(e) => onChange({ ...form, priority: e.target.value })}
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={onSave} disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isEdit ? "Guardar" : "Crear"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
