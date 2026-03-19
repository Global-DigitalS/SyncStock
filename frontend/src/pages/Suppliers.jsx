import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
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
  Plus,
  RefreshCw,
  Settings,
  Database,
  Link2,
  Columns,
  Globe,
  ExternalLink,
  Wifi
} from "lucide-react";
import ColumnMappingDialog from "../components/ColumnMappingDialog";
import {
  SupplierTable,
  FtpFileBrowser,
  FtpConnectionStatus,
  ConnectionTypeSelector,
  SupplierPresetSelector,
  ROLE_LABELS
} from "../components/suppliers";

const defaultFormData = {
  name: "",
  description: "",
  connection_type: "ftp",
  file_url: "",
  url_username: "",
  url_password: "",
  ftp_schema: "ftp",
  ftp_host: "",
  ftp_user: "",
  ftp_password: "",
  ftp_port: 21,
  ftp_path: "",
  ftp_mode: "passive",
  file_format: "csv",
  csv_separator: ";",
  csv_enclosure: '"',
  csv_line_break: "\\n",
  csv_header_row: 1,
  column_mapping: null,
  strip_ean_quotes: false,
  preset_id: null
};

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showMappingDialog, setShowMappingDialog] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [formData, setFormData] = useState(defaultFormData);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("general");
  const [mappingSupplier, setMappingSupplier] = useState(null);
  
  // FTP Browser state
  const [ftpFiles, setFtpFiles] = useState([]);
  const [ftpBrowsing, setFtpBrowsing] = useState(false);
  const [ftpCurrentPath, setFtpCurrentPath] = useState("/");
  const [selectedFtpFiles, setSelectedFtpFiles] = useState([]);
  const [ftpConnectionStatus, setFtpConnectionStatus] = useState(null);
  const [ftpTestingConnection, setFtpTestingConnection] = useState(false);
  const [ftpStats, setFtpStats] = useState(null);
  const [ftpListingAll, setFtpListingAll] = useState(false);

  const fetchSuppliers = useCallback(async () => {
    try {
      const res = await api.get("/suppliers");
      setSuppliers(res.data);
    } catch (error) {
      toast.error("Error al cargar los proveedores");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);

  const resetForm = () => {
    setFormData(defaultFormData);
    setSelectedSupplier(null);
    setActiveTab("general");
    setSelectedFtpFiles([]);
    setFtpFiles([]);
    setFtpCurrentPath("/");
    setFtpConnectionStatus(null);
    setFtpStats(null);
  };

  const openCreate = () => {
    resetForm();
    setShowDialog(true);
  };

  const openEdit = (supplier) => {
    setSelectedSupplier(supplier);
    setFormData({
      name: supplier.name || "",
      description: supplier.description || "",
      connection_type: supplier.connection_type || "ftp",
      file_url: supplier.file_url || "",
      url_username: supplier.url_username || "",
      url_password: "",
      ftp_schema: supplier.ftp_schema || "ftp",
      ftp_host: supplier.ftp_host || "",
      ftp_user: supplier.ftp_user || "",
      ftp_password: "",
      ftp_port: supplier.ftp_port || 21,
      ftp_path: supplier.ftp_path || "",
      ftp_mode: supplier.ftp_mode || "passive",
      file_format: supplier.file_format || "csv",
      csv_separator: supplier.csv_separator || ";",
      csv_enclosure: supplier.csv_enclosure || '"',
      csv_line_break: supplier.csv_line_break || "\\n",
      csv_header_row: supplier.csv_header_row || 1,
      column_mapping: supplier.column_mapping || null,
      strip_ean_quotes: supplier.strip_ean_quotes || false,
      preset_id: supplier.preset_id || null
    });
    setSelectedFtpFiles(supplier.ftp_paths || []);
    setShowDialog(true);
  };

  const openMapping = async (supplier) => {
    setMappingSupplier(supplier);
    setShowMappingDialog(true);
    
    try {
      const res = await api.post(`/suppliers/${supplier.id}/preview-file`);
      if (res.data.status === "success") {
        setMappingSupplier({
          ...supplier,
          detected_columns: res.data.columns,
          suggested_mapping: res.data.suggested_mapping
        });
        toast.success(`${res.data.columns.length} columnas detectadas automáticamente`);
      }
    } catch (error) {
      console.log("Could not load preview:", error.response?.data?.detail);
    }
  };

  const openDelete = (supplier) => {
    setSelectedSupplier(supplier);
    setShowDeleteDialog(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error("El nombre es obligatorio");
      return;
    }

    setSaving(true);

    const payload = {
      ...formData,
      ftp_port: parseInt(formData.ftp_port) || 21,
      csv_header_row: parseInt(formData.csv_header_row) >= 0 ? parseInt(formData.csv_header_row) : 1,
      ftp_paths: selectedFtpFiles.length > 0 ? selectedFtpFiles : null
    };

    try {
      let supplierId;
      let hasColumnMapping;

      if (selectedSupplier) {
        await api.put(`/suppliers/${selectedSupplier.id}`, payload);
        toast.success("Proveedor actualizado");
        supplierId = selectedSupplier.id;
        hasColumnMapping = !!payload.column_mapping;
      } else {
        const res = await api.post("/suppliers", payload);
        toast.success("Proveedor creado");
        supplierId = res.data.id;
        hasColumnMapping = !!payload.column_mapping;
      }

      setShowDialog(false);
      resetForm();
      fetchSuppliers();

      // Trigger sync + auto column mapping in background
      const canSync =
        (payload.connection_type === "url" && payload.file_url) ||
        (payload.connection_type !== "url" &&
          (payload.ftp_host || (payload.ftp_paths && payload.ftp_paths.length > 0)));

      if (canSync) {
        toast.info("Sincronizando catálogo...");
        api.post(`/suppliers/${supplierId}/sync`)
          .then(async (res) => {
            const d = res.data;
            if (d.status === "queued") {
              toast.info(d.message || "Sincronización iniciada en segundo plano");
              fetchSuppliers();
              return;
            }
            if (d.status === "error") {
              toast.error(`Error en sincronización: ${d.message}`);
              return;
            }
            toast.success(
              `Sincronización completada: ${d.imported ?? 0} importados, ${d.updated ?? 0} actualizados`
            );
            fetchSuppliers();

            // Auto-detect and save column mapping if none configured
            if (!hasColumnMapping) {
              try {
                const preview = await api.post(`/suppliers/${supplierId}/preview-file`);
                if (
                  preview.data.status === "success" &&
                  preview.data.suggested_mapping &&
                  Object.keys(preview.data.suggested_mapping).length > 0
                ) {
                  await api.put(`/suppliers/${supplierId}`, {
                    column_mapping: preview.data.suggested_mapping
                  });
                  toast.success(
                    `Mapeo automático: ${Object.keys(preview.data.suggested_mapping).length} campos detectados`
                  );
                  fetchSuppliers();
                }
              } catch (_) {
                // preview-file may fail for multi-file; ignore silently
              }
            }
          })
          .catch((err) => {
            toast.error(err.response?.data?.detail || "Error al sincronizar el catálogo");
          });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMapping = async (mapping) => {
    if (!mappingSupplier) return;
    
    setSaving(true);
    try {
      await api.put(`/suppliers/${mappingSupplier.id}`, { column_mapping: mapping });
      toast.success("Mapeo de columnas guardado");
      setShowMappingDialog(false);
      setMappingSupplier(null);
      fetchSuppliers();
    } catch (error) {
      toast.error("Error al guardar el mapeo");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/suppliers/${selectedSupplier.id}`);
      toast.success("Proveedor eliminado");
      setShowDeleteDialog(false);
      setSelectedSupplier(null);
      fetchSuppliers();
    } catch (error) {
      toast.error("Error al eliminar el proveedor");
    }
  };

  // FTP Functions
  const guessFileRole = (name) => {
    const n = name.toLowerCase();
    if (n.includes('stock')) return 'stock';
    if (n.includes('price') && !n.includes('qb')) return 'prices';
    if (n.includes('qb')) return 'prices_qb';
    if (n.includes('product')) return 'products';
    if (n.includes('kit')) return 'kit';
    if (n.includes('minqty')) return 'min_qty';
    if (n.endsWith('.zip')) return 'products';
    return 'products';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const handleFtpBrowse = async (path = "/") => {
    if (!formData.ftp_host) {
      toast.error("Configura el host FTP primero");
      return;
    }
    setFtpBrowsing(true);
    try {
      const res = await api.post("/suppliers/ftp-browse", {
        ftp_schema: formData.ftp_schema || "ftp",
        ftp_host: formData.ftp_host,
        ftp_user: formData.ftp_user,
        ftp_password: formData.ftp_password || "",
        ftp_port: parseInt(formData.ftp_port) || 21,
        ftp_mode: formData.ftp_mode || "passive",
        path,
        supplier_id: selectedSupplier?.id || null
      });
      if (res.data.status === "ok") {
        setFtpFiles(res.data.files);
        setFtpCurrentPath(res.data.path);
        setFtpStats(res.data.stats);
        
        // Auto-select on first browse
        if (path === "/" && selectedFtpFiles.length === 0) {
          const autoSelected = [];
          const files = res.data.files.filter(f => !f.is_dir);
          
          const stockFile = files.find(f => f.name.toLowerCase().includes('stock') && !f.name.endsWith('.zip'));
          if (stockFile) {
            autoSelected.push({
              path: stockFile.path, role: 'stock', label: stockFile.name,
              separator: ";", header_row: 1, merge_key: null
            });
          }
          
          const zips = files.filter(f => f.name.toLowerCase().endsWith('.zip'));
          if (zips.length > 0) {
            const sorted = [...zips].sort((a, b) => b.name.localeCompare(a.name));
            const latestZip = sorted[0];
            autoSelected.push({
              path: latestZip.path, role: 'products', label: latestZip.name,
              separator: ";", header_row: 1, merge_key: null, auto_latest: true
            });
          }
          
          if (autoSelected.length > 0) {
            setSelectedFtpFiles(autoSelected);
            toast.success(`Auto-seleccionados ${autoSelected.length} archivos (ZIP más reciente + Stock)`);
          }
        }
      } else {
        toast.error(res.data.message || "Error al explorar FTP");
        setFtpConnectionStatus({ connected: false, message: res.data.message });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error conectando al FTP");
      setFtpConnectionStatus({ connected: false, message: error.response?.data?.detail || "Error de conexión" });
    } finally {
      setFtpBrowsing(false);
    }
  };

  const handleFtpTestConnection = async () => {
    if (!formData.ftp_host) {
      toast.error("Introduce el host FTP");
      return;
    }
    
    setFtpTestingConnection(true);
    setFtpConnectionStatus(null);
    
    try {
      const res = await api.post("/suppliers/ftp-test", {
        ftp_schema: formData.ftp_schema || "ftp",
        ftp_host: formData.ftp_host,
        ftp_user: formData.ftp_user,
        ftp_password: formData.ftp_password || "",
        ftp_port: parseInt(formData.ftp_port) || 21,
        ftp_mode: formData.ftp_mode || "passive",
        supplier_id: selectedSupplier?.id || null
      });
      
      setFtpConnectionStatus(res.data);
      
      if (res.data.connected) {
        toast.success(res.data.message);
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      setFtpConnectionStatus({ 
        connected: false, 
        message: error.response?.data?.detail || "Error de conexión" 
      });
      toast.error("Error al probar la conexión");
    } finally {
      setFtpTestingConnection(false);
    }
  };

  const handleFtpListAllFiles = async () => {
    if (!selectedSupplier?.id) {
      toast.error("Guarda el proveedor primero para usar esta función");
      return;
    }
    
    setFtpListingAll(true);
    
    try {
      const res = await api.post(`/suppliers/${selectedSupplier.id}/ftp-list-all`, {
        path: ftpCurrentPath,
        max_depth: 2
      });
      
      if (res.data.status === "ok" && res.data.files.length > 0) {
        toast.success(`Encontrados ${res.data.total_files} archivos soportados`);
        
        const newFiles = res.data.files.map(f => ({
          path: f.path,
          role: guessFileRole(f.name),
          label: f.name,
          separator: ";",
          header_row: 1,
          merge_key: null,
          size: f.size_formatted
        }));
        
        const existingPaths = new Set(selectedFtpFiles.map(f => f.path));
        const toAdd = newFiles.filter(f => !existingPaths.has(f.path));
        
        if (toAdd.length > 0) {
          setSelectedFtpFiles(prev => [...prev, ...toAdd]);
          toast.success(`Añadidos ${toAdd.length} archivos nuevos`);
        } else {
          toast.info("Todos los archivos ya están seleccionados");
        }
      } else if (res.data.total_files === 0) {
        toast.info("No se encontraron archivos soportados en esta carpeta");
      } else {
        toast.error(res.data.message || "Error al listar archivos");
      }
    } catch (error) {
      toast.error("Error al listar archivos");
    } finally {
      setFtpListingAll(false);
    }
  };

  const addFtpFile = (file) => {
    if (selectedFtpFiles.some(f => f.path === file.path)) return;
    const role = guessFileRole(file.name);
    setSelectedFtpFiles(prev => [...prev, {
      path: file.path, role, label: file.name,
      separator: ";", header_row: 1, merge_key: null
    }]);
  };

  const removeFtpFile = (path) => {
    setSelectedFtpFiles(prev => prev.filter(f => f.path !== path));
  };

  const updateFtpFileRole = (path, role) => {
    setSelectedFtpFiles(prev => prev.map(f => f.path === path ? { ...f, role } : f));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in" data-testid="suppliers-page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Proveedores
          </h1>
          <p className="text-slate-500">
            Gestiona tus proveedores y sus configuraciones de conexión
          </p>
        </div>
        <Button onClick={openCreate} className="btn-primary" data-testid="add-supplier-btn">
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Añadir Proveedor
        </Button>
      </div>

      {/* Suppliers Table */}
      <SupplierTable 
        suppliers={suppliers}
        onEdit={openEdit}
        onMapping={openMapping}
        onDelete={openDelete}
        onCreate={openCreate}
      />

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              {selectedSupplier ? "Editar Proveedor" : "Nuevo Proveedor"}
            </DialogTitle>
            <DialogDescription>
              Configura los datos de conexión y formato de archivo del proveedor
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-6">
                <TabsTrigger value="general" className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  General
                </TabsTrigger>
                <TabsTrigger value="connection" className="flex items-center gap-2">
                  <Link2 className="w-4 h-4" />
                  Conexión
                </TabsTrigger>
                <TabsTrigger value="csv" className="flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Config. CSV
                </TabsTrigger>
              </TabsList>

              {/* Tab General */}
              <TabsContent value="general" className="space-y-4">
                <SupplierPresetSelector
                  selectedId={formData.preset_id}
                  onApplyPreset={(preset) => setFormData((prev) => ({ ...prev, ...preset.config, preset_id: preset.id }))}
                />

                <div className="space-y-2">
                  <Label htmlFor="name">Nombre del proveedor *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ej: Distribuidor Principal"
                    className="input-base"
                    data-testid="supplier-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Descripción</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descripción opcional del proveedor"
                    className="input-base min-h-[80px]"
                    data-testid="supplier-description-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Tipo de archivo</Label>
                  <Select
                    value={formData.file_format}
                    onValueChange={(value) => setFormData({ ...formData, file_format: value })}
                  >
                    <SelectTrigger className="input-base" data-testid="supplier-format-select">
                      <SelectValue placeholder="Seleccionar formato" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                      <SelectItem value="xls">Excel (XLS)</SelectItem>
                      <SelectItem value="xml">XML</SelectItem>
                      <SelectItem value="zip">ZIP (descompresión automática)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              {/* Tab Conexión */}
              <TabsContent value="connection" className="space-y-4">
                <ConnectionTypeSelector 
                  value={formData.connection_type}
                  onChange={(type) => setFormData({ ...formData, connection_type: type })}
                />

                {/* URL Configuration */}
                {formData.connection_type === "url" && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="file_url">URL del archivo *</Label>
                      <div className="relative">
                        <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <Input
                          id="file_url"
                          value={formData.file_url}
                          onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
                          placeholder="https://proveedor.com/catalogo.csv"
                          className="input-base pl-9 font-mono text-sm"
                          data-testid="supplier-file-url"
                        />
                      </div>
                      <p className="text-xs text-slate-500">
                        URL completa al archivo CSV, Excel o XML del proveedor
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="url_username">Usuario HTTP (opcional)</Label>
                        <Input
                          id="url_username"
                          value={formData.url_username}
                          onChange={(e) => setFormData({ ...formData, url_username: e.target.value })}
                          placeholder="usuario"
                          className="input-base"
                          autoComplete="off"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="url_password">Contraseña HTTP (opcional)</Label>
                        <Input
                          id="url_password"
                          type="password"
                          value={formData.url_password}
                          onChange={(e) => setFormData({ ...formData, url_password: e.target.value })}
                          placeholder={selectedSupplier?.url_username ? "••••  (guardada — dejar vacío para mantener)" : "contraseña"}
                          className="input-base"
                          autoComplete="new-password"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* FTP Configuration */}
                {formData.connection_type === "ftp" && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Protocolo FTP</Label>
                        <Select
                          value={formData.ftp_schema}
                          onValueChange={(value) => setFormData({ ...formData, ftp_schema: value })}
                        >
                          <SelectTrigger className="input-base" data-testid="ftp-schema-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ftp">FTP</SelectItem>
                            <SelectItem value="sftp">SFTP</SelectItem>
                            <SelectItem value="ftps">FTPS</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Modo de conexión</Label>
                        <Select
                          value={formData.ftp_mode}
                          onValueChange={(value) => setFormData({ ...formData, ftp_mode: value })}
                        >
                          <SelectTrigger className="input-base" data-testid="ftp-mode-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="passive">Pasivo</SelectItem>
                            <SelectItem value="active">Activo</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div className="col-span-2 space-y-2">
                        <Label htmlFor="ftp_host">Host</Label>
                        <Input
                          id="ftp_host"
                          value={formData.ftp_host}
                          onChange={(e) => setFormData({ ...formData, ftp_host: e.target.value })}
                          placeholder="ftp.ejemplo.com"
                          className="input-base font-mono text-sm"
                          data-testid="supplier-ftp-host"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="ftp_port">Puerto</Label>
                        <Input
                          id="ftp_port"
                          type="number"
                          value={formData.ftp_port}
                          onChange={(e) => setFormData({ ...formData, ftp_port: e.target.value })}
                          placeholder="21"
                          className="input-base font-mono text-sm"
                          data-testid="supplier-ftp-port"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="ftp_user">Usuario</Label>
                        <Input
                          id="ftp_user"
                          value={formData.ftp_user}
                          onChange={(e) => setFormData({ ...formData, ftp_user: e.target.value })}
                          placeholder="usuario"
                          className="input-base"
                          data-testid="supplier-ftp-user"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="ftp_password">Contraseña</Label>
                        <Input
                          id="ftp_password"
                          type="password"
                          value={formData.ftp_password}
                          onChange={(e) => setFormData({ ...formData, ftp_password: e.target.value })}
                          placeholder={selectedSupplier ? "••••  (guardada — dejar vacío para mantener)" : "Contraseña FTP"}
                          className="input-base"
                          data-testid="supplier-ftp-password"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="ftp_path">Ruta del archivo (único)</Label>
                      <Input
                        id="ftp_path"
                        value={formData.ftp_path}
                        onChange={(e) => setFormData({ ...formData, ftp_path: e.target.value })}
                        placeholder="/catalogo/productos.csv"
                        className="input-base font-mono text-sm"
                        data-testid="supplier-ftp-path"
                      />
                      <p className="text-xs text-slate-500">Ruta única, o usa el explorador FTP para múltiples archivos</p>
                    </div>

                    {/* Test Connection Button */}
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleFtpTestConnection}
                      disabled={ftpTestingConnection || !formData.ftp_host}
                      className="w-full"
                      data-testid="ftp-test-btn"
                    >
                      {ftpTestingConnection ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Wifi className="w-4 h-4 mr-2" />
                      )}
                      Probar Conexión
                    </Button>

                    {/* Connection Status */}
                    <FtpConnectionStatus status={ftpConnectionStatus} />

                    {/* FTP File Browser */}
                    <FtpFileBrowser
                      files={ftpFiles}
                      currentPath={ftpCurrentPath}
                      selectedFiles={selectedFtpFiles}
                      stats={ftpStats}
                      browsing={ftpBrowsing}
                      listingAll={ftpListingAll}
                      canListAll={!!selectedSupplier?.id}
                      onBrowse={handleFtpBrowse}
                      onListAll={handleFtpListAllFiles}
                      onAddFile={addFtpFile}
                      onRemoveFile={removeFtpFile}
                      onUpdateFileRole={updateFtpFileRole}
                      formatFileSize={formatFileSize}
                    />
                  </>
                )}
              </TabsContent>

              {/* Tab Config CSV */}
              <TabsContent value="csv" className="space-y-4">
                <div className="p-3 bg-slate-50 rounded-sm mb-4">
                  <p className="text-sm text-slate-600">
                    Configura cómo se debe interpretar el archivo CSV del proveedor.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="csv_separator">Separador de columnas</Label>
                    <Select
                      value={formData.csv_separator}
                      onValueChange={(value) => setFormData({ ...formData, csv_separator: value })}
                    >
                      <SelectTrigger className="input-base" data-testid="csv-separator-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=";">Punto y coma (;)</SelectItem>
                        <SelectItem value=",">Coma (,)</SelectItem>
                        <SelectItem value="\t">Tabulador</SelectItem>
                        <SelectItem value="|">Barra vertical (|)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="csv_enclosure">Delimitador de texto</Label>
                    <Select
                      value={formData.csv_enclosure}
                      onValueChange={(value) => setFormData({ ...formData, csv_enclosure: value === "none" ? "" : value })}
                    >
                      <SelectTrigger className="input-base" data-testid="csv-enclosure-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value='"'>Comillas dobles (")</SelectItem>
                        <SelectItem value="'">Comillas simples (')</SelectItem>
                        <SelectItem value="none">Ninguno</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="csv_line_break">Salto de línea</Label>
                    <Select
                      value={formData.csv_line_break}
                      onValueChange={(value) => setFormData({ ...formData, csv_line_break: value })}
                    >
                      <SelectTrigger className="input-base" data-testid="csv-linebreak-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="\n">Unix (LF)</SelectItem>
                        <SelectItem value="\r\n">Windows (CRLF)</SelectItem>
                        <SelectItem value="\r">Mac antiguo (CR)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="csv_header_row">Fila de la cabecera</Label>
                    <Input
                      id="csv_header_row"
                      type="number"
                      min="0"
                      value={formData.csv_header_row}
                      onChange={(e) => setFormData({ ...formData, csv_header_row: e.target.value })}
                      placeholder="1"
                      className="input-base font-mono"
                      data-testid="csv-header-row"
                    />
                    <p className="text-xs text-slate-500">Fila de cabecera (1 = primera fila). Usa 0 si el archivo no tiene cabecera (ej: INGRAM PRICE09.TXT).</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-sm border border-amber-200">
                  <input
                    type="checkbox"
                    id="strip_ean_quotes"
                    checked={formData.strip_ean_quotes || false}
                    onChange={(e) => setFormData({ ...formData, strip_ean_quotes: e.target.checked })}
                    className="w-4 h-4 text-amber-600 rounded cursor-pointer"
                    data-testid="strip-ean-quotes-checkbox"
                  />
                  <label htmlFor="strip_ean_quotes" className="flex-1 cursor-pointer">
                    <p className="text-sm font-medium text-amber-800">Limpiar comillas simples del EAN</p>
                    <p className="text-xs text-amber-700 mt-0.5">
                      Si el proveedor envía los códigos EAN entre comillas simples ('1234567890'), activa esta opción para eliminarlas automáticamente.
                    </p>
                  </label>
                </div>

                <div className="p-3 bg-indigo-50 rounded-sm border border-indigo-200">
                  <div className="flex items-start gap-3">
                    <Columns className="w-5 h-5 text-indigo-600 mt-0.5" strokeWidth={1.5} />
                    <div>
                      <p className="text-sm text-indigo-800 font-medium mb-1">Mapeo de columnas</p>
                      <p className="text-sm text-indigo-700 mb-2">
                        Después de crear el proveedor y sincronizar por primera vez, podrás mapear las columnas 
                        del archivo del proveedor a los campos del sistema desde el menú de acciones.
                      </p>
                      {formData.column_mapping && (
                        <p className="text-xs text-indigo-600">
                          Mapeo configurado: {Object.keys(formData.column_mapping).length} campos
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} className="btn-secondary">
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="supplier-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : selectedSupplier ? "Guardar Cambios" : "Crear Proveedor"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Column Mapping Dialog */}
      <ColumnMappingDialog
        open={showMappingDialog}
        onOpenChange={setShowMappingDialog}
        detectedColumns={mappingSupplier?.detected_columns || []}
        currentMapping={mappingSupplier?.column_mapping}
        suggestedMapping={mappingSupplier?.suggested_mapping}
        onSave={handleSaveMapping}
        saving={saving}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>¿Eliminar proveedor?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción eliminará permanentemente el proveedor "{selectedSupplier?.name}" y todos sus productos asociados. Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700 text-white" data-testid="confirm-delete-supplier">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Suppliers;
