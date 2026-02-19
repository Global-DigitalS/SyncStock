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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  ShoppingCart,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  RefreshCw,
  Check,
  X,
  ExternalLink,
  Upload,
  Wifi,
  WifiOff,
  Store,
  Package,
  Key,
  Link2,
  BookOpen
} from "lucide-react";

const WooCommerceExport = () => {
  const [configs, setConfigs] = useState([]);
  const [catalogs, setCatalogs] = useState([]);
  const [selectedCatalogProducts, setSelectedCatalogProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    store_url: "",
    consumer_key: "",
    consumer_secret: ""
  });
  const [exportOptions, setExportOptions] = useState({
    update_existing: true,
    catalog_id: ""
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const [loadingCatalogProducts, setLoadingCatalogProducts] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [configsRes, catalogsRes] = await Promise.all([
        api.get("/woocommerce/configs"),
        api.get("/catalogs")
      ]);
      setConfigs(configsRes.data);
      setCatalogs(catalogsRes.data);
      
      // Set default catalog
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
    setFormData({
      name: "",
      store_url: "",
      consumer_key: "",
      consumer_secret: ""
    });
    setSelectedConfig(null);
  };

  const openEdit = (config) => {
    setSelectedConfig(config);
    setFormData({
      name: config.name,
      store_url: config.store_url,
      consumer_key: "",
      consumer_secret: ""
    });
    setShowDialog(true);
  };

  const openDelete = (config) => {
    setSelectedConfig(config);
    setShowDeleteDialog(true);
  };

  const openExport = async (config) => {
    setSelectedConfig(config);
    setExportResult(null);
    
    // Set default catalog if not set
    if (!exportOptions.catalog_id && catalogs.length > 0) {
      const defaultCatalog = catalogs.find(c => c.is_default) || catalogs[0];
      setExportOptions(prev => ({ ...prev, catalog_id: defaultCatalog.id }));
      
      // Load products for default catalog
      setLoadingCatalogProducts(true);
      try {
        const res = await api.get(`/catalogs/${defaultCatalog.id}/products?active_only=true`);
        setSelectedCatalogProducts(res.data);
      } catch (error) {
        console.error("Error loading catalog products:", error);
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
    if (!formData.name.trim() || !formData.store_url.trim()) {
      toast.error("Nombre y URL son obligatorios");
      return;
    }

    if (!selectedConfig && (!formData.consumer_key || !formData.consumer_secret)) {
      toast.error("Las credenciales API son obligatorias");
      return;
    }

    setSaving(true);
    try {
      const payload = { ...formData };
      if (selectedConfig && !formData.consumer_key) {
        delete payload.consumer_key;
      }
      if (selectedConfig && !formData.consumer_secret) {
        delete payload.consumer_secret;
      }

      if (selectedConfig) {
        await api.put(`/woocommerce/configs/${selectedConfig.id}`, payload);
        toast.success("Configuración actualizada");
      } else {
        await api.post("/woocommerce/configs", payload);
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
      await api.delete(`/woocommerce/configs/${selectedConfig.id}`);
      toast.success("Configuración eliminada");
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleTestConnection = async (config) => {
    setTesting(true);
    try {
      const res = await api.post(`/woocommerce/configs/${config.id}/test`);
      if (res.data.status === "success") {
        toast.success(`Conexión exitosa: ${res.data.store_name}`);
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
      
      const res = await api.post("/woocommerce/export", payload);
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
            Exportar a WooCommerce
          </h1>
          <p className="text-slate-500">
            Conecta tus tiendas WooCommerce y exporta productos directamente vía API REST
          </p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowDialog(true); }} 
          className="btn-primary"
          data-testid="add-woo-config-btn"
        >
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Añadir Tienda
        </Button>
      </div>

      {/* Info Card */}
      <Card className="border-indigo-200 bg-indigo-50 mb-6">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <ShoppingCart className="w-5 h-5 text-indigo-600 mt-0.5" strokeWidth={1.5} />
            <div>
              <p className="text-sm font-medium text-indigo-900 mb-1">¿Cómo obtener las credenciales API?</p>
              <p className="text-sm text-indigo-700">
                En tu panel de WordPress, ve a <strong>WooCommerce → Ajustes → Avanzado → API REST</strong>. 
                Crea una nueva clave con permisos de <strong>Lectura/Escritura</strong> y copia el Consumer Key y Consumer Secret.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Tiendas Conectadas</p>
                <p className="text-2xl font-bold text-slate-900">
                  {configs.filter(c => c.is_connected).length}
                </p>
              </div>
              <Store className="w-8 h-8 text-indigo-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Configuraciones</p>
                <p className="text-2xl font-bold text-slate-900">{configs.length}</p>
              </div>
              <Key className="w-8 h-8 text-slate-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Catálogos Disponibles</p>
                <p className="text-2xl font-bold text-emerald-700">{catalogs.length}</p>
              </div>
              <BookOpen className="w-8 h-8 text-emerald-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Productos Sincronizados</p>
                <p className="text-2xl font-bold text-slate-900">
                  {configs.reduce((sum, c) => sum + (c.products_synced || 0), 0)}
                </p>
              </div>
              <Upload className="w-8 h-8 text-slate-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Configs Table */}
      {configs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <ShoppingCart className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay tiendas configuradas
          </h3>
          <p className="text-slate-500 mb-4">
            Añade tu primera tienda WooCommerce para comenzar a exportar productos
          </p>
          <Button onClick={() => { resetForm(); setShowDialog(true); }} className="btn-primary">
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
                  <TableHead>URL</TableHead>
                  <TableHead className="text-center">Estado</TableHead>
                  <TableHead className="text-right">Productos</TableHead>
                  <TableHead>Última Sync</TableHead>
                  <TableHead className="w-[120px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {configs.map((config) => (
                  <TableRow key={config.id} className="table-row" data-testid={`woo-config-${config.id}`}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                          <ShoppingCart className="w-5 h-5 text-purple-600" strokeWidth={1.5} />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{config.name}</p>
                          <p className="text-xs text-slate-500 font-mono">{config.consumer_key_masked}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <a 
                        href={config.store_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-sm"
                      >
                        {config.store_url.replace(/^https?:\/\//, '').slice(0, 30)}
                        <ExternalLink className="w-3 h-3" />
                      </a>
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
                      {config.last_sync 
                        ? new Date(config.last_sync).toLocaleDateString('es-ES', { 
                            day: '2-digit', 
                            month: 'short', 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })
                        : "Nunca"
                      }
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
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
                              <Pencil className="w-4 h-4 mr-2" strokeWidth={1.5} />
                              Editar
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
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <ShoppingCart className="w-5 h-5 text-purple-600" />
              {selectedConfig ? "Editar Tienda" : "Nueva Tienda WooCommerce"}
            </DialogTitle>
            <DialogDescription>
              Introduce las credenciales de la API REST de tu tienda WooCommerce
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la tienda *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Mi Tienda Online"
                className="input-base"
                data-testid="woo-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="store_url">URL de la tienda *</Label>
              <div className="relative">
                <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  id="store_url"
                  value={formData.store_url}
                  onChange={(e) => setFormData({ ...formData, store_url: e.target.value })}
                  placeholder="https://mitienda.com"
                  className="input-base pl-9"
                  data-testid="woo-url-input"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="consumer_key">
                Consumer Key {!selectedConfig && "*"}
              </Label>
              <Input
                id="consumer_key"
                type="password"
                value={formData.consumer_key}
                onChange={(e) => setFormData({ ...formData, consumer_key: e.target.value })}
                placeholder={selectedConfig ? "Dejar vacío para mantener actual" : "ck_xxxxxxxxxxxxxxxxxxxxxxxx"}
                className="input-base font-mono"
                data-testid="woo-key-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="consumer_secret">
                Consumer Secret {!selectedConfig && "*"}
              </Label>
              <Input
                id="consumer_secret"
                type="password"
                value={formData.consumer_secret}
                onChange={(e) => setFormData({ ...formData, consumer_secret: e.target.value })}
                placeholder={selectedConfig ? "Dejar vacío para mantener actual" : "cs_xxxxxxxxxxxxxxxxxxxxxxxx"}
                className="input-base font-mono"
                data-testid="woo-secret-input"
              />
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="woo-submit-btn">
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
              Configura las opciones de exportación para tu tienda WooCommerce
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">Actualizar productos existentes</p>
                <p className="text-sm text-slate-500">Actualiza productos con el mismo SKU en lugar de crear duplicados</p>
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
              <p className="text-sm text-indigo-700">
                Se exportarán <strong>{catalogItems.length}</strong> productos activos de tu catálogo
              </p>
            </div>
            
            {exportResult && (
              <div className={`p-4 rounded-lg border ${
                exportResult.status === 'success' ? 'bg-emerald-50 border-emerald-200' :
                exportResult.status === 'partial' ? 'bg-amber-50 border-amber-200' :
                'bg-rose-50 border-rose-200'
              }`}>
                <p className="font-medium mb-2">Resultado de la exportación:</p>
                <div className="grid grid-cols-3 gap-4 text-center mb-2">
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
                {exportResult.errors.length > 0 && (
                  <div className="mt-2 text-xs text-rose-700">
                    {exportResult.errors.slice(0, 3).map((err, i) => (
                      <p key={i}>• {err}</p>
                    ))}
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
                disabled={exporting || catalogItems.length === 0} 
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
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar configuración?</AlertDialogTitle>
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

export default WooCommerceExport;
