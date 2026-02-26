import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent } from "../components/ui/card";
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
  Truck,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Server,
  FileText,
  Eye,
  RefreshCw,
  Settings,
  Database,
  Link2,
  Columns,
  Globe,
  ExternalLink,
  FolderOpen,
  FileArchive,
  X,
  CheckCircle,
  ChevronRight,
  Wifi,
  WifiOff,
  FileSpreadsheet,
  Search,
  FolderTree
} from "lucide-react";
import ColumnMappingDialog from "../components/ColumnMappingDialog";
import { Badge } from "../components/ui/badge";

const defaultFormData = {
  name: "",
  description: "",
  // Tipo de conexión
  connection_type: "ftp",
  // URL directa
  file_url: "",
  // Conexión FTP
  ftp_schema: "ftp",
  ftp_host: "",
  ftp_user: "",
  ftp_password: "",
  ftp_port: 21,
  ftp_path: "",
  ftp_mode: "passive",
  // Configuración CSV
  file_format: "csv",
  csv_separator: ";",
  csv_enclosure: '"',
  csv_line_break: "\\n",
  csv_header_row: 1,
  // Mapeo de campos
  column_mapping: null
};

const Suppliers = () => {
  const navigate = useNavigate();
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
      column_mapping: supplier.column_mapping || null
    });
    setSelectedFtpFiles(supplier.ftp_paths || []);
    setShowDialog(true);
  };

  const openMapping = async (supplier) => {
    setMappingSupplier(supplier);
    setShowMappingDialog(true);
    
    // Try to load preview and suggested mapping from file
    try {
      const res = await api.post(`/suppliers/${supplier.id}/preview-file`);
      if (res.data.status === "success") {
        // Update supplier with detected columns and suggested mapping
        setMappingSupplier({
          ...supplier,
          detected_columns: res.data.columns,
          suggested_mapping: res.data.suggested_mapping
        });
        toast.success(`${res.data.columns.length} columnas detectadas automáticamente`);
      }
    } catch (error) {
      // If preview fails, just use existing detected columns
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
      csv_header_row: parseInt(formData.csv_header_row) || 1,
      ftp_paths: selectedFtpFiles.length > 0 ? selectedFtpFiles : null
    };

    try {
      if (selectedSupplier) {
        await api.put(`/suppliers/${selectedSupplier.id}`, payload);
        toast.success("Proveedor actualizado");
      } else {
        await api.post("/suppliers", payload);
        toast.success("Proveedor creado");
      }
      setShowDialog(false);
      resetForm();
      fetchSuppliers();
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
        ftp_password: formData.ftp_password || (selectedSupplier ? "__keep__" : ""),
        ftp_port: parseInt(formData.ftp_port) || 21,
        ftp_mode: formData.ftp_mode || "passive",
        path
      });
      if (res.data.status === "ok") {
        setFtpFiles(res.data.files);
        setFtpCurrentPath(res.data.path);
        setFtpStats(res.data.stats);
        
        // Auto-select: only on first browse (root path) and no files selected yet
        if (path === "/" && selectedFtpFiles.length === 0) {
          const autoSelected = [];
          const files = res.data.files.filter(f => !f.is_dir);
          
          // Find StockFile
          const stockFile = files.find(f => f.name.toLowerCase().includes('stock') && !f.name.endsWith('.zip'));
          if (stockFile) {
            autoSelected.push({
              path: stockFile.path, role: 'stock', label: stockFile.name,
              separator: ";", header_row: 1, merge_key: null
            });
          }
          
          // Find latest ZIP by date in filename (e.g. TD_ES_564195_A_20260223.zip)
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
        ftp_mode: formData.ftp_mode || "passive"
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
        // Mostrar archivos encontrados y preguntar si quiere añadirlos
        toast.success(`Encontrados ${res.data.total_files} archivos soportados`);
        
        // Convertir a formato de selectedFtpFiles
        const newFiles = res.data.files.map(f => ({
          path: f.path,
          role: guessFileRole(f.name),
          label: f.name,
          separator: ";",
          header_row: 1,
          merge_key: null,
          size: f.size_formatted
        }));
        
        // Añadir solo los que no estén ya seleccionados
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

  const ROLE_LABELS = {
    products: "Productos", prices: "Precios", stock: "Stock",
    prices_qb: "Precios Vol.", kit: "Kits", min_qty: "Cant. Mín.", other: "Otro"
  };

  const ROLE_COLORS = {
    products: "bg-indigo-100 text-indigo-700", prices: "bg-emerald-100 text-emerald-700",
    stock: "bg-amber-100 text-amber-700", prices_qb: "bg-purple-100 text-purple-700",
    kit: "bg-slate-100 text-slate-700", min_qty: "bg-blue-100 text-blue-700",
    other: "bg-slate-100 text-slate-700"
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
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

      {/* Suppliers List */}
      {suppliers.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Truck className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay proveedores
          </h3>
          <p className="text-slate-500 mb-4">
            Añade tu primer proveedor para comenzar a importar productos
          </p>
          <Button onClick={openCreate} className="btn-primary" data-testid="empty-add-supplier">
            <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Añadir Proveedor
          </Button>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Proveedor</TableHead>
                  <TableHead>Formato</TableHead>
                  <TableHead>Conexión</TableHead>
                  <TableHead></TableHead>
                  <TableHead className="text-right">Productos</TableHead>
                  <TableHead>Última Sincronización</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map((supplier) => (
                  <TableRow key={supplier.id} className="table-row" data-testid={`supplier-row-${supplier.id}`}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-100 rounded-sm flex items-center justify-center">
                          <Truck className="w-5 h-5 text-slate-600" strokeWidth={1.5} />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{supplier.name}</p>
                          {supplier.description && (
                            <p className="text-sm text-slate-500 truncate max-w-[200px]">
                              {supplier.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-slate-100 rounded-sm text-xs font-medium text-slate-700 uppercase">
                        <FileText className="w-3.5 h-3.5" strokeWidth={1.5} />
                        {supplier.file_format || "CSV"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {supplier.connection_type === "url" && supplier.file_url ? (
                        <div className="flex items-center gap-2">
                          <Globe className="w-4 h-4 text-emerald-500" strokeWidth={1.5} />
                          <span className="text-sm text-slate-600 truncate max-w-[200px]" title={supplier.file_url}>
                            URL Directa
                          </span>
                        </div>
                      ) : supplier.ftp_host ? (
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-emerald-500" strokeWidth={1.5} />
                          <span className="text-sm text-slate-600 font-mono">
                            {supplier.ftp_schema?.toUpperCase() || "FTP"}://{supplier.ftp_host}:{supplier.ftp_port || 21}
                          </span>
                          {supplier.ftp_paths?.length > 0 && (
                            <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full font-medium">
                              {supplier.ftp_paths.length} archivos
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-slate-400">No configurado</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/suppliers/${supplier.id}`)}
                        className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 font-medium"
                        data-testid={`view-catalog-${supplier.id}`}
                      >
                        <Eye className="w-4 h-4 mr-1.5" strokeWidth={1.5} />
                        Ver catálogo
                      </Button>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-slate-900">{supplier.product_count.toLocaleString()}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-500">{formatDate(supplier.last_sync)}</span>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid={`supplier-menu-${supplier.id}`}>
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(supplier)} data-testid={`edit-supplier-${supplier.id}`}>
                            <Pencil className="w-4 h-4 mr-2" strokeWidth={1.5} />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openMapping(supplier)} data-testid={`mapping-supplier-${supplier.id}`}>
                            <Columns className="w-4 h-4 mr-2" strokeWidth={1.5} />
                            Mapear Columnas
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => openDelete(supplier)}
                            className="text-rose-600 focus:text-rose-600"
                            data-testid={`delete-supplier-${supplier.id}`}
                          >
                            <Trash2 className="w-4 h-4 mr-2" strokeWidth={1.5} />
                            Eliminar
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

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
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              {/* Tab Conexión */}
              <TabsContent value="connection" className="space-y-4">
                {/* Tipo de conexión */}
                <div className="p-3 bg-slate-50 rounded-sm mb-4">
                  <Label className="text-sm font-medium mb-3 block">Tipo de conexión</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, connection_type: "ftp" })}
                      className={`p-3 rounded-lg border-2 text-left transition-all ${
                        formData.connection_type === "ftp" 
                          ? "border-indigo-500 bg-indigo-50" 
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Server className={`w-4 h-4 ${formData.connection_type === "ftp" ? "text-indigo-600" : "text-slate-400"}`} />
                        <span className={`font-medium ${formData.connection_type === "ftp" ? "text-indigo-900" : "text-slate-700"}`}>
                          FTP / SFTP
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">Conexión a servidor FTP del proveedor</p>
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, connection_type: "url" })}
                      className={`p-3 rounded-lg border-2 text-left transition-all ${
                        formData.connection_type === "url" 
                          ? "border-indigo-500 bg-indigo-50" 
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Globe className={`w-4 h-4 ${formData.connection_type === "url" ? "text-indigo-600" : "text-slate-400"}`} />
                        <span className={`font-medium ${formData.connection_type === "url" ? "text-indigo-900" : "text-slate-700"}`}>
                          URL Directa
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">Descargar desde URL HTTP/HTTPS</p>
                    </button>
                  </div>
                </div>

                {/* Configuración URL */}
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
                    
                    <div className="p-3 bg-amber-50 rounded-sm border border-amber-200">
                      <div className="flex items-start gap-2">
                        <ExternalLink className="w-4 h-4 text-amber-600 mt-0.5" />
                        <div className="text-sm text-amber-800">
                          <p className="font-medium mb-1">Nota sobre URLs</p>
                          <p className="text-xs">
                            La URL debe ser accesible públicamente o no requerir autenticación. 
                            Para URLs protegidas, usa la conexión FTP/SFTP.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Configuración FTP */}
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
                          placeholder="••••••••"
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
                    <div className="flex items-center gap-3">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleFtpTestConnection}
                        disabled={ftpTestingConnection || !formData.ftp_host}
                        className="flex-1"
                        data-testid="ftp-test-btn"
                      >
                        {ftpTestingConnection ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Wifi className="w-4 h-4 mr-2" />
                        )}
                        Probar Conexión
                      </Button>
                    </div>

                    {/* Connection Status */}
                    {ftpConnectionStatus && (
                      <div className={`p-3 rounded-lg border ${
                        ftpConnectionStatus.connected 
                          ? "bg-emerald-50 border-emerald-200" 
                          : "bg-rose-50 border-rose-200"
                      }`}>
                        <div className="flex items-start gap-3">
                          {ftpConnectionStatus.connected ? (
                            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                          ) : (
                            <WifiOff className="w-5 h-5 text-rose-500 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className={`font-medium text-sm ${
                              ftpConnectionStatus.connected ? "text-emerald-800" : "text-rose-800"
                            }`}>
                              {ftpConnectionStatus.connected ? "Conexión exitosa" : "Error de conexión"}
                            </p>
                            <p className="text-xs text-slate-600 mt-0.5">{ftpConnectionStatus.message}</p>
                            {ftpConnectionStatus.connected && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                <Badge variant="outline" className="text-xs">
                                  {ftpConnectionStatus.protocol}
                                </Badge>
                                {ftpConnectionStatus.mode && (
                                  <Badge variant="outline" className="text-xs">
                                    Modo {ftpConnectionStatus.mode}
                                  </Badge>
                                )}
                                {ftpConnectionStatus.files_in_root !== undefined && (
                                  <Badge variant="outline" className="text-xs">
                                    {ftpConnectionStatus.files_in_root} items en raíz
                                  </Badge>
                                )}
                              </div>
                            )}
                            {ftpConnectionStatus.suggestion && (
                              <p className="text-xs text-amber-700 mt-2 bg-amber-50 px-2 py-1 rounded">
                                💡 {ftpConnectionStatus.suggestion}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* FTP File Browser */}
                    <div className="border border-slate-200 rounded-lg overflow-hidden mt-4">
                      <div className="bg-slate-50 px-4 py-3 flex items-center justify-between border-b border-slate-200">
                        <div className="flex items-center gap-2">
                          <FolderOpen className="w-4 h-4 text-indigo-600" />
                          <span className="text-sm font-semibold text-slate-800">Explorador FTP</span>
                          {selectedFtpFiles.length > 0 && (
                            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
                              {selectedFtpFiles.length} archivos
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {selectedSupplier?.id && (
                            <Button
                              type="button" size="sm" variant="outline"
                              onClick={handleFtpListAllFiles}
                              disabled={ftpListingAll || ftpBrowsing || !formData.ftp_host}
                              className="text-xs h-7"
                              title="Buscar todos los archivos en subcarpetas"
                              data-testid="ftp-list-all-btn"
                            >
                              {ftpListingAll ? (
                                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                              ) : (
                                <FolderTree className="w-3 h-3 mr-1" />
                              )}
                              Buscar en carpetas
                            </Button>
                          )}
                          <Button
                            type="button" size="sm" variant="outline"
                            onClick={() => handleFtpBrowse(ftpCurrentPath)}
                            disabled={ftpBrowsing || !formData.ftp_host}
                            className="text-xs h-7"
                            data-testid="ftp-browse-btn"
                          >
                            {ftpBrowsing ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <FolderOpen className="w-3 h-3 mr-1" />}
                            Explorar
                          </Button>
                        </div>
                      </div>

                      {/* FTP Stats */}
                      {ftpStats && (
                        <div className="px-4 py-2 bg-slate-50/50 border-b border-slate-100 flex items-center gap-4">
                          <div className="flex items-center gap-1.5 text-xs text-slate-600">
                            <FolderOpen className="w-3.5 h-3.5 text-amber-500" />
                            <span>{ftpStats.total_dirs} carpetas</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-slate-600">
                            <FileText className="w-3.5 h-3.5 text-slate-400" />
                            <span>{ftpStats.total_files} archivos</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-emerald-600">
                            <FileSpreadsheet className="w-3.5 h-3.5" />
                            <span>{ftpStats.supported_files} soportados</span>
                          </div>
                        </div>
                      )}

                      {/* Selected Files */}
                      {selectedFtpFiles.length > 0 && (
                        <div className="p-3 bg-indigo-50/50 border-b border-slate-200">
                          <p className="text-xs font-medium text-slate-600 mb-2">Archivos seleccionados para sincronización:</p>
                          <div className="space-y-1.5">
                            {selectedFtpFiles.map((file) => (
                              <div key={file.path} className="flex items-center gap-2 bg-white rounded-md px-3 py-2 border border-slate-200">
                                <FileArchive className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                <span className="text-xs font-mono text-slate-700 flex-1 truncate">{file.label || file.path}</span>
                                <select
                                  value={file.role}
                                  onChange={(e) => updateFtpFileRole(file.path, e.target.value)}
                                  className="text-xs border border-slate-200 rounded px-2 py-1 bg-white"
                                  data-testid={`file-role-${file.path}`}
                                >
                                  {Object.entries(ROLE_LABELS).map(([val, label]) => (
                                    <option key={val} value={val}>{label}</option>
                                  ))}
                                </select>
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[file.role] || ROLE_COLORS.other}`}>
                                  {ROLE_LABELS[file.role] || file.role}
                                </span>
                                <button type="button" onClick={() => removeFtpFile(file.path)}
                                  className="text-slate-400 hover:text-rose-500 transition-colors" data-testid={`remove-file-${file.path}`}>
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* File Browser */}
                      {ftpFiles.length > 0 && (
                        <div className="max-h-64 overflow-y-auto">
                          {/* Current path */}
                          <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex items-center gap-1">
                            <span className="text-xs text-slate-500">Ruta:</span>
                            <span className="text-xs font-mono text-slate-700">{ftpCurrentPath}</span>
                            {ftpCurrentPath !== "/" && (
                              <button type="button" onClick={() => {
                                const parent = ftpCurrentPath.split("/").slice(0, -1).join("/") || "/";
                                handleFtpBrowse(parent);
                              }} className="text-xs text-indigo-600 hover:text-indigo-700 ml-2 font-medium">
                                ↑ Subir
                              </button>
                            )}
                          </div>
                          {ftpFiles.map((file) => {
                            const isSelected = selectedFtpFiles.some(f => f.path === file.path);
                            const isSupported = file.is_supported;
                            return (
                              <div key={file.path}
                                className={`flex items-center gap-3 px-3 py-2 border-b border-slate-100 hover:bg-slate-50 transition-colors ${
                                  file.is_dir ? "cursor-pointer" : ""
                                } ${isSelected ? "bg-indigo-50" : ""} ${!file.is_dir && !isSupported ? "opacity-50" : ""}`}
                                onClick={() => file.is_dir ? handleFtpBrowse(file.path) : null}
                                data-testid={`ftp-file-${file.name}`}
                              >
                                {file.is_dir ? (
                                  <FolderOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
                                ) : file.name.endsWith('.zip') ? (
                                  <FileArchive className="w-4 h-4 text-purple-500 flex-shrink-0" />
                                ) : file.extension === 'csv' || file.extension === 'xlsx' || file.extension === 'xls' ? (
                                  <FileSpreadsheet className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                ) : (
                                  <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                )}
                                <span className={`text-sm flex-1 truncate ${file.is_dir ? "font-medium text-slate-800" : "text-slate-700 font-mono text-xs"}`}>
                                  {file.name}
                                </span>
                                {!file.is_dir && (
                                  <>
                                    {file.extension && (
                                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                                        isSupported ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                                      }`}>
                                        {file.extension.toUpperCase()}
                                      </span>
                                    )}
                                    <span className="text-xs text-slate-400 min-w-[60px] text-right">
                                      {file.size_formatted || formatFileSize(file.size)}
                                    </span>
                                    {isSelected ? (
                                      <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 min-w-[70px]">
                                        <CheckCircle className="w-3 h-3" /> Añadido
                                      </span>
                                    ) : isSupported ? (
                                      <button type="button" onClick={(e) => { e.stopPropagation(); addFtpFile(file); }}
                                        className="text-xs bg-indigo-600 text-white px-2.5 py-1 rounded-md hover:bg-indigo-700 transition-colors font-medium min-w-[70px]"
                                        data-testid={`add-file-${file.name}`}
                                      >
                                        Añadir
                                      </button>
                                    ) : (
                                      <span className="text-xs text-slate-400 min-w-[70px]">No soportado</span>
                                    )}
                                  </>
                                )}
                                {file.is_dir && (
                                  <ChevronRight className="w-4 h-4 text-slate-400" />
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {ftpFiles.length === 0 && !ftpBrowsing && (
                        <div className="py-8 text-center text-sm text-slate-400">
                          Pulsa "Conectar" para explorar los archivos del servidor FTP
                        </div>
                      )}
                      {ftpBrowsing && (
                        <div className="py-8 text-center">
                          <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin mx-auto mb-2" />
                          <p className="text-sm text-slate-400">Conectando al FTP...</p>
                        </div>
                      )}
                    </div>
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
                      min="1"
                      value={formData.csv_header_row}
                      onChange={(e) => setFormData({ ...formData, csv_header_row: e.target.value })}
                      placeholder="1"
                      className="input-base font-mono"
                      data-testid="csv-header-row"
                    />
                    <p className="text-xs text-slate-500">Número de fila donde empiezan los nombres de columna</p>
                  </div>
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
