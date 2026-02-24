import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Checkbox } from "../components/ui/checkbox";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "../components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "../components/ui/alert-dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Webhook, Plus, Trash2, RefreshCw, Copy, Eye, EyeOff, 
  Activity, Store, CheckCircle, XCircle, Clock, Key, Link2,
  Bell, Package, ShoppingCart, AlertTriangle
} from "lucide-react";

const WEBHOOK_EVENTS = [
  { id: "inventory.updated", label: "Actualización de Inventario", icon: Package },
  { id: "order.created", label: "Pedido Creado", icon: ShoppingCart },
  { id: "order.completed", label: "Pedido Completado", icon: CheckCircle },
  { id: "product.updated", label: "Producto Actualizado", icon: RefreshCw },
  { id: "product.created", label: "Producto Creado", icon: Plus },
];

const WebhooksPage = () => {
  const [configs, setConfigs] = useState([]);
  const [stores, setStores] = useState([]);
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showSecretDialog, setShowSecretDialog] = useState(null);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [newSecret, setNewSecret] = useState(null);
  const [showSecret, setShowSecret] = useState(false);
  const [formData, setFormData] = useState({
    store_id: "",
    enabled: true,
    events: ["inventory.updated", "order.created"]
  });
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [configsRes, storesRes, eventsRes, statsRes] = await Promise.all([
        api.get("/webhooks/configs"),
        api.get("/stores/configs"),
        api.get("/webhooks/events?limit=20"),
        api.get("/webhooks/stats")
      ]);
      setConfigs(configsRes.data);
      setStores(storesRes.data);
      setEvents(eventsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async () => {
    if (!formData.store_id) {
      toast.error("Selecciona una tienda");
      return;
    }
    
    setSaving(true);
    try {
      const res = await api.post("/webhooks/configs", formData);
      toast.success("Webhook creado correctamente");
      setNewSecret(res.data.secret_key);
      setShowSecretDialog(res.data);
      setShowDialog(false);
      setFormData({ store_id: "", enabled: true, events: ["inventory.updated", "order.created"] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear webhook");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (config, enabled) => {
    try {
      await api.put(`/webhooks/configs/${config.id}`, { enabled });
      toast.success(enabled ? "Webhook activado" : "Webhook desactivado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar");
    }
  };

  const handleDelete = async () => {
    if (!selectedConfig) return;
    try {
      await api.delete(`/webhooks/configs/${selectedConfig.id}`);
      toast.success("Webhook eliminado");
      setShowDeleteDialog(false);
      setSelectedConfig(null);
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleRegenerateSecret = async (config) => {
    try {
      const res = await api.post(`/webhooks/configs/${config.id}/regenerate-secret`);
      setNewSecret(res.data.secret_key);
      setShowSecretDialog({ ...config, secret_key: res.data.secret_key });
      toast.success("Secret regenerado");
    } catch (error) {
      toast.error("Error al regenerar secret");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado al portapapeles");
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    return new Date(dateStr).toLocaleString("es-ES", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"
    });
  };

  const toggleEvent = (eventId) => {
    setFormData(prev => ({
      ...prev,
      events: prev.events.includes(eventId)
        ? prev.events.filter(e => e !== eventId)
        : [...prev.events, eventId]
    }));
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="webhooks-title">
            Webhooks
          </h1>
          <p className="text-slate-500">
            Recibe notificaciones en tiempo real desde tus tiendas
          </p>
        </div>
        <Button 
          onClick={() => setShowDialog(true)} 
          className="btn-primary"
          disabled={stores.length === 0}
          data-testid="create-webhook-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Crear Webhook
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Eventos Totales</p>
                  <p className="text-2xl font-bold text-slate-900">{stats.total_events}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-indigo-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Procesados</p>
                  <p className="text-2xl font-bold text-emerald-600">{stats.processed}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Pendientes</p>
                  <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Webhooks Activos</p>
                  <p className="text-2xl font-bold text-slate-900">
                    {configs.filter(c => c.enabled).length}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Webhook className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Webhook Configs */}
        <div className="lg:col-span-2">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <Webhook className="w-5 h-5 text-indigo-600" />
                Configuraciones de Webhook
              </CardTitle>
              <CardDescription>
                Endpoints configurados para recibir notificaciones
              </CardDescription>
            </CardHeader>
            <CardContent>
              {configs.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Webhook className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No hay webhooks configurados</p>
                  {stores.length === 0 && (
                    <p className="text-sm mt-2">Primero debes añadir una tienda</p>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {configs.map(config => (
                    <div 
                      key={config.id}
                      className={`p-4 rounded-lg border ${config.enabled ? 'border-emerald-200 bg-emerald-50/50' : 'border-slate-200 bg-slate-50'}`}
                      data-testid={`webhook-config-${config.id}`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${config.enabled ? 'bg-emerald-100' : 'bg-slate-200'}`}>
                            <Store className={`w-5 h-5 ${config.enabled ? 'text-emerald-600' : 'text-slate-500'}`} />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{config.store_name}</p>
                            <Badge className="bg-slate-100 text-slate-600 text-xs">{config.platform}</Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={config.enabled}
                            onCheckedChange={(checked) => handleToggle(config, checked)}
                            data-testid={`toggle-webhook-${config.id}`}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-rose-500 hover:text-rose-700"
                            onClick={() => { setSelectedConfig(config); setShowDeleteDialog(true); }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="bg-white/80 rounded-lg p-3 mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-slate-500">URL del Webhook</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={() => copyToClipboard(`${window.location.origin}${config.webhook_url}`)}
                          >
                            <Copy className="w-3 h-3 mr-1" />
                            Copiar
                          </Button>
                        </div>
                        <code className="text-xs text-slate-700 block break-all">
                          {window.location.origin}{config.webhook_url}
                        </code>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-4">
                          <span className="text-slate-500">
                            <Bell className="w-3 h-3 inline mr-1" />
                            {config.total_received || 0} eventos
                          </span>
                          <span className="text-slate-500">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {formatDate(config.last_received)}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => handleRegenerateSecret(config)}
                        >
                          <Key className="w-3 h-3 mr-1" />
                          Regenerar Secret
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recent Events */}
        <div>
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <Activity className="w-5 h-5 text-indigo-600" />
                Eventos Recientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-6 text-slate-500">
                  <Activity className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                  <p className="text-sm">No hay eventos aún</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {events.slice(0, 10).map(event => (
                    <div key={event.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        event.processed ? 'bg-emerald-100' : 'bg-amber-100'
                      }`}>
                        {event.processed ? (
                          <CheckCircle className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <Clock className="w-4 h-4 text-amber-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {event.event_type}
                        </p>
                        <p className="text-xs text-slate-500">
                          {formatDate(event.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Create Webhook Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Webhook className="w-5 h-5 text-indigo-600" />
              Crear Webhook
            </DialogTitle>
            <DialogDescription>
              Configura un webhook para recibir notificaciones de tu tienda
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Tienda</Label>
              <Select value={formData.store_id} onValueChange={(v) => setFormData({ ...formData, store_id: v })}>
                <SelectTrigger className="input-base" data-testid="webhook-store-select">
                  <Store className="w-4 h-4 mr-2 text-slate-400" />
                  <SelectValue placeholder="Selecciona una tienda" />
                </SelectTrigger>
                <SelectContent>
                  {stores.map(store => (
                    <SelectItem key={store.id} value={store.id}>
                      {store.name} ({store.platform})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Eventos a recibir</Label>
              <div className="space-y-2">
                {WEBHOOK_EVENTS.map(event => {
                  const Icon = event.icon;
                  return (
                    <div 
                      key={event.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        formData.events.includes(event.id) ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 hover:border-slate-300'
                      }`}
                      onClick={() => toggleEvent(event.id)}
                    >
                      <Checkbox 
                        checked={formData.events.includes(event.id)}
                        onCheckedChange={() => toggleEvent(event.id)}
                      />
                      <Icon className={`w-4 h-4 ${formData.events.includes(event.id) ? 'text-indigo-600' : 'text-slate-400'}`} />
                      <span className="text-sm">{event.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
              Cancelar
            </Button>
            <Button onClick={handleCreate} disabled={saving || !formData.store_id} className="btn-primary" data-testid="save-webhook-btn">
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Crear Webhook"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Secret Key Dialog */}
      <Dialog open={!!showSecretDialog} onOpenChange={() => { setShowSecretDialog(null); setNewSecret(null); }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Key className="w-5 h-5 text-amber-600" />
              Secret Key del Webhook
            </DialogTitle>
            <DialogDescription>
              Guarda este secret de forma segura. No se mostrará de nuevo.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 text-amber-700 mb-2">
                <AlertTriangle className="w-4 h-4" />
                <span className="font-medium">Importante</span>
              </div>
              <p className="text-sm text-amber-600">
                Copia este secret y configúralo en tu tienda para verificar los webhooks entrantes.
              </p>
            </div>
            
            <div className="bg-slate-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500">Secret Key</span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSecret(!showSecret)}
                  >
                    {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(newSecret || showSecretDialog?.secret_key)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <code className="text-sm font-mono text-slate-900 break-all">
                {showSecret ? (newSecret || showSecretDialog?.secret_key) : "••••••••••••••••••••••••••••••••"}
              </code>
            </div>
            
            {showSecretDialog && (
              <div className="mt-4 p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600 mb-1">URL del Webhook:</p>
                <code className="text-xs text-indigo-600 break-all">
                  {window.location.origin}{showSecretDialog.webhook_url}
                </code>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button onClick={() => { setShowSecretDialog(null); setNewSecret(null); }} className="btn-primary">
              Entendido
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar webhook?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la configuración del webhook para "{selectedConfig?.store_name}". 
              Tu tienda dejará de enviar notificaciones a esta URL.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700 text-white">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default WebhooksPage;
