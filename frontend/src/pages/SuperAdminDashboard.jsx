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
  Activity, Database, Server, CheckCircle, XCircle, Trash2,
  AlertTriangle, Mail, CreditCard, Palette, Globe, Settings,
  UserPlus, BarChart2, Zap, ArrowRight, TrendingDown, Award,
  FileText, Bell
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, AreaChart, Area
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

const PLAN_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

const StatCard = ({ icon: Icon, value, label, sub, color, bg, trend }) => (
  <Card className="border-slate-200 hover:shadow-md transition-shadow">
    <CardContent className="p-5">
      <div className="flex items-start justify-between">
        <div className={`p-3 rounded-xl ${bg}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${trend >= 0 ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"}`}>
            {trend >= 0 ? "+" : ""}{trend}
          </span>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
      </div>
    </CardContent>
  </Card>
);

const QuickActionCard = ({ icon: Icon, label, desc, href, color, bg }) => {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(href)}
      className={`flex items-center gap-3 p-4 rounded-xl border border-slate-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left w-full bg-white`}
    >
      <div className={`p-2.5 rounded-lg ${bg} flex-shrink-0`}>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-800">{label}</p>
        <p className="text-xs text-slate-500 truncate">{desc}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-300 ml-auto flex-shrink-0" />
    </button>
  );
};

const SuperAdminDashboard = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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

  const fetchStats = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
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
      setRefreshing(false);
    }
  };

  const formatDate = (dateStr) =>
    new Date(dateStr).toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });

  const formatDateShort = (dateStr) =>
    new Date(dateStr).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });

  const handleResetApplication = async () => {
    if (resetConfirmation !== "RESET") {
      toast.error("Escribe 'RESET' para confirmar");
      return;
    }
    setResetting(true);
    try {
      const res = await api.post("/admin/system/reset", { confirmation_text: "RESET" });
      toast.success(res.data.message);
      setShowResetDialog(false);
      setResetConfirmation("");
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al reiniciar la aplicación");
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6 lg:p-8">
        <div className="empty-state">
          <AlertCircle className="w-16 h-16 text-slate-300 mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Error al cargar</h2>
          <p className="text-slate-500">No se pudieron cargar las estadísticas globales.</p>
          <Button onClick={() => fetchStats()} className="mt-4">Reintentar</Button>
        </div>
      </div>
    );
  }

  const usersByRoleData = Object.entries(stats.users.by_role).map(([role, count]) => ({
    name: ROLE_CONFIG[role]?.label || role,
    value: count,
    color: ROLE_COLORS[role] || "#94a3b8"
  }));

  const syncSuccessRate = stats.sync.success_rate || 0;

  return (
    <div className="p-6 lg:p-8 animate-fade-in space-y-6">

      {/* ── Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}
            data-testid="superadmin-dashboard-title">
            Panel de Administración
          </h1>
          <p className="text-slate-500 mt-1">Vista global de la plataforma · estadísticas y gestión</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchStats(true)}
          disabled={refreshing}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {/* ── KPI Row 1: Usuarios ── */}
      <div>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Usuarios</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard icon={Users} value={stats.users.total} label="Usuarios Totales"
            sub={`${stats.users.inactive} inactivos`} color="text-indigo-600" bg="bg-indigo-100" />
          <StatCard icon={CheckCircle} value={stats.users.active} label="Usuarios Activos"
            sub={`${Math.round(stats.users.active / (stats.users.total || 1) * 100)}% del total`}
            color="text-emerald-600" bg="bg-emerald-100" />
          <StatCard icon={UserPlus} value={stats.users.new_this_week} label="Nuevos esta semana"
            sub={`${stats.users.new_this_month} este mes`} color="text-sky-600" bg="bg-sky-100"
            trend={stats.users.new_this_week} />
          <StatCard icon={Award} value={stats.plans[0]?.plan || "—"} label="Plan más popular"
            sub={`${stats.plans[0]?.count || 0} usuarios`} color="text-amber-600" bg="bg-amber-100" />
        </div>
      </div>

      {/* ── KPI Row 2: Plataforma & Sync ── */}
      <div>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Plataforma y Sincronización</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard icon={Package} value={stats.resources.products.toLocaleString()} label="Productos Totales"
            sub={`${stats.resources.suppliers} proveedores`} color="text-emerald-600" bg="bg-emerald-100" />
          <StatCard icon={RefreshCw} value={stats.sync.this_week} label="Syncs esta semana"
            sub={`${stats.sync.total.toLocaleString()} totales`} color="text-amber-600" bg="bg-amber-100" />
          <StatCard icon={TrendingUp} value={`${syncSuccessRate}%`} label="Tasa de éxito sync"
            sub={`${stats.sync.errors_this_week} errores`}
            color={syncSuccessRate >= 80 ? "text-emerald-600" : "text-rose-600"}
            bg={syncSuccessRate >= 80 ? "bg-emerald-100" : "bg-rose-100"} />
          <StatCard icon={BarChart2} value={stats.pricing.changes_this_week} label="Cambios de precio"
            sub="últimos 7 días" color="text-purple-600" bg="bg-purple-100" />
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Acciones Rápidas</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickActionCard icon={Users} label="Gestión de Usuarios" desc="Ver, editar y gestionar cuentas"
            href="/admin/users" color="text-indigo-600" bg="bg-indigo-100" />
          <QuickActionCard icon={CreditCard} label="Planes y Suscripciones" desc="Precios, límites y features"
            href="/admin/plans" color="text-emerald-600" bg="bg-emerald-100" />
          <QuickActionCard icon={Palette} label="Personalización" desc="Logo, colores y branding"
            href="/admin/branding" color="text-amber-600" bg="bg-amber-100" />
          <QuickActionCard icon={Mail} label="Config. Email" desc="Cuentas SMTP y plantillas"
            href="/admin/email-config" color="text-sky-600" bg="bg-sky-100" />
          <QuickActionCard icon={CreditCard} label="Config. Stripe" desc="Pasarela de pago"
            href="/admin/stripe" color="text-purple-600" bg="bg-purple-100" />
          <QuickActionCard icon={Globe} label="Landing Page" desc="Contenido de la web pública"
            href="/admin/landing" color="text-rose-600" bg="bg-rose-100" />
          <QuickActionCard icon={FileText} label="Plantillas Email" desc="Bienvenida, reset, suscripción"
            href="/admin/email-templates" color="text-slate-600" bg="bg-slate-100" />
          <QuickActionCard icon={Settings} label="Google Services" desc="Analytics, GTM, Ads"
            href="/admin/google-services" color="text-orange-600" bg="bg-orange-100" />
        </div>
      </div>

      {/* ── Estado del Sistema ── */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
            <Server className="w-4 h-4 text-indigo-600" />
            Estado del Sistema
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              {
                label: "Email SMTP",
                ok: stats.system.email_configured,
                ok_text: "Configurado",
                err_text: "Sin configurar",
                href: "/admin/email-config"
              },
              {
                label: "Stripe",
                ok: stats.system.stripe_configured,
                ok_text: "Configurado",
                err_text: "Sin configurar",
                href: "/admin/stripe"
              },
              {
                label: "Tiendas conectadas",
                ok: stats.woocommerce.connected > 0,
                ok_text: `${stats.woocommerce.connected} activas`,
                err_text: "Ninguna activa",
                href: "/stores"
              },
              {
                label: "Tasa sync semanal",
                ok: syncSuccessRate >= 80,
                ok_text: `${syncSuccessRate}% éxito`,
                err_text: `${syncSuccessRate}% (bajo)`,
                href: "/sync-history"
              },
            ].map(({ label, ok, ok_text, err_text, href }) => (
              <button
                key={label}
                onClick={() => navigate(href)}
                className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors text-left"
              >
                {ok
                  ? <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  : <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                }
                <div>
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className={`text-sm font-semibold ${ok ? "text-emerald-700" : "text-rose-600"}`}>
                    {ok ? ok_text : err_text}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Gráficas Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Usuarios por Rol */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <Users className="w-4 h-4 text-indigo-600" />
              Usuarios por Rol
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-center">
              <ResponsiveContainer width="55%" height="100%">
                <PieChart>
                  <Pie data={usersByRoleData} cx="50%" cy="50%" innerRadius={40} outerRadius={65}
                    paddingAngle={2} dataKey="value">
                    {usersByRoleData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2.5">
                {Object.entries(stats.users.by_role).map(([role, count]) => {
                  const config = ROLE_CONFIG[role];
                  const Icon = config?.icon || Users;
                  return (
                    <div key={role} className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: ROLE_COLORS[role] }} />
                        <Icon className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-xs text-slate-600">{config?.label || role}</span>
                      </div>
                      <Badge className={`${config?.color || "bg-slate-100"} text-xs`}>{count}</Badge>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Distribución de Planes */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <CreditCard className="w-4 h-4 text-emerald-600" />
              Distribución de Planes
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.plans.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">Sin datos de planes</p>
            ) : (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.plans} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="plan" width={80} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {stats.plans.map((_, i) => (
                        <Cell key={i} fill={PLAN_COLORS[i % PLAN_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recursos de la Plataforma */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <Database className="w-4 h-4 text-purple-600" />
              Recursos Totales
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Proveedores", value: stats.resources.suppliers, color: "bg-indigo-500", icon: Truck },
              { label: "Productos", value: stats.resources.products, color: "bg-emerald-500", icon: Package },
              { label: "Catálogos", value: stats.resources.catalogs, color: "bg-amber-500", icon: BookOpen },
              { label: "Tiendas", value: stats.resources.woocommerce_stores, color: "bg-rose-500", icon: ShoppingCart },
            ].map(({ label, value, color, icon: Icon }) => {
              const max = Math.max(stats.resources.suppliers, stats.resources.products, stats.resources.catalogs, stats.resources.woocommerce_stores) || 1;
              const pct = Math.round(value / max * 100);
              return (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <div className="flex items-center gap-1.5 text-slate-600">
                      <Icon className="w-3.5 h-3.5" />
                      {label}
                    </div>
                    <span className="font-semibold text-slate-700">{value.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* ── Actividad Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Registros diarios (14 días) */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <UserPlus className="w-4 h-4 text-sky-600" />
              Registros diarios (14 días)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.users.daily_registrations.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">Sin registros recientes</p>
            ) : (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={stats.users.daily_registrations}>
                    <defs>
                      <linearGradient id="regGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip labelFormatter={d => `Día ${d}`} />
                    <Area type="monotone" dataKey="count" stroke="#6366f1" fill="url(#regGrad)"
                      strokeWidth={2} name="Registros" dot={{ r: 3, fill: "#6366f1" }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sync diario (14 días) */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <RefreshCw className="w-4 h-4 text-amber-600" />
              Sincronizaciones diarias (14 días)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.sync.daily.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">Sin sincronizaciones recientes</p>
            ) : (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.sync.daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tickFormatter={d => d.slice(5)} tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip labelFormatter={d => `Día ${d}`} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="success" stackId="a" fill="#10b981" name="Éxito" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="errors" stackId="a" fill="#ef4444" name="Error" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Tiendas + Top usuarios ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Tiendas Online */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <ShoppingCart className="w-4 h-4 text-purple-600" />
              Tiendas Online
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Total", value: stats.woocommerce.total, icon: Server, cls: "bg-slate-50 text-slate-700" },
              { label: "Conectadas", value: stats.woocommerce.connected, icon: CheckCircle, cls: "bg-emerald-50 text-emerald-700" },
              { label: "Auto-Sync", value: stats.woocommerce.auto_sync, icon: Zap, cls: "bg-indigo-50 text-indigo-700" },
            ].map(({ label, value, icon: Icon, cls }) => (
              <div key={label} className={`flex items-center justify-between p-3 rounded-lg ${cls}`}>
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{label}</span>
                </div>
                <span className="font-semibold">{value}</span>
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full mt-2 text-xs"
              onClick={() => navigate("/stores")}>
              Ver tiendas <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          </CardContent>
        </Card>

        {/* Top por Proveedores */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <TrendingUp className="w-4 h-4 text-amber-600" />
              Top por Proveedores
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2.5">
              {stats.top_users.by_suppliers.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">Sin datos</p>
              ) : stats.top_users.by_suppliers.map((u, i) => (
                <div key={u.user_id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-slate-900 truncate">{u.name}</p>
                      <p className="text-xs text-slate-400 truncate max-w-[110px]">{u.email}</p>
                    </div>
                  </div>
                  <Badge className="bg-amber-100 text-amber-700 text-xs">{u.count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top por Productos */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              Top por Productos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2.5">
              {stats.top_users.by_products.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">Sin datos</p>
              ) : stats.top_users.by_products.map((u, i) => (
                <div key={u.user_id} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-slate-900 truncate">{u.name}</p>
                      <p className="text-xs text-slate-400 truncate max-w-[110px]">{u.email}</p>
                    </div>
                  </div>
                  <Badge className="bg-emerald-100 text-emerald-700 text-xs">{u.count.toLocaleString()}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Errores Recientes de Sync ── */}
      {stats.sync.recent_errors.length > 0 && (
        <Card className="border-rose-100">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base text-rose-700" style={{ fontFamily: "Manrope, sans-serif" }}>
                <AlertCircle className="w-4 h-4" />
                Errores Recientes de Sincronización
              </CardTitle>
              <Button variant="outline" size="sm" className="text-xs" onClick={() => navigate("/sync-history")}>
                Ver historial <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {stats.sync.recent_errors.map((err, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-rose-50 rounded-lg border border-rose-100">
                  <XCircle className="w-4 h-4 text-rose-500 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-800 truncate">{err.supplier_name || "Proveedor desconocido"}</p>
                    <p className="text-xs text-rose-600 truncate">{err.error_message || "Sin descripción"}</p>
                  </div>
                  <span className="text-xs text-slate-400 flex-shrink-0">
                    {err.created_at ? formatDateShort(err.created_at) : ""}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Usuarios Recientes ── */}
      <Card className="border-slate-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base" style={{ fontFamily: "Manrope, sans-serif" }}>
              <Activity className="w-4 h-4 text-indigo-600" />
              Usuarios Recientes
            </CardTitle>
            <Button variant="outline" size="sm" className="text-xs" onClick={() => navigate("/admin/users")}>
              Ver todos <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {stats.users.recent.map((u) => {
              const roleConfig = ROLE_CONFIG[u.role] || ROLE_CONFIG.user;
              const Icon = roleConfig.icon;
              const isInactive = u.is_active === false;
              return (
                <div key={u.id} className={`p-4 rounded-xl border transition-colors ${isInactive ? "bg-slate-50 border-slate-200 opacity-60" : "bg-white border-slate-100 hover:border-indigo-200"}`}>
                  <div className="flex items-center gap-2.5 mb-3">
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                      u.role === "superadmin" ? "bg-purple-100" : u.role === "admin" ? "bg-indigo-100" : "bg-slate-100"
                    }`}>
                      <span className={`text-sm font-bold ${
                        u.role === "superadmin" ? "text-purple-600" : u.role === "admin" ? "text-indigo-600" : "text-slate-600"
                      }`}>
                        {u.name?.charAt(0).toUpperCase() || "U"}
                      </span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{u.name}</p>
                      <p className="text-xs text-slate-400 truncate">{u.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <Badge className={`${roleConfig.color} text-xs`}>{roleConfig.label}</Badge>
                    <div className="flex items-center gap-1.5">
                      {isInactive && (
                        <span className="w-2 h-2 rounded-full bg-slate-300" title="Inactivo" />
                      )}
                      <span className="text-xs text-slate-400">{u.created_at ? formatDate(u.created_at) : ""}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Zona de Peligro ── */}
      <Card className="border-rose-200 bg-rose-50/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-rose-700" style={{ fontFamily: "Manrope, sans-serif" }}>
            <AlertTriangle className="w-4 h-4" />
            Zona de Peligro
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-rose-200">
            <div>
              <h3 className="font-semibold text-slate-900">Reiniciar Aplicación</h3>
              <p className="text-sm text-slate-500 mt-0.5">
                Elimina todos los datos (proveedores, productos, catálogos, tiendas…){" "}
                <strong className="text-slate-700">excepto los usuarios</strong>.
              </p>
            </div>
            <Button variant="destructive" onClick={() => setShowResetDialog(true)}
              className="bg-rose-600 hover:bg-rose-700 flex-shrink-0 ml-4"
              data-testid="reset-app-btn">
              <Trash2 className="w-4 h-4 mr-2" />
              Reiniciar App
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Reset Dialog ── */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-rose-700" style={{ fontFamily: "Manrope, sans-serif" }}>
              <AlertTriangle className="w-5 h-5" />
              ¿Reiniciar la Aplicación?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3">
                <p>Esta acción eliminará <strong>permanentemente</strong> todos los datos:</p>
                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                  <li>Todos los proveedores y sus configuraciones</li>
                  <li>Todos los productos importados</li>
                  <li>Todos los catálogos y categorías</li>
                  <li>Todas las tiendas configuradas</li>
                  <li>Todo el historial de sincronización</li>
                  <li>Todas las configuraciones de la app</li>
                </ul>
                <p className="text-emerald-600 font-medium">✓ Los usuarios se mantendrán intactos</p>
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
            <AlertDialogCancel onClick={() => { setResetConfirmation(""); setShowResetDialog(false); }} className="btn-secondary">
              Cancelar
            </AlertDialogCancel>
            <Button
              onClick={handleResetApplication}
              disabled={resetConfirmation !== "RESET" || resetting}
              className="bg-rose-600 hover:bg-rose-700 text-white"
              data-testid="confirm-reset-btn">
              {resetting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
              {resetting ? "Reiniciando..." : "Reiniciar Aplicación"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default SuperAdminDashboard;
