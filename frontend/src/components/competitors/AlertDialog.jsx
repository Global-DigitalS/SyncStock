import { Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../ui/dialog";

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

export function AlertDialog({ open, onOpenChange, isEdit, form, onChange, onSave, saving }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Alerta" : "Nueva Alerta de Precio"}</DialogTitle>
          <DialogDescription>Configura cuándo quieres recibir notificaciones</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>SKU</Label>
              <Input
                placeholder="SKU del producto"
                value={form.sku}
                onChange={(e) => onChange({ ...form, sku: e.target.value })}
              />
            </div>
            <div>
              <Label>EAN</Label>
              <Input
                placeholder="EAN / código de barras"
                value={form.ean}
                onChange={(e) => onChange({ ...form, ean: e.target.value })}
              />
            </div>
          </div>
          <div>
            <Label>Tipo de alerta</Label>
            <Select value={form.alert_type} onValueChange={(val) => onChange({ ...form, alert_type: val })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ALERT_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {(form.alert_type === "price_drop" || form.alert_type === "price_below") && (
            <div>
              <Label>
                {form.alert_type === "price_below" ? "Precio umbral (€)" : "Porcentaje de bajada (%)"}
              </Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder={form.alert_type === "price_below" ? "99.99" : "10"}
                value={form.threshold}
                onChange={(e) => onChange({ ...form, threshold: e.target.value })}
              />
            </div>
          )}
          <div>
            <Label>Canal de notificación</Label>
            <Select value={form.channel} onValueChange={(val) => onChange({ ...form, channel: val })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ALERT_CHANNELS.map((c) => (
                  <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {form.channel === "webhook" && (
            <div>
              <Label>URL del Webhook</Label>
              <Input
                placeholder="https://tu-servidor.com/webhook"
                value={form.webhook_url}
                onChange={(e) => onChange({ ...form, webhook_url: e.target.value })}
              />
            </div>
          )}
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
