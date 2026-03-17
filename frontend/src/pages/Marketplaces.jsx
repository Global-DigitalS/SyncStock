import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "../components/ui/alert-dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  ShoppingCart, Plus, Pencil, Trash2, Copy, ExternalLink, RefreshCw,
  CheckCircle, Globe, Package, Zap, Link2, Eye, FileText, AlertCircle
} from "lucide-react";
import { useCustomIcons } from "../hooks/useCustomIcons";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Platform icon map using emoji/color as fallback
const PLATFORM_COLORS = {
  google_merchant: "bg-blue-500",
  facebook_shops: "bg-indigo-600",
  amazon: "bg-orange-500",
  el_corte_ingles: "bg-green-600",
  miravia: "bg-pink-500",
  idealo: "bg-yellow-500",
  kelkoo: "bg-red-500",
  trovaprezzi: "bg-purple-500",
  ebay: "bg-sky-500",
  zalando: "bg-orange-700",
  pricerunner: "bg-teal-500",
  bing_shopping: "bg-cyan-600",
};

const PLATFORM_INITIALS = {
  google_merchant: "GM",
  facebook_shops: "FB",
  amazon: "AMZ",
  el_corte_ingles: "ECI",
  miravia: "MIR",
  idealo: "IDL",
  kelkoo: "KEL",
  trovaprezzi: "TRV",
  ebay: "eBay",
  zalando: "ZAL",
  pricerunner: "PR",
  bing_shopping: "BING",
};

const Marketplaces = () => {
  const { user } = useContext(AuthContext);
  const { getIconUrl } = useCustomIcons();
  const [platforms, setPlatforms] = useState([]);
  const [connections, setConnections] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showFeedDialog, setShowFeedDialog] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(1); // 1: select platform, 2: configure

  const emptyForm = {
    platform_id: "",
    name: "",
    catalog_id: "",
    store_url: "",
    currency: "EUR",
    condition: "new",
    shipping_cost: "",
    delivery_time: "",
    include_out_of_stock: false,
    field_mapping: {},
  };
  const [formData, setFormData] = useState(emptyForm);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [platformsRes, connectionsRes, catalogsRes] = await Promise.all([
        api.get("/marketplaces/platforms"),
        api.get("/marketplaces/connections"),
        api.get("/catalogs"),
      ]);
      setPlatforms(platformsRes.data);
      setConnections(connectionsRes.data);
      setCatalogs(catalogsRes.data || []);
    } catch (error) {
      toast.error("Error al cargar los datos de marketplaces");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlatform = (platform) => {
    setSelectedPlatform(platform);
    setFormData({
      ...emptyForm,
      platform_id: platform.id,
      name: platform.name,
    });
    setStep(2);
  };

  const handleCreate = async () => {
    if (!formData.catalog_id) {
      toast.error("Debes seleccionar un catálogo");
      return;
    }
    setSaving(true);
    try {
      await api.post("/marketplaces/connections", formData);
      toast.success("Conexión de marketplace creada correctamente");
      setShowCreateDialog(false);
      resetForm();
      fetchAll();
    } catch (error) {
      const msg = error.response?.data?.detail || "Error al crear la conexión";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (connection) => {
    setSelectedConnection(connection);
    const platform = platforms.find((p) => p.id === connection.platform_id);
    setSelectedPlatform(platform || null);
    setFormData({
      platform_id: connection.platform_id,
      name: connection.name,
      catalog_id: connection.catalog_id,
      store_url: connection.store_url || "",
      currency: connection.currency || "EUR",
      condition: connection.condition || "new",
      shipping_cost: connection.shipping_cost || "",
      delivery_time: connection.delivery_time || "",
      include_out_of_stock: connection.include_out_of_stock || false,
      field_mapping: connection.field_mapping || {},
    });
    setShowEditDialog(true);
  };

  const handleUpdate = async () => {
    if (!selectedConnection) return;
    setSaving(true);
    try {
      await api.put(`/marketplaces/connections/${selectedConnection.id}`, formData);
      toast.success("Conexión actualizada correctamente");
      setShowEditDialog(false);
      setSelectedConnection(null);
      fetchAll();
    } catch (error) {
      const msg = error.response?.data?.detail || "Error al actualizar la conexión";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedConnection) return;
    try {
      await api.delete(`/marketplaces/connections/${selectedConnection.id}`);
      toast.success("Conexión eliminada correctamente");
      setShowDeleteDialog(false);
      setSelectedConnection(null);
      fetchAll();
    } catch (error) {
      toast.error("Error al eliminar la conexión");
    }
  };

  const handleToggleActive = async (connection) => {
    try {
      await api.put(`/marketplaces/connections/${connection.id}`, {
        is_active: !connection.is_active,
      });
      toast.success(connection.is_active ? "Feed desactivado" : "Feed activado");
      fetchAll();
    } catch (error) {
      toast.error("Error al cambiar el estado");
    }
  };

  const getFeedUrl = (connection) => {
    return `${BACKEND_URL}/api/marketplaces/feeds/${connection.id}/feed`;
  };

  const copyFeedUrl = (connection) => {
    navigator.clipboard.writeText(getFeedUrl(connection));
    toast.success("URL del feed copiada al portapapeles");
  };

  const resetForm = () => {
    setFormData(emptyForm);
    setSelectedPlatform(null);
    setStep(1);
  };

  const maxConnections = user?.max_marketplace_connections ?? 1;
  const currentCount = connections.length;
  const limitReached = currentCount >= maxConnections && user?.role !== "superadmin";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Marketplaces</h1>
          <p className="text-sm text-slate-500 mt-1">
            Genera feeds de productos para publicar en los principales marketplaces y comparadores de precios
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">
            {currentCount} / {maxConnections === 999999 ? "∞" : maxConnections} feeds
          </span>
          <Button
            onClick={() => { resetForm(); setShowCreateDialog(true); }}
            disabled={limitReached}
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            Nueva conexión
          </Button>
        </div>
      </div>

      {/* Limit warning */}
      {limitReached && (
        <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>Has alcanzado el límite de conexiones de marketplace de tu plan ({maxConnections}). Actualiza tu suscripción para añadir más.</span>
        </div>
      )}

      {/* Connections list */}
      {connections.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4">
              <ShoppingCart className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Sin conexiones de marketplace</h3>
            <p className="text-slate-500 text-sm max-w-md mb-6">
              Conecta tus catálogos con Google Merchant, Amazon, El Corte Inglés y más de 10 plataformas para publicar tus productos automáticamente.
            </p>
            <Button onClick={() => { resetForm(); setShowCreateDialog(true); }} className="gap-2">
              <Plus className="w-4 h-4" />
              Crear primera conexión
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {connections.map((connection) => {
            const platform = platforms.find((p) => p.id === connection.platform_id);
            const bgColor = PLATFORM_COLORS[connection.platform_id] || "bg-slate-500";
            const initials = PLATFORM_INITIALS[connection.platform_id] || connection.platform_id.substring(0, 3).toUpperCase();
            const customIconUrl = getIconUrl(`marketplace_${connection.platform_id}`);

            return (
              <Card key={connection.id} className={`relative transition-all ${!connection.is_active ? "opacity-60" : ""}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 ${bgColor} rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
                        {customIconUrl ? (
                          <img src={customIconUrl} alt={connection.platform_id} className="w-7 h-7 object-contain" />
                        ) : initials}
                      </div>
                      <div className="min-w-0">
                        <CardTitle className="text-base truncate">{connection.name}</CardTitle>
                        <CardDescription className="text-xs">{connection.platform_name}</CardDescription>
                      </div>
                    </div>
                    <Switch
                      checked={connection.is_active}
                      onCheckedChange={() => handleToggleActive(connection)}
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Catalog */}
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Package className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span className="truncate">{connection.catalog_name || "Sin catálogo"}</span>
                  </div>

                  {/* Format badge */}
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {connection.feed_format.toUpperCase()}
                    </Badge>
                    {connection.include_out_of_stock && (
                      <Badge variant="secondary" className="text-xs">Sin stock incluido</Badge>
                    )}
                  </div>

                  {/* Stats */}
                  {connection.last_generated && (
                    <div className="text-xs text-slate-500">
                      Última generación: {new Date(connection.last_generated).toLocaleString("es-ES")}
                      {" · "}{connection.products_count} productos
                    </div>
                  )}

                  {/* Feed URL */}
                  <div className="flex items-center gap-1 pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 text-xs gap-1 truncate"
                      onClick={() => copyFeedUrl(connection)}
                    >
                      <Copy className="w-3 h-3 flex-shrink-0" />
                      Copiar URL del feed
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => window.open(getFeedUrl(connection), "_blank")}
                      title="Abrir feed"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </Button>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex-1 gap-1 text-xs"
                      onClick={() => handleEdit(connection)}
                    >
                      <Pencil className="w-3 h-3" />
                      Editar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="flex-1 gap-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => { setSelectedConnection(connection); setShowDeleteDialog(true); }}
                    >
                      <Trash2 className="w-3 h-3" />
                      Eliminar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* ==================== CREATE DIALOG ==================== */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {step === 1 ? "Seleccionar plataforma" : `Configurar ${selectedPlatform?.name}`}
            </DialogTitle>
            <DialogDescription>
              {step === 1
                ? "Elige el marketplace o comparador donde quieres publicar tus productos"
                : "Configura los parámetros de tu feed de productos"}
            </DialogDescription>
          </DialogHeader>

          {step === 1 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 py-2">
              {platforms.map((platform) => {
                const bgColor = PLATFORM_COLORS[platform.id] || "bg-slate-500";
                const initials = PLATFORM_INITIALS[platform.id] || platform.id.substring(0, 3).toUpperCase();
                const customIconUrl = getIconUrl(`marketplace_${platform.id}`);
                return (
                  <button
                    key={platform.id}
                    onClick={() => handleSelectPlatform(platform)}
                    className="flex flex-col items-center gap-3 p-4 border-2 border-slate-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all text-center group"
                  >
                    <div className={`w-12 h-12 ${bgColor} rounded-xl flex items-center justify-center text-white text-sm font-bold`}>
                      {customIconUrl ? (
                        <img src={customIconUrl} alt={platform.name} className="w-9 h-9 object-contain" />
                      ) : initials}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800 group-hover:text-blue-700">{platform.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{platform.feed_format.toUpperCase()}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <ConnectionForm
              formData={formData}
              setFormData={setFormData}
              catalogs={catalogs}
              platform={selectedPlatform}
            />
          )}

          <DialogFooter className="gap-2">
            {step === 2 && (
              <Button variant="outline" onClick={() => setStep(1)}>
                Atrás
              </Button>
            )}
            <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetForm(); }}>
              Cancelar
            </Button>
            {step === 2 && (
              <Button onClick={handleCreate} disabled={saving}>
                {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
                Crear conexión
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== EDIT DIALOG ==================== */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar conexión — {selectedConnection?.platform_name}</DialogTitle>
            <DialogDescription>Modifica la configuración del feed de marketplace</DialogDescription>
          </DialogHeader>

          <ConnectionForm
            formData={formData}
            setFormData={setFormData}
            catalogs={catalogs}
            platform={selectedPlatform}
          />

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancelar</Button>
            <Button onClick={handleUpdate} disabled={saving}>
              {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
              Guardar cambios
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== DELETE DIALOG ==================== */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar conexión</AlertDialogTitle>
            <AlertDialogDescription>
              ¿Estás seguro de que quieres eliminar la conexión <strong>{selectedConnection?.name}</strong>?
              El feed dejará de estar disponible y no se podrá recuperar.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

// ==================== CONNECTION FORM COMPONENT ====================

const ConnectionForm = ({ formData, setFormData, catalogs, platform }) => {
  const update = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }));

  const CURRENCIES = ["EUR", "USD", "GBP", "MXN", "ARS", "COP", "CLP", "PEN"];
  const CONDITIONS = [
    { value: "new", label: "Nuevo" },
    { value: "used", label: "Usado" },
    { value: "refurbished", label: "Reacondicionado" },
  ];

  return (
    <div className="space-y-4 py-2">
      {/* Name */}
      <div className="space-y-1.5">
        <Label htmlFor="name">Nombre de la conexión</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => update("name", e.target.value)}
          placeholder={`Ej: ${platform?.name} - Catálogo Principal`}
        />
      </div>

      {/* Catalog */}
      <div className="space-y-1.5">
        <Label htmlFor="catalog_id">Catálogo de productos <span className="text-red-500">*</span></Label>
        <Select value={formData.catalog_id} onValueChange={(v) => update("catalog_id", v)}>
          <SelectTrigger id="catalog_id">
            <SelectValue placeholder="Seleccionar catálogo..." />
          </SelectTrigger>
          <SelectContent>
            {catalogs.map((cat) => (
              <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-slate-500">Los productos de este catálogo se incluirán en el feed</p>
      </div>

      {/* Store URL */}
      <div className="space-y-1.5">
        <Label htmlFor="store_url">URL de tu tienda / página de producto</Label>
        <Input
          id="store_url"
          type="url"
          value={formData.store_url}
          onChange={(e) => update("store_url", e.target.value)}
          placeholder="https://tutienda.com"
        />
        <p className="text-xs text-slate-500">Se usará como enlace de producto en el feed</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Currency */}
        <div className="space-y-1.5">
          <Label>Moneda</Label>
          <Select value={formData.currency} onValueChange={(v) => update("currency", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CURRENCIES.map((c) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Condition */}
        <div className="space-y-1.5">
          <Label>Condición por defecto</Label>
          <Select value={formData.condition} onValueChange={(v) => update("condition", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CONDITIONS.map((c) => (
                <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Shipping cost */}
        <div className="space-y-1.5">
          <Label htmlFor="shipping_cost">Gastos de envío</Label>
          <Input
            id="shipping_cost"
            value={formData.shipping_cost}
            onChange={(e) => update("shipping_cost", e.target.value)}
            placeholder="Ej: 4.99"
          />
        </div>

        {/* Delivery time */}
        <div className="space-y-1.5">
          <Label htmlFor="delivery_time">Plazo de entrega</Label>
          <Input
            id="delivery_time"
            value={formData.delivery_time}
            onChange={(e) => update("delivery_time", e.target.value)}
            placeholder="Ej: 2-3 días"
          />
        </div>
      </div>

      {/* Include out of stock */}
      <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
        <div>
          <p className="text-sm font-medium text-slate-800">Incluir productos sin stock</p>
          <p className="text-xs text-slate-500">Si está desactivado, solo se incluirán productos con stock &gt; 0</p>
        </div>
        <Switch
          checked={formData.include_out_of_stock}
          onCheckedChange={(v) => update("include_out_of_stock", v)}
        />
      </div>

      {/* Feed format info */}
      {platform && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          <div className="flex items-center gap-2 font-medium text-blue-800 mb-1">
            <FileText className="w-4 h-4" />
            Formato del feed: {platform.feed_format.toUpperCase()}
          </div>
          <p className="text-blue-700 text-xs">
            El feed se generará en formato {platform.feed_format.toUpperCase()} compatible con {platform.name}.
            Una vez creada la conexión, obtendrás una URL pública que puedes registrar en {platform.name}.
          </p>
          {platform.docs_url && (
            <a
              href={platform.docs_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-xs mt-2"
            >
              <ExternalLink className="w-3 h-3" />
              Ver documentación oficial
            </a>
          )}
        </div>
      )}
    </div>
  );
};

export default Marketplaces;
