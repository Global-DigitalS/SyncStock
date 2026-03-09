import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "../components/ui/alert-dialog";
import {
  Users, Shield, UserCog, Trash2, Crown, Eye, Edit3, Settings, Truck, BookOpen, ShoppingCart, FileUser
} from "lucide-react";
import UserDetailDialog from "../components/UserDetailDialog";

const ROLE_CONFIG = {
  superadmin: { label: "SuperAdmin", color: "bg-purple-100 text-purple-700", icon: Crown },
  admin: { label: "Administrador", color: "bg-indigo-100 text-indigo-700", icon: Shield },
  user: { label: "Usuario", color: "bg-emerald-100 text-emerald-700", icon: Edit3 },
  viewer: { label: "Visor", color: "bg-slate-100 text-slate-600", icon: Eye }
};

const ROLE_PERMISSIONS = {
  superadmin: ["Todos los permisos", "Gestión de usuarios", "Configurar límites"],
  admin: ["Lectura", "Escritura", "Eliminación", "Sincronización", "Exportación"],
  user: ["Lectura", "Escritura", "Eliminación", "Sincronización", "Exportación"],
  viewer: ["Solo lectura"]
};

const UserManagement = () => {
  const { user: currentUser } = useContext(AuthContext);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [editLimitsUser, setEditLimitsUser] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [limitsForm, setLimitsForm] = useState({
    max_suppliers: 10,
    max_catalogs: 5,
    max_woocommerce_stores: 2
  });
  const [savingLimits, setSavingLimits] = useState(false);

  const fetchUsers = async () => {
    try {
      const res = await api.get("/users");
      setUsers(res.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("No tienes permisos para ver esta página");
      } else {
        toast.error("Error al cargar usuarios");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.put(`/users/${userId}/role?role=${newRole}`);
      toast.success("Rol actualizado correctamente");
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cambiar rol");
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteConfirm) return;
    try {
      await api.delete(`/users/${deleteConfirm}`);
      toast.success("Usuario eliminado");
      setDeleteConfirm(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar usuario");
    }
  };

  const openLimitsDialog = async (user) => {
    setEditLimitsUser(user);
    // Fetch current usage
    try {
      const res = await api.get(`/users/${user.id}`);
      setLimitsForm({
        max_suppliers: res.data.max_suppliers || 10,
        max_catalogs: res.data.max_catalogs || 5,
        max_woocommerce_stores: res.data.max_woocommerce_stores || 2
      });
    } catch (error) {
      setLimitsForm({
        max_suppliers: user.max_suppliers || 10,
        max_catalogs: user.max_catalogs || 5,
        max_woocommerce_stores: user.max_woocommerce_stores || 2
      });
    }
  };

  const handleSaveLimits = async () => {
    if (!editLimitsUser) return;
    setSavingLimits(true);
    try {
      await api.put(`/users/${editLimitsUser.id}/limits`, limitsForm);
      toast.success("Límites actualizados correctamente");
      setEditLimitsUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar límites");
    } finally {
      setSavingLimits(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric"
    });
  };

  const isSuperAdmin = currentUser?.role === "superadmin";

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  if (!["admin", "superadmin"].includes(currentUser?.role)) {
    return (
      <div className="p-6 lg:p-8">
        <div className="empty-state">
          <Shield className="w-16 h-16 text-slate-300 mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Acceso Restringido</h2>
          <p className="text-slate-500">Solo los administradores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="users-title">
          Gestión de Usuarios
        </h1>
        <p className="text-slate-500">
          {isSuperAdmin 
            ? "Administra usuarios, roles y límites de recursos" 
            : "Visualiza los usuarios de la plataforma"}
        </p>
      </div>

      {/* Role Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Object.entries(ROLE_CONFIG).map(([role, config]) => {
          const count = users.filter(u => u.role === role).length;
          const Icon = config.icon;
          return (
            <Card key={role} className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${config.color.replace("text-", "bg-").split(" ")[0]}/20`}>
                    <Icon className={`w-5 h-5 ${config.color.split(" ")[1]}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900 text-sm">{config.label}</span>
                      <Badge className={config.color}>{count}</Badge>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 truncate">
                      {ROLE_PERMISSIONS[role][0]}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Users Table */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <Users className="w-5 h-5 text-indigo-600" />
            Usuarios ({users.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="table-header">
                <TableHead>Usuario</TableHead>
                <TableHead>Empresa</TableHead>
                <TableHead>Rol</TableHead>
                <TableHead className="text-center">Límites</TableHead>
                <TableHead>Registro</TableHead>
                <TableHead className="w-[120px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => {
                const roleConfig = ROLE_CONFIG[user.role] || ROLE_CONFIG.user;
                const isCurrentUser = user.id === currentUser?.id;
                const canEditLimits = isSuperAdmin && user.role !== "superadmin";
                const canChangeRole = (isSuperAdmin || (currentUser?.role === "admin" && !["admin", "superadmin"].includes(user.role)));
                
                return (
                  <TableRow key={user.id} className="table-row" data-testid={`user-row-${user.id}`}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                          user.role === "superadmin" ? "bg-purple-100" : "bg-indigo-100"
                        }`}>
                          <span className={`text-sm font-semibold ${
                            user.role === "superadmin" ? "text-purple-600" : "text-indigo-600"
                          }`}>
                            {user.name?.charAt(0).toUpperCase() || "U"}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-900">{user.name}</span>
                            {isCurrentUser && (
                              <Badge className="bg-indigo-100 text-indigo-700 text-xs">Tú</Badge>
                            )}
                          </div>
                          <span className="text-sm text-slate-500">{user.email}</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-slate-600">{user.company || "-"}</span>
                    </TableCell>
                    <TableCell>
                      {canChangeRole && !isCurrentUser ? (
                        <Select
                          value={user.role}
                          onValueChange={(v) => handleRoleChange(user.id, v)}
                        >
                          <SelectTrigger className="w-[140px] h-8" data-testid={`role-select-${user.id}`}>
                            <Badge className={roleConfig.color}>{roleConfig.label}</Badge>
                          </SelectTrigger>
                          <SelectContent>
                            {Object.entries(ROLE_CONFIG).map(([role, config]) => {
                              // Only superadmin can assign superadmin/admin
                              if (!isSuperAdmin && ["superadmin", "admin"].includes(role)) return null;
                              return (
                                <SelectItem key={role} value={role}>
                                  <div className="flex items-center gap-2">
                                    <config.icon className="w-4 h-4" />
                                    {config.label}
                                  </div>
                                </SelectItem>
                              );
                            })}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge className={roleConfig.color}>{roleConfig.label}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="flex items-center gap-1" title="Proveedores">
                          <Truck className="w-3 h-3 text-slate-400" />
                          {user.max_suppliers || 10}
                        </span>
                        <span className="flex items-center gap-1" title="Catálogos">
                          <BookOpen className="w-3 h-3 text-slate-400" />
                          {user.max_catalogs || 5}
                        </span>
                        <span className="flex items-center gap-1" title="Tiendas">
                          <ShoppingCart className="w-3 h-3 text-slate-400" />
                          {user.max_woocommerce_stores || 2}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-500">{formatDate(user.created_at)}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {isSuperAdmin && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-purple-500 hover:text-purple-700 hover:bg-purple-50"
                            onClick={() => setSelectedUserId(user.id)}
                            data-testid={`view-user-${user.id}`}
                            title="Ver ficha de usuario"
                          >
                            <FileUser className="w-4 h-4" />
                          </Button>
                        )}
                        {canEditLimits && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50"
                            onClick={() => openLimitsDialog(user)}
                            data-testid={`edit-limits-${user.id}`}
                          >
                            <Settings className="w-4 h-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 text-rose-500 hover:text-rose-700 hover:bg-rose-50"
                          onClick={() => setDeleteConfirm(user.id)}
                          disabled={isCurrentUser || (user.role === "superadmin" && !isSuperAdmin)}
                          data-testid={`delete-user-${user.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* User Detail Dialog (SuperAdmin only) */}
      {isSuperAdmin && (
        <UserDetailDialog
          userId={selectedUserId}
          open={!!selectedUserId}
          onClose={() => setSelectedUserId(null)}
          onUpdate={fetchUsers}
        />
      )}

      {/* Edit Limits Dialog (SuperAdmin only) */}
      <Dialog open={!!editLimitsUser} onOpenChange={() => setEditLimitsUser(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Settings className="w-5 h-5 text-indigo-600" />
              Configurar Límites
            </DialogTitle>
            <DialogDescription>
              Configura los límites de recursos para {editLimitsUser?.name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-slate-500" />
                Máximo de Proveedores
              </Label>
              <Input
                type="number"
                min="0"
                value={limitsForm.max_suppliers}
                onChange={(e) => setLimitsForm({ ...limitsForm, max_suppliers: parseInt(e.target.value) || 0 })}
                className="input-base"
                data-testid="input-max-suppliers"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-slate-500" />
                Máximo de Catálogos
              </Label>
              <Input
                type="number"
                min="0"
                value={limitsForm.max_catalogs}
                onChange={(e) => setLimitsForm({ ...limitsForm, max_catalogs: parseInt(e.target.value) || 0 })}
                className="input-base"
                data-testid="input-max-catalogs"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <ShoppingCart className="w-4 h-4 text-slate-500" />
                Máximo de Tiendas Online
              </Label>
              <Input
                type="number"
                min="0"
                value={limitsForm.max_woocommerce_stores}
                onChange={(e) => setLimitsForm({ ...limitsForm, max_woocommerce_stores: parseInt(e.target.value) || 0 })}
                className="input-base"
                data-testid="input-max-stores"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditLimitsUser(null)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveLimits} disabled={savingLimits} className="btn-primary">
              {savingLimits ? "Guardando..." : "Guardar Límites"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar usuario?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. El usuario perderá acceso a la plataforma.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteUser} className="bg-rose-600 hover:bg-rose-700">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default UserManagement;
