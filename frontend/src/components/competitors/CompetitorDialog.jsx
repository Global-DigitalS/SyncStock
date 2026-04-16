import { Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../ui/dialog";

const CHANNELS = [
  { value: "amazon_es", label: "Amazon España" },
  { value: "pccomponentes", label: "PCComponentes" },
  { value: "mediamarkt", label: "MediaMarkt" },
  { value: "fnac", label: "Fnac" },
  { value: "el_corte_ingles", label: "El Corte Inglés" },
  { value: "worten", label: "Worten" },
  { value: "coolmod", label: "Coolmod" },
  { value: "ldlc", label: "LDLC" },
  { value: "alternate", label: "Alternate" },
  { value: "web_directa", label: "Web Directa" },
  { value: "otro", label: "Otro" },
];

export function CompetitorDialog({ open, onOpenChange, isEdit, form, onChange, onSave, saving }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Competidor" : "Nuevo Competidor"}</DialogTitle>
          <DialogDescription>Configura un competidor para monitorizar sus precios</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Nombre *</Label>
            <Input
              placeholder="Ej: Amazon España"
              value={form.name}
              onChange={(e) => onChange({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <Label>URL base *</Label>
            <Input
              placeholder="https://www.ejemplo.com"
              value={form.base_url}
              onChange={(e) => onChange({ ...form, base_url: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Canal</Label>
              <Select value={form.channel} onValueChange={(val) => onChange({ ...form, channel: val })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CHANNELS.map((ch) => (
                    <SelectItem key={ch.value} value={ch.value}>{ch.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>País</Label>
              <Input
                placeholder="ES"
                value={form.country}
                maxLength={2}
                onChange={(e) => onChange({ ...form, country: e.target.value.toUpperCase() })}
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
