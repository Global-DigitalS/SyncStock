import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { api } from "../App";
import {
  RefreshCw,
  Clock,
  Truck,
  Store,
  Building2,
  AlertCircle,
  CheckCircle,
  Settings,
  Play,
  Loader2
} from "lucide-react";

const SYNC_INTERVAL_OPTIONS = [
  { value: 1, label: "Cada hora", description: "Sincronización más frecuente" },
  { value: 6, label: "Cada 6 horas", description: "4 veces al día" },
  { value: 12, label: "Cada 12 horas", description: "2 veces al día" },
  { value: 24, label: "Cada 24 horas", description: "1 vez al día" }
];

const SyncSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState(null);
  
  // Form state
  const [syncInterval, setSyncInterval] = useState(null);
  const [syncSuppliers, setSyncSuppliers] = useState(true);
  const [syncStores, setSyncStores] = useState(true);
  const [syncCrm, setSyncCrm] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await api.get("/sync/settings");
      setSettings(res.data);
      setSyncInterval(res.data.current_interval);
      setSyncSuppliers(res.data.sync_suppliers ?? true);
      setSyncStores(res.data.sync_stores ?? true);
      setSyncCrm(res.data.sync_crm ?? true);
    } catch (error) {
      toast.error("Error al cargar configuración");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/sync/settings", {
        interval: syncInterval,
        sync_suppliers: syncSuppliers,
        sync_stores: syncStores,
        sync_crm: syncCrm
      });
      toast.success("Configuración guardada");
      fetchSettings();
    } catch (error) {
      toast.error(error.response?.data?.message || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleSyncNow = async () => {
    setSyncing(true);
    setLastSyncResult(null);
    try {
      const res = await api.post("/sync/run-now");
      setLastSyncResult(res.data);
      toast.success(res.data.message);
      fetchSettings();
    } catch (error) {
      toast.error("Error al sincronizar");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const hasChanges = 
    syncInterval !== settings?.current_interval ||
    syncSuppliers !== (settings?.sync_suppliers ?? true) ||
    syncStores !== (settings?.sync_stores ?? true) ||
    syncCrm !== (settings?.sync_crm ?? true);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <RefreshCw className="w-6 h-6 text-blue-600" />
            Sincronización Automática
          </h2>
          <p className="text-slate-600 mt-1">
            Configura la sincronización automática de proveedores, tiendas y CRM
          </p>
        </div>
        <Button 
          onClick={handleSyncNow} 
          disabled={syncing}
          className="gap-2"
          data-testid="sync-now-btn"
        >
          {syncing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Sincronizar Ahora
        </Button>
      </div>

      {/* Plan Status */}
      {!settings?.enabled && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-start gap-3 pt-6">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-800">Sincronización automática no disponible</h4>
              <p className="text-sm text-amber-700 mt-1">
                Tu plan actual no incluye sincronización automática. Actualiza tu suscripción para acceder a esta funcionalidad.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Configuración
          </CardTitle>
          <CardDescription>
            Selecciona el intervalo y qué servicios sincronizar
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Interval Selection */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2 text-base font-medium">
              <Clock className="w-4 h-4 text-blue-600" />
              Frecuencia de sincronización
            </Label>
            
            {settings?.enabled ? (
              <Select 
                value={syncInterval ? String(syncInterval) : "disabled"} 
                onValueChange={(v) => setSyncInterval(v === "disabled" ? null : Number(v))}
              >
                <SelectTrigger className="w-full max-w-xs" data-testid="sync-interval-select">
                  <SelectValue placeholder="Selecciona un intervalo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="disabled">Desactivado</SelectItem>
                  {SYNC_INTERVAL_OPTIONS.filter(opt => settings.intervals.includes(opt.value)).map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-slate-500">Actualiza tu plan para acceder a esta función</p>
            )}
            
            {settings?.intervals?.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="text-sm text-slate-500">Intervalos disponibles:</span>
                {SYNC_INTERVAL_OPTIONS.filter(opt => settings.intervals.includes(opt.value)).map((opt) => (
                  <Badge key={opt.value} variant="secondary" className="text-xs">
                    {opt.label}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Services Selection */}
          <div className="space-y-4 pt-4 border-t">
            <Label className="text-base font-medium">Servicios a sincronizar</Label>
            
            <div className="space-y-3">
              {/* Suppliers */}
              <div className="flex items-center justify-between p-3 rounded-lg border bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                    <Truck className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium">Proveedores</p>
                    <p className="text-sm text-slate-500">Catálogos de proveedores (FTP/URL)</p>
                  </div>
                </div>
                <Switch
                  checked={syncSuppliers}
                  onCheckedChange={setSyncSuppliers}
                  disabled={!settings?.enabled || !syncInterval}
                  data-testid="sync-suppliers-switch"
                />
              </div>

              {/* Stores */}
              <div className="flex items-center justify-between p-3 rounded-lg border bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                    <Store className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium">Tiendas</p>
                    <p className="text-sm text-slate-500">Tiendas online (WooCommerce, PrestaShop, Shopify...)</p>
                  </div>
                </div>
                <Switch
                  checked={syncStores}
                  onCheckedChange={setSyncStores}
                  disabled={!settings?.enabled || !syncInterval}
                  data-testid="sync-stores-switch"
                />
              </div>

              {/* CRM */}
              <div className="flex items-center justify-between p-3 rounded-lg border bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">CRM</p>
                    <p className="text-sm text-slate-500">Dolibarr y otros CRM conectados</p>
                  </div>
                </div>
                <Switch
                  checked={syncCrm}
                  onCheckedChange={setSyncCrm}
                  disabled={!settings?.enabled || !syncInterval}
                  data-testid="sync-crm-switch"
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          {settings?.enabled && (
            <div className="flex items-center justify-between pt-4 border-t">
              <div>
                {settings?.last_sync && (
                  <p className="text-sm text-slate-500">
                    Última sincronización: {new Date(settings.last_sync).toLocaleString("es-ES")}
                  </p>
                )}
                {settings?.next_sync && syncInterval && (
                  <p className="text-sm text-slate-500">
                    Próxima sincronización: {new Date(settings.next_sync).toLocaleString("es-ES")}
                  </p>
                )}
              </div>
              <Button 
                onClick={handleSave} 
                disabled={saving || !hasChanges}
                data-testid="save-sync-settings-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Guardar Configuración
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Last Sync Result */}
      {lastSyncResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              Resultado de Sincronización
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {lastSyncResult.details?.suppliers && (
                <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Truck className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-green-800">Proveedores</span>
                  </div>
                  <p className="text-2xl font-bold text-green-700">
                    {lastSyncResult.details.suppliers.synced}/{lastSyncResult.details.suppliers.total}
                  </p>
                  <p className="text-sm text-green-600">sincronizados</p>
                </div>
              )}
              {lastSyncResult.details?.stores && (
                <div className="p-4 rounded-lg bg-purple-50 border border-purple-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Store className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-purple-800">Tiendas</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-700">
                    {lastSyncResult.details.stores.synced}/{lastSyncResult.details.stores.total}
                  </p>
                  <p className="text-sm text-purple-600">sincronizadas</p>
                </div>
              )}
              {lastSyncResult.details?.crm && (
                <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-800">CRM</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-700">
                    {lastSyncResult.details.crm.synced}/{lastSyncResult.details.crm.total}
                  </p>
                  <p className="text-sm text-blue-600">sincronizados</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SyncSettings;
