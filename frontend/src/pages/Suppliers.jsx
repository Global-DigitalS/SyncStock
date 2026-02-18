import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
  Package,
  RefreshCw,
  Eye
} from "lucide-react";

const Suppliers = () => {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    ftp_host: "",
    ftp_user: "",
    ftp_password: "",
    ftp_path: "",
    file_format: "csv"
  });
  const [saving, setSaving] = useState(false);

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
    setFormData({
      name: "",
      description: "",
      ftp_host: "",
      ftp_user: "",
      ftp_password: "",
      ftp_path: "",
      file_format: "csv"
    });
    setSelectedSupplier(null);
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
      ftp_host: supplier.ftp_host || "",
      ftp_user: supplier.ftp_user || "",
      ftp_password: "",
      ftp_path: supplier.ftp_path || "",
      file_format: supplier.file_format || "csv"
    });
    setShowDialog(true);
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
    try {
      if (selectedSupplier) {
        await api.put(`/suppliers/${selectedSupplier.id}`, formData);
        toast.success("Proveedor actualizado");
      } else {
        await api.post("/suppliers", formData);
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
                  <TableHead>Conexión FTP</TableHead>
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
                      {supplier.ftp_host ? (
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-emerald-500" strokeWidth={1.5} />
                          <span className="text-sm text-slate-600 font-mono">{supplier.ftp_host}</span>
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              {selectedSupplier ? "Editar Proveedor" : "Nuevo Proveedor"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-5">
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
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Descripción opcional"
                className="input-base"
                data-testid="supplier-description-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="file_format">Formato de archivo</Label>
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

            <div className="pt-2 border-t border-slate-200">
              <p className="text-sm font-medium text-slate-700 mb-3">Configuración FTP (opcional)</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ftp_host">Host FTP</Label>
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
                  <Label htmlFor="ftp_path">Ruta</Label>
                  <Input
                    id="ftp_path"
                    value={formData.ftp_path}
                    onChange={(e) => setFormData({ ...formData, ftp_path: e.target.value })}
                    placeholder="/catalogo/"
                    className="input-base font-mono text-sm"
                    data-testid="supplier-ftp-path"
                  />
                </div>
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
            </div>

            <DialogFooter>
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
