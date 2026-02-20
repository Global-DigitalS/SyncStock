import { useState, useEffect } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Bell, CheckCheck, ShoppingCart, AlertTriangle, PackageX, TrendingUp, RefreshCw, Info } from "lucide-react";

const NOTIFICATION_ICONS = {
  sync_complete: { icon: RefreshCw, color: "text-emerald-600", bg: "bg-emerald-50" },
  sync_error: { icon: AlertTriangle, color: "text-rose-600", bg: "bg-rose-50" },
  stock_out: { icon: PackageX, color: "text-rose-600", bg: "bg-rose-50" },
  stock_low: { icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50" },
  woocommerce_export: { icon: ShoppingCart, color: "text-purple-600", bg: "bg-purple-50" },
  price_change: { icon: TrendingUp, color: "text-blue-600", bg: "bg-blue-50" },
};

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetchNotifications = async () => {
    try {
      const params = filter === "unread" ? "?unread_only=true" : "";
      const res = await api.get(`/notifications${params}`);
      setNotifications(res.data);
    } catch (error) {
      toast.error("Error al cargar notificaciones");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const markRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    } catch (error) {
      toast.error("Error al marcar como leída");
    }
  };

  const markAllRead = async () => {
    try {
      await api.put("/notifications/read-all");
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      toast.success("Todas las notificaciones marcadas como leídas");
    } catch (error) {
      toast.error("Error al marcar todas como leídas");
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
    return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="notifications-title">
            Notificaciones
          </h1>
          <p className="text-slate-500">
            {unreadCount > 0 ? `${unreadCount} sin leer` : "Todas leídas"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-slate-200 overflow-hidden">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${filter === "all" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
              data-testid="filter-all"
            >
              Todas
            </button>
            <button
              onClick={() => setFilter("unread")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${filter === "unread" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
              data-testid="filter-unread"
            >
              Sin leer
            </button>
          </div>
          {unreadCount > 0 && (
            <Button variant="outline" onClick={markAllRead} className="btn-secondary" data-testid="mark-all-read-btn">
              <CheckCheck className="w-4 h-4 mr-2" />
              Marcar todas como leídas
            </Button>
          )}
        </div>
      </div>

      {notifications.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Bell className="w-12 h-12 text-slate-300 mb-4" />
            <p className="text-slate-500 text-lg">No hay notificaciones</p>
            <p className="text-slate-400 text-sm mt-1">Las alertas de stock, sincronización y precios aparecerán aquí</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifications.map((notif) => {
            const config = NOTIFICATION_ICONS[notif.type] || { icon: Info, color: "text-slate-600", bg: "bg-slate-50" };
            const Icon = config.icon;
            return (
              <div
                key={notif.id}
                onClick={() => !notif.read && markRead(notif.id)}
                className={`flex items-start gap-4 p-4 rounded-lg border transition-all cursor-pointer ${
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
                  <p className={`text-sm ${notif.read ? "text-slate-600" : "text-slate-900 font-medium"}`}>
                    {notif.message}
                  </p>
                  {notif.product_name && (
                    <p className="text-xs text-slate-500 mt-0.5 font-mono">{notif.product_name}</p>
                  )}
                  <p className="text-xs text-slate-400 mt-1">{formatDate(notif.created_at)}</p>
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
