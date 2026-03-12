import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
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
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Store, Plus, MoreVertical, Trash2, RefreshCw, ExternalLink, Upload, 
  Wifi, WifiOff, Package, Key, Link2, BookOpen, Settings,
  ShoppingCart, ShoppingBag, Globe, Boxes, Sparkles
} from "lucide-react";

// Platform configurations
const PLATFORMS = {
  woocommerce: {
    id: "woocommerce",
    name: "WooCommerce",
    icon: ShoppingCart,
    color: "bg-purple-100 text-purple-600",
    borderColor: "border-purple-200",
    fields: [
      { key: "store_url", label: "URL de la tienda", type: "url", required: true, placeholder: "https://mitienda.com" },
      { key: "consumer_key", label: "Consumer Key", type: "password", required: true, placeholder: "ck_xxxxxxxxxxxxxxxxxxxxxxxx" },
      { key: "consumer_secret", label: "Consumer Secret", type: "password", required: true, placeholder: "cs_xxxxxxxxxxxxxxxxxxxxxxxx" },
    ],
    helpText: "En WooCommerce → Ajustes → Avanzado → API REST. Crea una clave con permisos de Lectura/Escritura."
  },
  prestashop: {
    id: "prestashop",
    name: "PrestaShop",
    icon: ShoppingBag,
    color: "bg-pink-100 text-pink-600",
    borderColor: "border-pink-200",
    fields: [
      { key: "store_url", label: "URL de la tienda", type: "url", required: true, placeholder: "https://mitienda.com" },
      { key: "api_key", label: "Clave Webservice API", type: "password", required: true, placeholder: "XXXXXXXXXXXXXXXXXXXXXXXXXX" },
    ],
    helpText: "En PrestaShop → Parámetros Avanzados → Webservice. Crea una nueva clave con permisos en productos y stocks."
  },
  shopify: {
    id: "shopify",
    name: "Shopify",
    icon: Boxes,
    color: "bg-green-100 text-green-600",
    borderColor: "border-green-200",
    fields: [
      { key: "store_url", label: "URL de la tienda", type: "url", required: true, placeholder: "mitienda.myshopify.com" },
      { key: "access_token", label: "Admin API Access Token", type: "password", required: true, placeholder: "shpat_xxxxxxxxxxxxxxxxxxxxxxxxxx" },
      { key: "api_version", label: "Versión de API", type: "select", options: ["2024-01", "2024-04", "2024-07", "2024-10"], default: "2024-10" },
    ],
    helpText: "En Shopify Admin → Configuración → Apps → Desarrollar apps. Crea una app personalizada con permisos de productos."
  },
  wix: {
    id: "wix",
    name: "Wix eCommerce",
    icon: Sparkles,
    color: "bg-blue-100 text-blue-600",
    borderColor: "border-blue-200",
    fields: [
      { key: "store_url", label: "URL del sitio", type: "url", required: true, placeholder: "https://mitienda.wixsite.com" },
      { key: "api_key", label: "API Key", type: "password", required: true, placeholder: "IST.xxxxxxxxxxxx" },
      { key: "site_id", label: "Site ID", type: "text", required: true, placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
    ],
    helpText: "En Wix → Configuración del sitio → API Keys. También necesitas el Site ID de tu dashboard."
  },
  magento: {
    id: "magento",
    name: "Magento",
    icon: Globe,
    color: "bg-orange-100 text-orange-600",
    borderColor: "border-orange-200",
    fields: [
      { key: "store_url", label: "URL de la tienda", type: "url", required: true, placeholder: "https://mitienda.com" },
      { key: "access_token", label: "Integration Access Token", type: "password", required: true, placeholder: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
      { key: "store_code", label: "Store Code", type: "text", default: "default", placeholder: "default" },
    ],
    helpText: "En Magento Admin → System → Integrations. Crea una integración y actívala para obtener el Access Token."
  }
};

const StoresPage = () => {
  const [configs, setConfigs] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  const [selectedCatalogProducts, setSelectedCatalogProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPlatformSelector, setShowPlatformSelector] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [formData, setFormData] = useState({});
  const [exportOptions, setExportOptions] = useState({ update_existing: true, catalog_id: "" });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [syncing, setSyncing] = useState({});
  const [exportResult, setExportResult] = useState(null);
  const [loadingCatalogProducts, setLoadingCatalogProducts] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [configsRes, catalogsRes] = await Promise.all([
        api.get("/stores/configs"),
        api.get("/catalogs")
      ]);
      setConfigs(configsRes.data);
      setCatalogs(catalogsRes.data);
      const defaultCatalog = catalogsRes.data.find(c => c.is_default);
      if (defaultCatalog) {
        setExportOptions(prev => ({ ...prev, catalog_id: defaultCatalog.id }));
      } else if (catalogsRes.data.length > 0) {
        setExportOptions(prev => ({ ...prev, catalog_id: catalogsRes.data[0].id }));
      }
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const resetForm = () => {
    setFormData({ name: "", catalog_id: "", auto_sync_enabled: false });
    setSelectedConfig(null);
    setSelectedPlatform(null);
  };

  const openAddStore = () => {
    resetForm();
    setShowPlatformSelector(true);
  };

  const selectPlatform = (platformId) => {
    setSelectedPlatform(PLATFORMS[platformId]);
    setShowPlatformSelector(false);
    
    // Initialize form with platform defaults
    const platform = PLATFORMS[platformId];
    const initialData = { name: "", platform: platformId, catalog_id: "", auto_sync_enabled: false };
    platform.fields.forEach(field => {
      if (field.default) initialData[field.key] = field.default;
    });
    setFormData(initialData);
    setShowDialog(true);
  };

  const openEdit = (config) => {
    setSelectedConfig(config);
    setSelectedPlatform(PLATFORMS[config.platform] || PLATFORMS.woocommerce);
    
    const editData = {
      name: config.name,
      platform: config.platform,
      catalog_id: config.catalog_id || "",
      auto_sync_enabled: config.auto_sync_enabled || false,
      store_url: config.store_url || "",
    };
    // Don't populate sensitive fields for editing
    setFormData(editData);
    setShowDialog(true);
  };

  const openDelete = (config) => {
    setSelectedConfig(config);
    setShowDeleteDialog(true);
  };

  const openExport = async (config) => {
    setSelectedConfig(config);
    setSelectedPlatform(PLATFORMS[config.platform] || PLATFORMS.woocommerce);
    setExportResult(null);
    
    // Determine which catalog to use
    let catalogIdToLoad = exportOptions.catalog_id;
    
    if (!catalogIdToLoad && catalogs.length > 0) {
      const defaultCatalog = catalogs.find(c => c.is_default) || catalogs[0];
      catalogIdToLoad = defaultCatalog.id;
      setExportOptions(prev => ({ ...prev, catalog_id: defaultCatalog.id }));
    }
    
    // Always load products for the selected catalog
    if (catalogIdToLoad) {
      setLoadingCatalogProducts(true);
      try {
        const res = await api.get(`/catalogs/${catalogIdToLoad}/products?active_only=true`);
        setSelectedCatalogProducts(res.data);
      } catch (error) {
        console.error("Error loading catalog products:", error);
        setSelectedCatalogProducts([]);
      } finally {
        setLoadingCatalogProducts(false);
      }
    }
    
    setShowExportDialog(true);
  };

  const handleCatalogChange = async (catalogId) => {
    setExportOptions(prev => ({ ...prev, catalog_id: catalogId }));
    setLoadingCatalogProducts(true);
    try {
      const res = await api.get(`/catalogs/${catalogId}/products?active_only=true`);
      setSelectedCatalogProducts(res.data);
    } catch (error) {
      console.error("Error loading catalog products:", error);
    } finally {
      setLoadingCatalogProducts(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name?.trim() || !formData.store_url?.trim()) {
      toast.error("Nombre y URL son obligatorios");
      return;
    }

    // Validate required fields for new stores
    if (!selectedConfig && selectedPlatform) {
      const missingRequired = selectedPlatform.fields
        .filter(f => f.required && !formData[f.key])
        .map(f => f.label);
      if (missingRequired.length > 0) {
        toast.error(`Campos obligatorios: ${missingRequired.join(", ")}`);
        return;
      }
    }

    setSaving(true);
    try {
      const payload = { ...formData };
      
      // Remove empty credential fields when editing
      if (selectedConfig) {
        selectedPlatform?.fields.forEach(field => {
          if (field.type === "password" && !payload[field.key]) {
            delete payload[field.key];
          }
        });
      }

      if (selectedConfig) {
        await api.put(`/stores/configs/${selectedConfig.id}`, payload);
        toast.success("Tienda actualizada");
      } else {
        await api.post("/stores/configs", payload);
        toast.success("Tienda añadida correctamente");
      }
      setShowDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/stores/configs/${selectedConfig.id}`);
      toast.success("Tienda eliminada");
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleSyncPriceStock = async (config) => {
    setSyncing(prev => ({ ...prev, [config.id]: true }));
    try {
      const res = await api.post(`/stores/configs/${config.id}/sync`);
      if (res.data.status === "success") {
        toast.success(res.data.message);
        fetchData();
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al sincronizar");
    } finally {
      setSyncing(prev => ({ ...prev, [config.id]: false }));
    }
  };

  const handleTestConnection = async (config) => {
    setTesting(true);
    try {
      const res = await api.post(`/stores/configs/${config.id}/test`);
      if (res.data.status === "success") {
        toast.success(`Conexión exitosa: ${res.data.store_name || config.name}`);
        fetchData();
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error("Error al probar conexión");
    } finally {
      setTesting(false);
    }
  };

  const handleExport = async () => {
    if (!selectedConfig || !exportOptions.catalog_id) {
      toast.error("Selecciona un catálogo para exportar");
      return;
    }
    
    setExporting(true);
    setExportResult(null);
    
    try {
      const payload = {
        config_id: selectedConfig.id,
        update_existing: exportOptions.update_existing,
        catalog_id: exportOptions.catalog_id
      };
      
      const res = await api.post("/stores/export", payload);
      setExportResult(res.data);
      
      if (res.data.status === "success") {
        toast.success(`Exportación completada: ${res.data.created} creados, ${res.data.updated} actualizados`);
      } else if (res.data.status === "partial") {
        toast.warning(`Exportación parcial: ${res.data.failed} errores`);
      } else {
        toast.error("Error en la exportación");
      }
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al exportar");
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    return new Date(dateStr).toLocaleString("es-ES", {
      day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  };

  const getPlatformIcon = (platformId) => {
    const platform = PLATFORMS[platformId];
    return platform ? platform.icon : Store;
  };

  const getPlatformColor = (platformId) => {
    const platform = PLATFORMS[platformId];
    return platform ? platform.color : "bg-slate-100 text-slate-600";
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
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Tiendas Online
          </h1>
          <p className="text-slate-500">
            Conecta tus tiendas eCommerce y sincroniza productos automáticamente
          </p>
        </div>
        <Button onClick={openAddStore} className="btn-primary" data-testid="add-store-btn">
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Añadir Tienda
        </Button>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {Object.values(PLATFORMS).map(platform => {
          const Icon = platform.icon;
          const count = configs.filter(c => c.platform === platform.id).length;
          return (
            <Card key={platform.id} className={`border-slate-200 ${count > 0 ? platform.borderColor : ""}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">{platform.name}</p>
                    <p className="text-2xl font-bold text-slate-900">{count}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${platform.color}`}>
                    <Icon className="w-5 h-5" strokeWidth={1.5} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Configs Table */}
      {configs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Store className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay tiendas configuradas
          </h3>
          <p className="text-slate-500 mb-4">
            Añade tu primera tienda para comenzar a sincronizar productos
          </p>
          <Button onClick={openAddStore} className="btn-primary">
            <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Añadir Tienda
          </Button>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Tienda</TableHead>
                  <TableHead>Plataforma</TableHead>
                  <TableHead>Catálogo Asociado</TableHead>
                  <TableHead className="text-center">Estado</TableHead>
                  <TableHead className="text-right">Productos</TableHead>
                  <TableHead>Última Sync</TableHead>
                  <TableHead className="w-[180px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {configs.map((config) => {
                  const PlatformIcon = getPlatformIcon(config.platform);
                  const platformColor = getPlatformColor(config.platform);
                  const platform = PLATFORMS[config.platform];
                  
                  return (
                    <TableRow key={config.id} className="table-row" data-testid={`store-config-${config.id}`}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${platformColor}`}>
                            <PlatformIcon className="w-5 h-5" strokeWidth={1.5} />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{config.name}</p>
                            <a 
                              href={config.store_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                            >
                              {config.store_url?.replace(/^https?:\/\//, '').slice(0, 30)}
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${platformColor} border-0`}>
                          {platform?.name || config.platform}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {config.catalog_name ? (
                          <Badge className="bg-indigo-100 text-indigo-700 border-0">
                            <BookOpen className="w-3 h-3 mr-1" />
                            {config.catalog_name}
                          </Badge>
                        ) : (
                          <span className="text-sm text-slate-400">No configurado</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {config.is_connected ? (
                          <Badge className="bg-emerald-100 text-emerald-700 border-0">
                            <Wifi className="w-3 h-3 mr-1" />
                            Conectado
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-slate-500">
                            <WifiOff className="w-3 h-3 mr-1" />
                            Sin probar
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {config.products_synced || 0}
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">
                        {formatDate(config.last_sync)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleSyncPriceStock(config)}
                            disabled={!config.catalog_id || syncing[config.id]}
                            className="btn-secondary"
                            title="Sincronizar precio y stock"
                            data-testid={`sync-btn-${config.id}`}
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${syncing[config.id] ? "animate-spin" : ""}`} />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => openExport(config)}
                            className="btn-primary"
                            disabled={catalogs.length === 0}
                            data-testid={`export-btn-${config.id}`}
                          >
                            <Upload className="w-3.5 h-3.5 mr-1" />
                            Exportar
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleTestConnection(config)} disabled={testing}>
                                <Wifi className="w-4 h-4 mr-2" strokeWidth={1.5} />
                                Probar Conexión
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => openEdit(config)}>
                                <Settings className="w-4 h-4 mr-2" strokeWidth={1.5} />
                                Configurar
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                onClick={() => openDelete(config)}
                                className="text-rose-600 focus:text-rose-600"
                              >
                                <Trash2 className="w-4 h-4 mr-2" strokeWidth={1.5} />
                                Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Platform Selector Dialog */}
      <Dialog open={showPlatformSelector} onOpenChange={setShowPlatformSelector}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Store className="w-5 h-5 text-indigo-600" />
              Seleccionar Plataforma
            </DialogTitle>
            <DialogDescription>
              Elige el tipo de tienda que deseas conectar
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 py-4">
            {Object.values(PLATFORMS).map(platform => {
              const Icon = platform.icon;
              return (
                <button
                  key={platform.id}
                  onClick={() => selectPlatform(platform.id)}
                  className={`p-4 rounded-lg border-2 ${platform.borderColor} hover:shadow-md transition-all duration-200 text-left group`}
                  data-testid={`select-platform-${platform.id}`}
                >
                  <div className={`w-12 h-12 rounded-lg ${platform.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6" strokeWidth={1.5} />
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-1">{platform.name}</h3>
                  <p className="text-xs text-slate-500">{platform.helpText?.slice(0, 50)}...</p>
                </button>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Store Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {selectedPlatform && (
                <div className={`w-8 h-8 rounded-lg ${selectedPlatform.color} flex items-center justify-center`}>
                  <selectedPlatform.icon className="w-4 h-4" />
                </div>
              )}
              {selectedConfig ? `Editar ${selectedPlatform?.name || "Tienda"}` : `Nueva Tienda ${selectedPlatform?.name || ""}`}
            </DialogTitle>
            <DialogDescription>
              {selectedPlatform?.helpText}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la tienda *</Label>
              <Input
                id="name"
                value={formData.name || ""}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Mi Tienda Online"
                className="input-base"
                data-testid="store-name-input"
              />
            </div>

            {/* Platform-specific fields */}
            {selectedPlatform?.fields.map(field => (
              <div key={field.key} className="space-y-2">
                <Label htmlFor={field.key}>
                  {field.label} {field.required && !selectedConfig && "*"}
                </Label>
                {field.type === "select" ? (
                  <Select
                    value={formData[field.key] || field.default || ""}
                    onValueChange={(val) => setFormData({ ...formData, [field.key]: val })}
                  >
                    <SelectTrigger className="input-base" data-testid={`store-${field.key}-select`}>
                      <SelectValue placeholder={`Seleccionar ${field.label}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options?.filter(Boolean).map(opt => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="relative">
                    {field.type === "url" && (
                      <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    )}
                    {field.type === "password" && (
                      <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    )}
                    <Input
                      id={field.key}
                      type={field.type === "url" ? "text" : field.type}
                      value={formData[field.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                      placeholder={selectedConfig && field.type === "password" ? "Dejar vacío para mantener actual" : field.placeholder}
                      className={`input-base ${(field.type === "url" || field.type === "password") ? "pl-9" : ""} ${field.type === "password" ? "font-mono" : ""}`}
                      data-testid={`store-${field.key}-input`}
                    />
                  </div>
                )}
              </div>
            ))}

            {/* Sync Configuration */}
            <div className="border-t border-slate-200 pt-4 mt-4">
              <p className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-indigo-600" strokeWidth={1.5} />
                Configuración de Sincronización
              </p>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="catalog_id">Catálogo para sincronización *</Label>
                  <Select
                    value={formData.catalog_id || "none"}
                    onValueChange={(val) => setFormData({ ...formData, catalog_id: val === "none" ? "" : val })}
                  >
                    <SelectTrigger className="input-base" data-testid="store-catalog-select">
                      <BookOpen className="w-4 h-4 mr-2 text-slate-400" />
                      <SelectValue placeholder="Selecciona un catálogo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sin catálogo</SelectItem>
                      {catalogs.map(catalog => (
                        <SelectItem key={catalog.id} value={catalog.id}>
                          {catalog.name} ({catalog.product_count} productos)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    Selecciona el catálogo que se exportará a esta tienda
                  </p>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="store-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : selectedConfig ? "Guardar Cambios" : "Añadir Tienda"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Upload className="w-5 h-5 text-indigo-600" />
              Exportar a {selectedConfig?.name}
            </DialogTitle>
            <DialogDescription>
              Selecciona el catálogo y configura las opciones de exportación
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Catálogo a exportar</Label>
              <Select value={exportOptions.catalog_id} onValueChange={handleCatalogChange}>
                <SelectTrigger className="input-base">
                  <BookOpen className="w-4 h-4 mr-2 text-slate-400" />
                  <SelectValue placeholder="Selecciona un catálogo" />
                </SelectTrigger>
                <SelectContent>
                  {catalogs.map(catalog => (
                    <SelectItem key={catalog.id} value={catalog.id}>
                      {catalog.name} ({catalog.product_count} productos)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">Actualizar productos existentes</p>
                <p className="text-sm text-slate-500">Actualiza productos con el mismo SKU</p>
              </div>
              <Switch
                checked={exportOptions.update_existing}
                onCheckedChange={(checked) => setExportOptions({ ...exportOptions, update_existing: checked })}
              />
            </div>
            
            <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
              <div className="flex items-center gap-2 mb-2">
                <Package className="w-4 h-4 text-indigo-600" />
                <p className="font-medium text-indigo-900">Productos a exportar</p>
              </div>
              {loadingCatalogProducts ? (
                <div className="flex items-center gap-2 text-sm text-indigo-700">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Cargando productos...
                </div>
              ) : (
                <p className="text-sm text-indigo-700">
                  Se exportarán <strong>{selectedCatalogProducts.length}</strong> productos
                </p>
              )}
            </div>
            
            {exportResult && (
              <div className={`p-4 rounded-lg border ${
                exportResult.status === 'success' ? 'bg-emerald-50 border-emerald-200' :
                exportResult.status === 'partial' ? 'bg-amber-50 border-amber-200' :
                'bg-rose-50 border-rose-200'
              }`}>
                <p className="font-medium mb-2">Resultado:</p>
                <div className="grid grid-cols-3 gap-4 text-center mb-3">
                  <div>
                    <p className="text-2xl font-bold text-emerald-600">{exportResult.created}</p>
                    <p className="text-xs text-slate-600">Creados</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-indigo-600">{exportResult.updated}</p>
                    <p className="text-xs text-slate-600">Actualizados</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-rose-600">{exportResult.failed}</p>
                    <p className="text-xs text-slate-600">Errores</p>
                  </div>
                </div>
                {exportResult.errors?.length > 0 && (
                  <div className="mt-2 border-t border-rose-200 pt-2">
                    <p className="text-xs font-semibold text-rose-700 mb-1">Detalle de errores:</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {exportResult.errors.map((err, i) => (
                        <p key={i} className="text-xs text-rose-600 font-mono bg-rose-100 px-2 py-1 rounded break-all">{err}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExportDialog(false)} className="btn-secondary">
              {exportResult ? "Cerrar" : "Cancelar"}
            </Button>
            {!exportResult && (
              <Button 
                onClick={handleExport} 
                disabled={exporting || !exportOptions.catalog_id || selectedCatalogProducts.length === 0} 
                className="btn-primary"
                data-testid="confirm-export-btn"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Exportando...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Iniciar Exportación
                  </>
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar tienda?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la configuración de "{selectedConfig?.name}". Esta acción no se puede deshacer.
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

export default StoresPage;
