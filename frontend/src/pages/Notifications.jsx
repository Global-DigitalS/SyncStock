import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  Bell, CheckCheck, ShoppingCart, AlertTriangle, PackageX, TrendingUp,
  RefreshCw, Info, Trash2, X, Filter
} from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuTrigger, DropdownMenuSeparator
} from "../components/ui/dropdown-menu";

const NOTIFICATION_ICONS = {
  sync_complete: { icon: RefreshCw, color: "text-emerald-600", bg: "bg-emerald-50", label: "Sincronización" },
  sync_error: { icon: AlertTriangle, color: "text-rose-600", bg: "bg-rose-50", label: "Error" },
  stock_out: { icon: PackageX, color: "text-rose-600", bg: "bg-rose-50", label: "Sin stock" },
  stock_low: { icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50", label: "Stock bajo" },
  woocommerce_export: { icon: ShoppingCart, color: "text-purple-600", bg: "bg-purple-50", label: "Tienda Online" },
  price_change: { icon: TrendingUp, color: "text-blue-600", bg: "bg-blue-50", label: "Cambio precio" },
};

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const fetchNotifications = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter === "unread") params.append("unread_only", "true");
      const res = await api.get(`/notifications?${params.toString()}`);
      let data = res.data;
      if (typeFilter !== "all") {
        data = data.filter(n => n.type === typeFilter);
      }
      setNotifications(data);
    } catch (error) {
      toast.error("Error al cargar notificaciones");
    } finally {
      setLoading(false);
    }
  }, [filter, typeFilter]);

  const fetchStats = async () => {
    try {
      const res = await api.get("/notifications/stats");
      setStats(res.data);
    } catch (error) {
      // handled silently
    }
  };

  useEffect(() => {
    fetchNotifications();
    fetchStats();
  }, [fetchNotifications]);

  const markRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      setStats(prev => prev ? { ...prev, unread: Math.max(0, prev.unread - 1) } : prev);
    } catch (error) {
      toast.error("Error al marcar como leída");
    }
  };

  const markAllRead = async () => {
    try {
      await api.put("/notifications/read-all");
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setStats(prev => prev ? { ...prev, unread: 0 } : prev);
      toast.success("Todas las notificaciones marcadas como leídas");
    } catch (error) {
      toast.error("Error al marcar todas como leídas");
    }
  };

  const deleteNotification = async (id, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/notifications/${id}`);
      setNotifications(prev => prev.filter(n => n.id !== id));
      toast.success("Notificación eliminada");
      fetchStats();
    } catch (error) {
      toast.error("Error al eliminar notificación");
    }
  };

  const deleteReadNotifications = async () => {
    try {
      const res = await api.delete("/notifications?read_only=true");
      toast.success(res.data.message);
      fetchNotifications();
      fetchStats();
    } catch (error) {
      toast.error("Error al eliminar notificaciones");
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `Hace ${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `Hace ${hours}h`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `Hace ${days}d`;
    return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
  };

  const unreadCount = notifications.filter(n => !n.read).length;
  const readCount = notifications.filter(n => n.read).length;

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-1" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="notifications-title">
            Notificaciones
          </h1>
          <p className="text-slate-500 text-sm">
            {stats ? `${stats.total} total · ${stats.unread} sin leer` : "Cargando..."}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Type Filter Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-9" data-testid="type-filter-btn">
                <Filter className="w-4 h-4 mr-2" />
                {typeFilter === "all" ? "Todos los tipos" : NOTIFICATION_ICONS[typeFilter]?.label || typeFilter}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setTypeFilter("all")}>
                Todos los tipos
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {Object.entries(NOTIFICATION_ICONS).map(([key, val]) => (
                <DropdownMenuItem key={key} onClick={() => setTypeFilter(key)}>
                  <val.icon className={`w-4 h-4 mr-2 ${val.color}`} />
                  {val.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Read/Unread Filter */}
          <div className="flex rounded-lg border border-slate-200 overflow-hidden">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-2 text-sm font-medium transition-colors ${filter === "all" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
              data-testid="filter-all"
            >
              Todas
            </button>
            <button
              onClick={() => setFilter("unread")}
              className={`px-3 py-2 text-sm font-medium transition-colors ${filter === "unread" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
              data-testid="filter-unread"
            >
              Sin leer
            </button>
          </div>

          {/* Actions Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-9" data-testid="actions-dropdown">
                Acciones
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={markAllRead} disabled={unreadCount === 0}>
                <CheckCheck className="w-4 h-4 mr-2" />
                Marcar todas como leídas
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={deleteReadNotifications} disabled={readCount === 0} className="text-rose-600">
                <Trash2 className="w-4 h-4 mr-2" />
                Eliminar leídas ({readCount})
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && stats.unread > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          {Object.entries(NOTIFICATION_ICONS).map(([key, val]) => {
            const typeStats = stats.by_type[key];
            if (!typeStats || typeStats.total === 0) return null;
            const Icon = val.icon;
            return (
              <Card
                key={key}
                className={`cursor-pointer transition-all hover:shadow-md ${typeFilter === key ? "ring-2 ring-indigo-500" : ""}`}
                onClick={() => setTypeFilter(typeFilter === key ? "all" : key)}
                data-testid={`stat-card-${key}`}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded ${val.bg}`}>
                      <Icon className={`w-4 h-4 ${val.color}`} strokeWidth={1.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-500 truncate">{val.label}</p>
                      <div className="flex items-baseline gap-1">
                        <span className="text-lg font-bold text-slate-900">{typeStats.unread}</span>
                        {typeStats.total > typeStats.unread && (
                          <span className="text-xs text-slate-400">/ {typeStats.total}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Notifications List */}
      {notifications.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Bell className="w-12 h-12 text-slate-300 mb-4" />
            <p className="text-slate-500 text-lg">No hay notificaciones</p>
            <p className="text-slate-400 text-sm mt-1">
              {typeFilter !== "all"
                ? `No hay notificaciones de tipo "${NOTIFICATION_ICONS[typeFilter]?.label}"`
                : "Las alertas de stock, sincronización y precios aparecerán aquí"}
            </p>
            {typeFilter !== "all" && (
              <Button variant="outline" className="mt-4" onClick={() => setTypeFilter("all")}>
                Ver todas las notificaciones
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifications.map((notif) => {
            const config = NOTIFICATION_ICONS[notif.type] || { icon: Info, color: "text-slate-600", bg: "bg-slate-50", label: "Info" };
            const Icon = config.icon;
            return (
              <div
                key={notif.id}
                onClick={() => !notif.read && markRead(notif.id)}
                className={`group flex items-start gap-4 p-4 rounded-lg border transition-all cursor-pointer ${
                  notif.read
                    ? "bg-white border-slate-100 hover:bg-slate-50"
                    : "bg-indigo-50/50 border-indigo-100 hover:bg-indigo-50"
                }`}
                data-testid={`notification-${notif.id}`}
              >
                <div className={`p-2 rounded-lg flex-shrink-0 ${config.bg}`}>
                  <Icon className={`w-5 h-5 ${config.color}`} strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-sm ${notif.read ? "text-slate-600" : "text-slate-900 font-medium"}`}>
                      {notif.message}
                    </p>
                    <button
                      onClick={(e) => deleteNotification(notif.id, e)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-slate-200 rounded"
                      data-testid={`delete-notification-${notif.id}`}
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                  {notif.product_name && (
                    <p className="text-xs text-slate-500 mt-0.5 font-mono truncate">{notif.product_name}</p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${config.bg} ${config.color}`}>
                      {config.label}
                    </span>
                    <span className="text-xs text-slate-400">{formatDate(notif.created_at)}</span>
                  </div>
                </div>
                {!notif.read && (
                  <div className="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-2" />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Notifications;
