import { useState, useEffect } from "react";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Building2,
  Plus,
  Settings,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  ExternalLink,
  Link2,
  Users,
  Package,
  FileText,
  Zap,
  Truck,
  ShoppingCart,
  Image,
  DollarSign,
  Layers,
  ChevronDown,
  ChevronUp
} from "lucide-react";

// CRM Platform configurations
const CRM_PLATFORMS = {
  dolibarr: {
    id: "dolibarr",
    name: "Dolibarr",
    description: "ERP y CRM de código abierto",
    logo: "/dolibarr-logo.png",
    color: "#4a90a4",
    fields: [
      { key: "api_url", label: "URL de la API", placeholder: "https://tu-dolibarr.com/api/index.php", type: "text", required: true },
      { key: "api_key", label: "API Key (DOLAPIKEY)", placeholder: "Tu clave API de Dolibarr", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar catálogo de productos" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Proveedores", icon: Truck, description: "Sincronizar lista de proveedores" },
      { key: "orders", label: "Pedidos", icon: ShoppingCart, description: "Importar pedidos desde tiendas" },
    ],
    features: ["Sincronizar productos", "Stock y precios", "Proveedores", "Pedidos de tiendas"]
  },
};

const CRMPage = () => {
  const [connections, setConnections] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [selectedCatalogId, setSelectedCatalogId] = useState("");
  const [configForm, setConfigForm] = useState({});
  const [syncSettings, setSyncSettings] = useState({
    products: true,
    stock: true,
    prices: true,
    descriptions: true,
    images: true,
    suppliers: true,
    orders: true
  });
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState({});
  const [expandedCard, setExpandedCard] = useState(null);

  useEffect(() => {
    fetchConnections();
    fetchCatalogs();
  }, []);

  const fetchConnections = async () => {
    try {
      const res = await api.get("/crm/connections");
      setConnections(res.data);
    } catch (error) {
      console.error("Error fetching CRM connections:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCatalogs = async () => {
    try {
      const res = await api.get("/catalogs");
      setCatalogs(res.data);
    } catch (error) {
      console.error("Error fetching catalogs:", error);
    }
  };

  const handleAddConnection = (platform) => {
    setSelectedPlatform(platform);
    setConfigForm({ name: `Mi ${platform.name}`, platform: platform.id });
    setSyncSettings({
      products: true,
      stock: true,
      prices: true,
      descriptions: true,
      images: true,
      suppliers: true,
      orders: true
    });
    setShowAddDialog(false);
    setShowConfigDialog(true);
  };

  const handleEditConnection = (connection) => {
    const platform = CRM_PLATFORMS[connection.platform];
    setSelectedPlatform(platform);
    setSelectedConnection(connection);
    setConfigForm({
      name: connection.name,
      platform: connection.platform,
      ...connection.config
    });
    setSyncSettings(connection.sync_settings || {
      products: true,
      stock: true,
      prices: true,
      descriptions: true,
      images: true,
      suppliers: true,
      orders: true
    });
    setShowConfigDialog(true);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const testData = {
        platform: selectedPlatform.id,
        config: {}
      };
      
      selectedPlatform.fields.forEach(field => {
        testData.config[field.key] = configForm[field.key];
      });

      const res = await api.post("/crm/test-connection", testData);
      
      if (res.data.status === "success") {
        toast.success(`Conexión exitosa con ${selectedPlatform.name}${res.data.version ? ` (v${res.data.version})` : ''}`);
      } else {
        toast.error(res.data.message || "Error de conexión");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al probar la conexión");
    } finally {
      setTesting(false);
    }
  };

  const handleSaveConnection = async () => {
    setSaving(true);
    try {
      const connectionData = {
        name: configForm.name,
        platform: selectedPlatform.id,
        config: {},
        sync_settings: syncSettings
      };
      
      selectedPlatform.fields.forEach(field => {
        connectionData.config[field.key] = configForm[field.key];
      });

      if (selectedConnection) {
        await api.put(`/crm/connections/${selectedConnection.id}`, connectionData);
        toast.success("Conexión actualizada");
      } else {
        await api.post("/crm/connections", connectionData);
        toast.success("Conexión creada");
      }
      
      setShowConfigDialog(false);
      setSelectedConnection(null);
      setConfigForm({});
      fetchConnections();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar la conexión");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConnection = async (connectionId) => {
    if (!window.confirm("¿Estás seguro de eliminar esta conexión?")) return;
    
    try {
      await api.delete(`/crm/connections/${connectionId}`);
      toast.success("Conexión eliminada");
      fetchConnections();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const handleOpenSyncDialog = (connection) => {
    setSelectedConnection(connection);
    setSelectedPlatform(CRM_PLATFORMS[connection.platform]);
    setSyncSettings(connection.sync_settings || {});
    setSelectedCatalogId(""); // Reset catalog selection
    setShowSyncDialog(true);
  };

  const handleSync = async (syncType = "all") => {
    if (!selectedConnection) return;
    
    setSyncing(prev => ({ ...prev, [selectedConnection.id]: true }));
    try {
      const payload = { 
        sync_type: syncType,
        sync_settings: syncSettings
      };
      
      // Add catalog_id if selected
      if (selectedCatalogId) {
        payload.catalog_id = selectedCatalogId;
      }
      
      const res = await api.post(`/crm/connections/${selectedConnection.id}/sync`, payload);
      
      if (res.data.status === "success") {
        toast.success(res.data.message || "Sincronización completada");
      } else {
        toast.warning(res.data.message || "Sincronización parcial");
      }
      
      fetchConnections();
      setShowSyncDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error en la sincronización");
    } finally {
      setSyncing(prev => ({ ...prev, [selectedConnection.id]: false }));
    }
  };

  const handleQuickSync = async (connectionId, syncType) => {
    setSyncing(prev => ({ ...prev, [`${connectionId}-${syncType}`]: true }));
    try {
      const res = await api.post(`/crm/connections/${connectionId}/sync`, { sync_type: syncType });
      toast.success(res.data.message || `${syncType} sincronizado`);
      fetchConnections();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error en la sincronización");
    } finally {
      setSyncing(prev => ({ ...prev, [`${connectionId}-${syncType}`]: false }));
    }
  };

  const getStatusBadge = (connection) => {
    if (connection.is_connected) {
      return (
        <Badge className="bg-emerald-100 text-emerald-700 border-0">
          <CheckCircle className="w-3 h-3 mr-1" />
          Conectado
        </Badge>
      );
    }
    return (
      <Badge className="bg-red-100 text-red-700 border-0">
        <XCircle className="w-3 h-3 mr-1" />
        Desconectado
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Conexiones CRM
          </h1>
          <p className="text-slate-500 mt-1">
            Sincroniza proveedores, productos, stock, precios y pedidos con tu CRM
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)} className="btn-primary" data-testid="add-crm-btn">
          <Plus className="w-4 h-4 mr-2" />
          Añadir CRM
        </Button>
      </div>

      {/* Connections List */}
      {connections.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Building2 className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No hay conexiones CRM</h3>
            <p className="text-slate-500 text-center mb-4 max-w-md">
              Conecta tu catálogo con un sistema CRM para sincronizar proveedores, productos, stock, precios y pedidos automáticamente.
            </p>
            <Button onClick={() => setShowAddDialog(true)} className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Añadir tu primer CRM
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {connections.map((connection) => {
            const platform = CRM_PLATFORMS[connection.platform];
            const isExpanded = expandedCard === connection.id;
            return (
              <Card key={connection.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: platform?.color || "#4f46e5" }}
                      >
                        <Building2 className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{connection.name}</CardTitle>
                        <CardDescription>{platform?.name || connection.platform}</CardDescription>
                      </div>
                    </div>
                    {getStatusBadge(connection)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div className="bg-slate-50 rounded-lg p-2">
                      <Package className="w-4 h-4 mx-auto text-slate-400 mb-1" />
                      <p className="text-sm font-semibold">{connection.stats?.products || 0}</p>
                      <p className="text-xs text-slate-500">Productos</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <Truck className="w-4 h-4 mx-auto text-slate-400 mb-1" />
                      <p className="text-sm font-semibold">{connection.stats?.suppliers || 0}</p>
                      <p className="text-xs text-slate-500">Proveed.</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <Users className="w-4 h-4 mx-auto text-slate-400 mb-1" />
                      <p className="text-sm font-semibold">{connection.stats?.clients || 0}</p>
                      <p className="text-xs text-slate-500">Clientes</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <ShoppingCart className="w-4 h-4 mx-auto text-slate-400 mb-1" />
                      <p className="text-sm font-semibold">{connection.stats?.orders || 0}</p>
                      <p className="text-xs text-slate-500">Pedidos</p>
                    </div>
                  </div>

                  {/* Last sync */}
                  {connection.last_sync && (
                    <p className="text-xs text-slate-500 text-center">
                      Última sync: {new Date(connection.last_sync).toLocaleString("es-ES")}
                    </p>
                  )}

                  {/* Quick Sync Buttons */}
                  <div 
                    className="cursor-pointer flex items-center justify-between text-sm text-slate-600 hover:text-slate-900"
                    onClick={() => setExpandedCard(isExpanded ? null : connection.id)}
                  >
                    <span className="font-medium">Sincronización rápida</span>
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>

                  {isExpanded && (
                    <div className="grid grid-cols-2 gap-2 animate-in slide-in-from-top-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickSync(connection.id, "products")}
                        disabled={syncing[`${connection.id}-products`]}
                        className="text-xs"
                      >
                        {syncing[`${connection.id}-products`] ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <Package className="w-3 h-3 mr-1" />}
                        Productos
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickSync(connection.id, "suppliers")}
                        disabled={syncing[`${connection.id}-suppliers`]}
                        className="text-xs"
                      >
                        {syncing[`${connection.id}-suppliers`] ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <Truck className="w-3 h-3 mr-1" />}
                        Proveedores
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickSync(connection.id, "orders")}
                        disabled={syncing[`${connection.id}-orders`]}
                        className="text-xs col-span-2"
                      >
                        {syncing[`${connection.id}-orders`] ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <ShoppingCart className="w-3 h-3 mr-1" />}
                        Importar Pedidos
                      </Button>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleOpenSyncDialog(connection)}
                      disabled={syncing[connection.id]}
                      data-testid={`sync-all-${connection.id}`}
                    >
                      {syncing[connection.id] ? (
                        <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <Zap className="w-4 h-4 mr-1" />
                      )}
                      Sync Completo
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditConnection(connection)}
                      data-testid={`edit-crm-${connection.id}`}
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleDeleteConnection(connection.id)}
                      data-testid={`delete-crm-${connection.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add CRM Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Seleccionar CRM</DialogTitle>
            <DialogDescription>
              Elige el sistema CRM que deseas conectar
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-4">
            {Object.values(CRM_PLATFORMS).map((platform) => (
              <button
                key={platform.id}
                onClick={() => handleAddConnection(platform)}
                className="flex items-start gap-4 p-4 border border-slate-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
                data-testid={`select-crm-${platform.id}`}
              >
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                  style={{ backgroundColor: platform.color }}
                >
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-900">{platform.name}</h4>
                  <p className="text-sm text-slate-500">{platform.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {platform.features.map((feature, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-slate-400 shrink-0" />
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Config Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={(open) => {
        setShowConfigDialog(open);
        if (!open) {
          setSelectedConnection(null);
          setConfigForm({});
        }
      }}>
        <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              {selectedConnection ? "Editar" : "Configurar"} {selectedPlatform?.name}
            </DialogTitle>
            <DialogDescription>
              Configura la conexión y opciones de sincronización
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Connection Name */}
            <div className="space-y-2">
              <Label>Nombre de la conexión</Label>
              <Input
                value={configForm.name || ""}
                onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                placeholder="Mi Dolibarr"
                data-testid="crm-connection-name"
              />
            </div>

            {/* Platform-specific fields */}
            {selectedPlatform?.fields.map((field) => (
              <div key={field.key} className="space-y-2">
                <Label>
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </Label>
                <Input
                  type={field.type}
                  value={configForm[field.key] || ""}
                  onChange={(e) => setConfigForm({ ...configForm, [field.key]: e.target.value })}
                  placeholder={field.placeholder}
                  data-testid={`crm-field-${field.key}`}
                />
              </div>
            ))}

            {/* Sync Options */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Opciones de Sincronización</Label>
              <p className="text-sm text-slate-500">Selecciona qué datos quieres sincronizar con el CRM</p>
              
              <div className="grid grid-cols-2 gap-3 mt-3">
                {selectedPlatform?.syncOptions?.map((option) => {
                  const Icon = option.icon;
                  return (
                    <div 
                      key={option.key}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        syncSettings[option.key] 
                          ? 'border-blue-300 bg-blue-50' 
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                      onClick={() => setSyncSettings({...syncSettings, [option.key]: !syncSettings[option.key]})}
                    >
                      <Checkbox 
                        checked={syncSettings[option.key] || false}
                        onCheckedChange={(checked) => setSyncSettings({...syncSettings, [option.key]: checked})}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-slate-600" />
                          <span className="font-medium text-sm">{option.label}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{option.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Dolibarr specific help */}
            {selectedPlatform?.id === "dolibarr" && (
              <div className="bg-blue-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-blue-800 mb-1">¿Cómo obtener la API Key?</p>
                <ol className="text-blue-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu Dolibarr como administrador</li>
                  <li>Ve a Inicio → Configuración → Módulos</li>
                  <li>Activa el módulo "API REST (servidor)"</li>
                  <li>Ve a tu perfil de usuario → Pestaña "API"</li>
                  <li>Genera o copia tu clave API</li>
                </ol>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={testing}
              data-testid="test-crm-connection"
            >
              {testing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Probando...
                </>
              ) : (
                <>
                  <Link2 className="w-4 h-4 mr-2" />
                  Probar Conexión
                </>
              )}
            </Button>
            <Button
              onClick={handleSaveConnection}
              disabled={saving}
              className="btn-primary"
              data-testid="save-crm-connection"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Guardando...
                </>
              ) : (
                "Guardar"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sync Dialog */}
      <Dialog open={showSyncDialog} onOpenChange={setShowSyncDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Sincronización Completa
            </DialogTitle>
            <DialogDescription>
              Selecciona qué datos sincronizar con {selectedConnection?.name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Catalog Selector */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Catálogo a sincronizar</Label>
              <Select value={selectedCatalogId} onValueChange={setSelectedCatalogId}>
                <SelectTrigger data-testid="sync-catalog-selector">
                  <SelectValue placeholder="Todos los productos seleccionados" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todos los productos seleccionados</SelectItem>
                  {catalogs.map((catalog) => (
                    <SelectItem key={catalog.id} value={catalog.id}>
                      {catalog.name} ({catalog.products?.length || 0} productos)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                {selectedCatalogId 
                  ? "Solo se sincronizarán los productos de este catálogo"
                  : "Se sincronizarán todos los productos marcados como seleccionados"}
              </p>
            </div>

            {/* Sync Options */}
            <div className="space-y-3">
              {selectedPlatform?.syncOptions?.map((option) => {
                const Icon = option.icon;
                return (
                  <div 
                    key={option.key}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      syncSettings[option.key] 
                        ? 'border-blue-300 bg-blue-50' 
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                    onClick={() => setSyncSettings({...syncSettings, [option.key]: !syncSettings[option.key]})}
                  >
                    <Checkbox 
                      checked={syncSettings[option.key] || false}
                      onCheckedChange={(checked) => setSyncSettings({...syncSettings, [option.key]: checked})}
                    />
                    <Icon className="w-5 h-5 text-slate-600" />
                    <div className="flex-1">
                      <span className="font-medium">{option.label}</span>
                      <p className="text-xs text-slate-500">{option.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSyncDialog(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={() => handleSync("all")} 
              className="btn-primary"
              disabled={syncing[selectedConnection?.id]}
            >
              {syncing[selectedConnection?.id] ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Sincronizando...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Iniciar Sincronización
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CRMPage;
