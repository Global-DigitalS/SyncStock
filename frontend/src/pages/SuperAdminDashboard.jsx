import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
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
  Users, Shield, Package, Truck, BookOpen, ShoppingCart, 
  RefreshCw, AlertCircle, TrendingUp, Crown, Eye, Edit3,
  Activity, Database, Server, CheckCircle, XCircle, Trash2, AlertTriangle
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const ROLE_COLORS = {
  superadmin: "#8b5cf6",
  admin: "#6366f1",
  user: "#10b981",
  viewer: "#64748b"
};

const ROLE_CONFIG = {
  superadmin: { label: "SuperAdmin", icon: Crown, color: "bg-purple-100 text-purple-700" },
  admin: { label: "Admin", icon: Shield, color: "bg-indigo-100 text-indigo-700" },
  user: { label: "Usuario", icon: Edit3, color: "bg-emerald-100 text-emerald-700" },
  viewer: { label: "Visor", icon: Eye, color: "bg-slate-100 text-slate-600" }
};

const SuperAdminDashboard = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetConfirmation, setResetConfirmation] = useState("");
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    if (user?.role !== "superadmin") {
      navigate("/");
      return;
    }
    fetchStats();
  }, [user, navigate]);

  const fetchStats = async () => {
    try {
      const res = await api.get("/dashboard/superadmin-stats");
      setStats(res.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Acceso denegado. Solo SuperAdmin puede ver esta página.");
        navigate("/");
      } else {
        toast.error("Error al cargar estadísticas");
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric"
    });
  };

  const handleResetApplication = async () => {
    if (resetConfirmation !== "RESET") {
      toast.error("Escribe 'RESET' para confirmar");
      return;
    }

    setResetting(true);
    try {
      const res = await api.post("/admin/system/reset", {
        confirmation_text: "RESET"
      });
      toast.success(res.data.message);
      setShowResetDialog(false);
      setResetConfirmation("");
      // Refresh stats after reset
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al reiniciar la aplicación");
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  if (!stats) {
    return (
      <div className="p-6 lg:p-8">
        <div className="empty-state">
          <AlertCircle className="w-16 h-16 text-slate-300 mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Error al cargar</h2>
          <p className="text-slate-500">No se pudieron cargar las estadísticas globales.</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const usersByRoleData = Object.entries(stats.users.by_role).map(([role, count]) => ({
    name: ROLE_CONFIG[role]?.label || role,
    value: count,
    color: ROLE_COLORS[role] || "#94a3b8"
  }));

  const resourcesData = [
    { name: "Proveedores", value: stats.resources.suppliers, icon: Truck },
    { name: "Productos", value: stats.resources.products, icon: Package },
    { name: "Catálogos", value: stats.resources.catalogs, icon: BookOpen },
    { name: "Tiendas WC", value: stats.resources.woocommerce_stores, icon: ShoppingCart }
  ];

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="superadmin-dashboard-title">
          Dashboard SuperAdmin
        </h1>
        <p className="text-slate-500">Vista global de la plataforma y estadísticas de uso</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-slate-200 hover:border-indigo-200 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-indigo-100">
                <Users className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.users.total}</p>
                <p className="text-sm text-slate-500">Usuarios Totales</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 hover:border-emerald-200 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-emerald-100">
                <Package className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.resources.products.toLocaleString()}</p>
                <p className="text-sm text-slate-500">Productos Totales</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 hover:border-amber-200 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-amber-100">
                <RefreshCw className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.sync.this_week}</p>
                <p className="text-sm text-slate-500">Syncs esta semana</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 hover:border-rose-200 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-rose-100">
                <AlertCircle className="w-6 h-6 text-rose-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.sync.errors_this_week}</p>
                <p className="text-sm text-slate-500">Errores Sync</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Users by Role */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Users className="w-5 h-5 text-indigo-600" />
              Usuarios por Rol
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center">
              <ResponsiveContainer width="50%" height="100%">
                <PieChart>
                  <Pie
                    data={usersByRoleData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {usersByRoleData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-3">
                {Object.entries(stats.users.by_role).map(([role, count]) => {
                  const config = ROLE_CONFIG[role];
                  const Icon = config?.icon || Users;
                  return (
                    <div key={role} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ROLE_COLORS[role] }} />
                        <Icon className="w-4 h-4 text-slate-500" />
                        <span className="text-sm text-slate-600">{config?.label || role}</span>
                      </div>
                      <Badge className={config?.color || "bg-slate-100"}>{count}</Badge>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Resources Overview */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Database className="w-5 h-5 text-emerald-600" />
              Recursos de la Plataforma
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resourcesData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={100} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* WooCommerce & Top Users */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* WooCommerce Stats */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <ShoppingCart className="w-5 h-5 text-purple-600" />
              WooCommerce
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-slate-500" />
                <span className="text-sm text-slate-600">Total Tiendas</span>
              </div>
              <span className="font-semibold text-slate-900">{stats.woocommerce.total}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span className="text-sm text-emerald-700">Conectadas</span>
              </div>
              <span className="font-semibold text-emerald-700">{stats.woocommerce.connected}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-indigo-500" />
                <span className="text-sm text-indigo-700">Auto-Sync</span>
              </div>
              <span className="font-semibold text-indigo-700">{stats.woocommerce.auto_sync}</span>
            </div>
          </CardContent>
        </Card>

        {/* Top Users by Suppliers */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <TrendingUp className="w-5 h-5 text-amber-600" />
              Top por Proveedores
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.top_users.by_suppliers.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-4">Sin datos</p>
              ) : (
                stats.top_users.by_suppliers.map((u, i) => (
                  <div key={u.user_id} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-xs font-bold">
                        {i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{u.name}</p>
                        <p className="text-xs text-slate-500 truncate max-w-[120px]">{u.email}</p>
                      </div>
                    </div>
                    <Badge className="bg-amber-100 text-amber-700">{u.count}</Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Top Users by Products */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              Top por Productos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.top_users.by_products.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-4">Sin datos</p>
              ) : (
                stats.top_users.by_products.map((u, i) => (
                  <div key={u.user_id} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-xs font-bold">
                        {i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{u.name}</p>
                        <p className="text-xs text-slate-500 truncate max-w-[120px]">{u.email}</p>
                      </div>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700">{u.count.toLocaleString()}</Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Users */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <Activity className="w-5 h-5 text-indigo-600" />
            Usuarios Recientes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {stats.users.recent.map((u) => {
              const roleConfig = ROLE_CONFIG[u.role] || ROLE_CONFIG.user;
              const Icon = roleConfig.icon;
              return (
                <div key={u.id} className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      u.role === "superadmin" ? "bg-purple-100" : u.role === "admin" ? "bg-indigo-100" : "bg-slate-200"
                    }`}>
                      <span className={`text-sm font-semibold ${
                        u.role === "superadmin" ? "text-purple-600" : u.role === "admin" ? "text-indigo-600" : "text-slate-600"
                      }`}>
                        {u.name?.charAt(0).toUpperCase() || "U"}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{u.name}</p>
                      <p className="text-xs text-slate-500 truncate">{u.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <Badge className={roleConfig.color}>{roleConfig.label}</Badge>
                    <span className="text-xs text-slate-400">{formatDate(u.created_at)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* System Administration - Danger Zone */}
      <Card className="border-rose-200 bg-rose-50/30 mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg text-rose-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
            <AlertTriangle className="w-5 h-5" />
            Zona de Peligro
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-rose-200">
            <div>
              <h3 className="font-semibold text-slate-900">Reiniciar Aplicación</h3>
              <p className="text-sm text-slate-500">
                Elimina todos los datos de la aplicación (proveedores, productos, catálogos, tiendas, etc.) 
                <strong className="text-slate-700"> excepto los usuarios</strong>.
              </p>
            </div>
            <Button 
              variant="destructive" 
              onClick={() => setShowResetDialog(true)}
              className="bg-rose-600 hover:bg-rose-700"
              data-testid="reset-app-btn"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Reiniciar App
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reset Confirmation Dialog */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-rose-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <AlertTriangle className="w-5 h-5" />
              ¿Reiniciar la Aplicación?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>
                  Esta acción eliminará <strong>permanentemente</strong> todos los datos de la aplicación:
                </p>
                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                  <li>Todos los proveedores y sus configuraciones</li>
                  <li>Todos los productos importados</li>
                  <li>Todos los catálogos y categorías</li>
                  <li>Todas las tiendas configuradas</li>
                  <li>Todo el historial de sincronización</li>
                  <li>Todas las configuraciones de la app</li>
                </ul>
                <p className="text-emerald-600 font-medium">
                  ✓ Los usuarios se mantendrán intactos
                </p>
                <div className="pt-2">
                  <Label htmlFor="reset-confirm" className="text-slate-700">
                    Escribe <strong>RESET</strong> para confirmar:
                  </Label>
                  <Input
                    id="reset-confirm"
                    value={resetConfirmation}
                    onChange={(e) => setResetConfirmation(e.target.value.toUpperCase())}
                    placeholder="RESET"
                    className="mt-2 border-rose-200 focus:border-rose-400"
                    data-testid="reset-confirmation-input"
                  />
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              onClick={() => {
                setResetConfirmation("");
                setShowResetDialog(false);
              }}
              className="btn-secondary"
            >
              Cancelar
            </AlertDialogCancel>
            <Button
              onClick={handleResetApplication}
              disabled={resetConfirmation !== "RESET" || resetting}
              className="bg-rose-600 hover:bg-rose-700 text-white"
              data-testid="confirm-reset-btn"
            >
              {resetting ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              {resetting ? "Reiniciando..." : "Reiniciar Aplicación"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default SuperAdminDashboard;
