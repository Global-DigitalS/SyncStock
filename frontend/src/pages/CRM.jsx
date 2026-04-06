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
import { Progress } from "../components/ui/progress";
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
import { useCustomIcons } from "../hooks/useCustomIcons";

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
  odoo: {
    id: "odoo",
    name: "Odoo",
    description: "Plataforma ERP/CRM completa",
    logo: "/odoo-logo.png",
    color: "#875a7b",
    fields: [
      { key: "api_url", label: "URL de Odoo", placeholder: "https://tu-odoo.com", type: "text", required: true },
      { key: "api_token", label: "API Token", placeholder: "Tu token de acceso de Odoo", type: "password", required: true },
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
  hubspot: {
    id: "hubspot",
    name: "HubSpot",
    description: "CRM líder en marketing y ventas",
    logo: "/hubspot-logo.png",
    color: "#ff7a59",
    fields: [
      { key: "api_token", label: "Token de acceso privado", placeholder: "pat-na1-xxxxxxxx-xxxx-xxxx", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar productos como Line Items" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Contactos", icon: Truck, description: "Sincronizar proveedores como contactos" },
      { key: "orders", label: "Deals", icon: ShoppingCart, description: "Importar pedidos como deals" },
    ],
    features: ["Productos como Line Items", "Contactos y Deals", "Proveedores", "Precios y stock"]
  },
  salesforce: {
    id: "salesforce",
    name: "Salesforce",
    description: "CRM empresarial líder mundial",
    logo: "/salesforce-logo.png",
    color: "#00a1e0",
    fields: [
      { key: "api_url", label: "URL de instancia", placeholder: "https://tu-empresa.my.salesforce.com", type: "text", required: true },
      { key: "client_id", label: "Client ID (Consumer Key)", placeholder: "Tu Consumer Key de Connected App", type: "text", required: true },
      { key: "client_secret", label: "Client Secret", placeholder: "Tu Consumer Secret", type: "password", required: true },
      { key: "api_token", label: "Access Token", placeholder: "Token de acceso OAuth", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Products", icon: Package, description: "Sincronizar como Products en Salesforce" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar Pricebook Entries" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Accounts", icon: Truck, description: "Sincronizar proveedores como Accounts" },
      { key: "orders", label: "Opportunities", icon: ShoppingCart, description: "Importar pedidos como Opportunities" },
    ],
    features: ["Products y Pricebooks", "Accounts y Opportunities", "Proveedores", "Stock y precios"]
  },
  zoho: {
    id: "zoho",
    name: "Zoho CRM",
    description: "CRM completo para pymes y empresas",
    logo: "/zoho-logo.png",
    color: "#e42527",
    fields: [
      { key: "api_url", label: "URL del dominio API", placeholder: "https://www.zohoapis.eu", type: "text", required: true },
      { key: "client_id", label: "Client ID", placeholder: "Tu Client ID de Zoho", type: "text", required: true },
      { key: "client_secret", label: "Client Secret", placeholder: "Tu Client Secret de Zoho", type: "password", required: true },
      { key: "api_token", label: "Refresh Token", placeholder: "Tu Refresh Token de Zoho", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar como Products en Zoho" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Vendors", icon: Truck, description: "Sincronizar proveedores como Vendors" },
      { key: "orders", label: "Sales Orders", icon: ShoppingCart, description: "Importar pedidos como Sales Orders" },
    ],
    features: ["Products y Vendors", "Sales Orders", "Proveedores", "Stock y precios"]
  },
  pipedrive: {
    id: "pipedrive",
    name: "Pipedrive",
    description: "CRM de ventas intuitivo y potente",
    logo: "/pipedrive-logo.png",
    color: "#017737",
    fields: [
      { key: "api_url", label: "URL de la empresa", placeholder: "https://tu-empresa.pipedrive.com", type: "text", required: true },
      { key: "api_token", label: "API Token", placeholder: "Tu token API de Pipedrive", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar catálogo de productos" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Organizaciones", icon: Truck, description: "Sincronizar proveedores como organizaciones" },
      { key: "orders", label: "Deals", icon: ShoppingCart, description: "Importar pedidos como deals" },
    ],
    features: ["Productos y Deals", "Organizaciones", "Proveedores", "Precios y stock"]
  },
  monday: {
    id: "monday",
    name: "Monday CRM",
    description: "CRM flexible basado en work management",
    logo: "/monday-logo.png",
    color: "#6161ff",
    fields: [
      { key: "api_token", label: "API Token", placeholder: "Tu token API de Monday.com", type: "password", required: true },
      { key: "board_id", label: "ID del Board", placeholder: "ID del board de productos", type: "text", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar productos como ítems del board" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar columna de stock" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Proveedores", icon: Truck, description: "Sincronizar proveedores como ítems" },
      { key: "orders", label: "Pedidos", icon: ShoppingCart, description: "Importar pedidos como ítems" },
    ],
    features: ["Productos en Boards", "Stock y precios", "Proveedores", "Pedidos"]
  },
  freshsales: {
    id: "freshsales",
    name: "Freshsales",
    description: "CRM inteligente con IA integrada",
    logo: "/freshsales-logo.png",
    color: "#f26522",
    fields: [
      { key: "api_url", label: "URL del dominio", placeholder: "https://tu-empresa.myfreshworks.com/crm/sales", type: "text", required: true },
      { key: "api_token", label: "API Key", placeholder: "Tu API Key de Freshsales", type: "password", required: true },
    ],
    syncOptions: [
      { key: "products", label: "Productos", icon: Package, description: "Sincronizar catálogo de productos" },
      { key: "stock", label: "Stock", icon: Layers, description: "Actualizar niveles de inventario" },
      { key: "prices", label: "Precios", icon: DollarSign, description: "Sincronizar precios de productos" },
      { key: "descriptions", label: "Descripciones", icon: FileText, description: "Incluir descripciones y marca" },
      { key: "images", label: "Imágenes", icon: Image, description: "Subir imágenes de productos" },
      { key: "suppliers", label: "Contactos", icon: Truck, description: "Sincronizar proveedores como contactos" },
      { key: "orders", label: "Deals", icon: ShoppingCart, description: "Importar pedidos como deals" },
    ],
    features: ["Productos y Deals", "Contactos", "Proveedores", "Precios y stock"]
  },
};

const CRMPage = () => {
  const { getIconUrl } = useCustomIcons();
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
  const [syncProgress, setSyncProgress] = useState(null);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  useEffect(() => {
    fetchConnections();
    fetchCatalogs();
  }, []);

  const fetchConnections = async () => {
    try {
      const res = await api.get("/crm/connections");
      setConnections(res.data);
    } catch (error) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  const fetchCatalogs = async () => {
    try {
      const res = await api.get("/catalogs");
      setCatalogs(res.data);
    } catch (error) {
      // handled silently
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
    
    // Require catalog selection
    if (!selectedCatalogId) {
      toast.error("Debes seleccionar un catálogo para sincronizar");
      return;
    }
    
    setSyncing(prev => ({ ...prev, [selectedConnection.id]: true }));
    setShowSyncDialog(false);
    setShowProgressDialog(true);
    setSyncProgress({
      status: "running",
      progress: 0,
      current_step: "Iniciando sincronización...",
      total_items: 0,
      processed_items: 0,
      created: 0,
      updated: 0,
      errors: 0
    });
    
    try {
      const payload = { 
        sync_type: syncType,
        sync_settings: syncSettings,
        catalog_id: selectedCatalogId  // Always required now
      };
      
      const res = await api.post(`/crm/connections/${selectedConnection.id}/sync`, payload);
      
      // Start polling for progress - the backend now returns immediately with job ID
      if (res.data.sync_job_id) {
        pollSyncProgress(res.data.sync_job_id);
      } else {
        // Fallback: No job tracking
        setSyncProgress(prev => ({
          ...prev,
          status: "completed",
          progress: 100,
          current_step: res.data.message || "Sincronización completada"
        }));
        fetchConnections();
      }
    } catch (error) {
      setSyncProgress(prev => ({
        ...prev,
        status: "error",
        current_step: error.response?.data?.detail || "Error en la sincronización"
      }));
      toast.error(error.response?.data?.detail || "Error en la sincronización");
      setSyncing(prev => ({ ...prev, [selectedConnection.id]: false }));
    }
  };

  const pollSyncProgress = async (jobId) => {
    let attempts = 0;
    const maxAttempts = 600; // 10 minutes max
    
    const poll = async () => {
      try {
        const res = await api.get(`/crm/sync-jobs/${jobId}`);
        setSyncProgress(res.data);
        
        if (res.data.status === "completed" || res.data.status === "error") {
          // Sync finished
          setSyncing(prev => ({ ...prev, [selectedConnection?.id]: false }));
          fetchConnections();
          
          if (res.data.status === "completed") {
            toast.success("Sincronización completada");
          }
          return; // Stop polling
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // Poll every second
        } else {
          setSyncing(prev => ({ ...prev, [selectedConnection?.id]: false }));
        }
      } catch (error) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Retry with delay
        }
      }
    };
    
    poll();
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
            const crmIconUrl = getIconUrl(`crm_${connection.platform}`);
            return (
              <Card key={connection.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: platform?.color || "#4f46e5" }}
                      >
                        {crmIconUrl ? (
                          <img src={crmIconUrl} alt={platform?.name || connection.platform} className="w-7 h-7 object-contain" />
                        ) : (
                          <Building2 className="w-5 h-5 text-white" />
                        )}
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
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Seleccionar CRM</DialogTitle>
            <DialogDescription>
              Elige el sistema CRM que deseas conectar
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 py-4 max-h-[60vh] overflow-y-auto pr-1">
            {Object.values(CRM_PLATFORMS).map((platform) => {
              const platformIconUrl = getIconUrl(`crm_${platform.id}`);
              return (
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
                  {platformIconUrl ? (
                    <img src={platformIconUrl} alt={platform.name} className="w-9 h-9 object-contain" />
                  ) : (
                    <Building2 className="w-6 h-6 text-white" />
                  )}
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
            );})}
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
                placeholder={`Mi ${selectedPlatform?.name}`}
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

            {/* Odoo specific help */}
            {selectedPlatform?.id === "odoo" && (
              <div className="bg-purple-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-purple-800 mb-1">¿Cómo obtener el API Token?</p>
                <ol className="text-purple-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu Odoo como administrador</li>
                  <li>Ve a Settings (Configuración)</li>
                  <li>Haz clic en "Manage Users" (Gestionar usuarios)</li>
                  <li>Selecciona tu usuario</li>
                  <li>Copia el "Access Token" o genera uno nuevo</li>
                </ol>
              </div>
            )}

            {/* HubSpot specific help */}
            {selectedPlatform?.id === "hubspot" && (
              <div className="bg-orange-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-orange-800 mb-1">¿Cómo obtener el Token de acceso?</p>
                <ol className="text-orange-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu cuenta de HubSpot</li>
                  <li>Ve a Settings → Integrations → Private Apps</li>
                  <li>Crea una nueva Private App o selecciona una existente</li>
                  <li>Asigna los scopes: crm.objects.contacts, crm.objects.deals, crm.objects.line_items</li>
                  <li>Copia el "Access Token" generado</li>
                </ol>
              </div>
            )}

            {/* Salesforce specific help */}
            {selectedPlatform?.id === "salesforce" && (
              <div className="bg-cyan-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-cyan-800 mb-1">¿Cómo configurar Salesforce?</p>
                <ol className="text-cyan-700 space-y-1 list-decimal list-inside">
                  <li>Accede a Salesforce Setup</li>
                  <li>Busca "App Manager" y crea una Connected App</li>
                  <li>Activa OAuth y selecciona los scopes necesarios</li>
                  <li>Copia el Consumer Key (Client ID) y Consumer Secret</li>
                  <li>Genera un Access Token con el flujo OAuth 2.0</li>
                </ol>
              </div>
            )}

            {/* Zoho CRM specific help */}
            {selectedPlatform?.id === "zoho" && (
              <div className="bg-red-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-red-800 mb-1">¿Cómo configurar Zoho CRM?</p>
                <ol className="text-red-700 space-y-1 list-decimal list-inside">
                  <li>Accede a Zoho API Console (api-console.zoho.eu)</li>
                  <li>Crea un "Self Client" o "Server-based Application"</li>
                  <li>Copia el Client ID y Client Secret</li>
                  <li>Genera un Refresh Token con los scopes: ZohoCRM.modules.ALL</li>
                  <li>Selecciona tu dominio API (zohoapis.eu para Europa)</li>
                </ol>
              </div>
            )}

            {/* Pipedrive specific help */}
            {selectedPlatform?.id === "pipedrive" && (
              <div className="bg-green-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-green-800 mb-1">¿Cómo obtener el API Token?</p>
                <ol className="text-green-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu cuenta de Pipedrive</li>
                  <li>Ve a Settings → Personal preferences</li>
                  <li>Selecciona la pestaña "API"</li>
                  <li>Copia tu "Personal API Token"</li>
                </ol>
              </div>
            )}

            {/* Monday CRM specific help */}
            {selectedPlatform?.id === "monday" && (
              <div className="bg-indigo-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-indigo-800 mb-1">¿Cómo configurar Monday CRM?</p>
                <ol className="text-indigo-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu cuenta de Monday.com</li>
                  <li>Ve a tu avatar → Administration → API</li>
                  <li>Copia tu "API Token personal"</li>
                  <li>Para el Board ID, abre el board y cópialo de la URL</li>
                </ol>
              </div>
            )}

            {/* Freshsales specific help */}
            {selectedPlatform?.id === "freshsales" && (
              <div className="bg-orange-50 p-3 rounded-lg text-sm">
                <p className="font-medium text-orange-800 mb-1">¿Cómo obtener la API Key?</p>
                <ol className="text-orange-700 space-y-1 list-decimal list-inside">
                  <li>Accede a tu cuenta de Freshsales</li>
                  <li>Haz clic en tu perfil → Settings</li>
                  <li>Ve a "API Settings"</li>
                  <li>Copia tu "API Key"</li>
                  <li>Tu URL es: https://tu-empresa.myfreshworks.com/crm/sales</li>
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
              Selecciona el catálogo y qué datos sincronizar con {selectedConnection?.name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Catalog Selector - Required */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Catálogo a sincronizar <span className="text-red-500">*</span>
              </Label>
              <Select value={selectedCatalogId} onValueChange={setSelectedCatalogId}>
                <SelectTrigger data-testid="sync-catalog-selector" className={!selectedCatalogId ? "border-amber-300" : ""}>
                  <SelectValue placeholder="Selecciona un catálogo..." />
                </SelectTrigger>
                <SelectContent>
                  {catalogs.length === 0 ? (
                    <div className="p-3 text-sm text-slate-500 text-center">
                      No hay catálogos disponibles
                    </div>
                  ) : (
                    catalogs.map((catalog) => (
                      <SelectItem key={catalog.id} value={catalog.id}>
                        {catalog.name} ({catalog.product_count || 0} productos)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {!selectedCatalogId && (
                <p className="text-xs text-amber-600">
                  Debes seleccionar un catálogo para sincronizar
                </p>
              )}
              {selectedCatalogId && (
                <p className="text-xs text-slate-500">
                  Solo se sincronizarán los productos de este catálogo
                </p>
              )}
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
              disabled={syncing[selectedConnection?.id] || !selectedCatalogId}
              data-testid="start-sync-btn"
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

      {/* Progress Dialog */}
      <Dialog open={showProgressDialog} onOpenChange={(open) => {
        if (!open && syncProgress?.status !== "running") {
          setShowProgressDialog(false);
          setSyncProgress(null);
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              {syncProgress?.status === "completed" ? "Sincronización Completada" : 
               syncProgress?.status === "error" ? "Error en Sincronización" :
               "Sincronizando..."}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Progreso</span>
                <span className="font-medium">{syncProgress?.progress || 0}%</span>
              </div>
              <Progress value={syncProgress?.progress || 0} className="h-3" />
            </div>

            {/* Current Step */}
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm text-slate-600 flex items-center gap-2">
                {syncProgress?.status === "running" && (
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                )}
                {syncProgress?.status === "completed" && (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
                {syncProgress?.status === "error" && (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                {syncProgress?.current_step || "Preparando..."}
              </p>
            </div>

            {/* Stats */}
            {(syncProgress?.total_items > 0 || syncProgress?.created > 0 || syncProgress?.updated > 0) && (
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {syncProgress?.processed_items || 0}/{syncProgress?.total_items || 0}
                  </p>
                  <p className="text-xs text-blue-600">Procesados</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {syncProgress?.created || 0}
                  </p>
                  <p className="text-xs text-green-600">Creados</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-amber-600">
                    {syncProgress?.updated || 0}
                  </p>
                  <p className="text-xs text-amber-600">Actualizados</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {syncProgress?.errors || 0}
                  </p>
                  <p className="text-xs text-red-600">Errores</p>
                </div>
              </div>
            )}

            {/* Error Details Section */}
            {syncProgress?.errors > 0 && syncProgress?.error_details && (
              <div className="border-t pt-4 space-y-2">
                <button
                  onClick={() => setShowErrorDetails(!showErrorDetails)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-red-50 hover:bg-red-100 transition-colors text-red-700 font-medium text-sm"
                >
                  <span>Ver {syncProgress.errors} producto(s) con error</span>
                  {showErrorDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showErrorDetails && (
                  <div className="max-h-48 overflow-y-auto bg-red-50 rounded-lg p-3 space-y-2 text-sm">
                    {Object.entries(syncProgress.error_details).map(([sku, errorMsg]) => (
                      <div key={sku} className="border-l-2 border-red-500 pl-2 py-1">
                        <p className="font-mono text-red-700 font-semibold">{sku}</p>
                        <p className="text-red-600 text-xs">{errorMsg}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button 
              onClick={() => {
                setShowProgressDialog(false);
                setSyncProgress(null);
              }}
              disabled={syncProgress?.status === "running"}
              className={syncProgress?.status === "completed" ? "btn-primary" : ""}
            >
              {syncProgress?.status === "running" ? "Sincronizando..." : "Cerrar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CRMPage;
