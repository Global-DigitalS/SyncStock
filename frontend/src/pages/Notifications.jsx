import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Bell,
  Check,
  CheckCheck,
  AlertTriangle,
  PackageX,
  TrendingUp,
  Clock
} from "lucide-react";

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await api.get("/notifications");
      setNotifications(res.data);
    } catch (error) {
      toast.error("Error al cargar las notificaciones");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(notifications.map(n => 
        n.id === id ? { ...n, read: true } : n
      ));
    } catch (error) {
      toast.error("Error al marcar como leída");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put("/notifications/read-all");
      setNotifications(notifications.map(n => ({ ...n, read: true })));
      toast.success("Todas las notificaciones marcadas como leídas");
    } catch (error) {
      toast.error("Error al marcar todas como leídas");
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case "stock_low":
        return <AlertTriangle className="w-5 h-5 text-amber-500" strokeWidth={1.5} />;
      case "stock_out":
        return <PackageX className="w-5 h-5 text-rose-500" strokeWidth={1.5} />;
      case "price_change":
        return <TrendingUp className="w-5 h-5 text-blue-500" strokeWidth={1.5} />;
      default:
        return <Bell className="w-5 h-5 text-slate-500" strokeWidth={1.5} />;
    }
  };

  const getBadge = (type) => {
    switch (type) {
      case "stock_low":
        return <Badge className="badge-warning">Stock Bajo</Badge>;
      case "stock_out":
        return <Badge className="badge-error">Sin Stock</Badge>;
      case "price_change":
        return <Badge className="bg-blue-50 text-blue-700 border-blue-200 border">Precio</Badge>;
      default:
        return <Badge variant="secondary">Info</Badge>;
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return "Hace unos minutos";
    if (hours < 24) return `Hace ${hours} hora${hours > 1 ? "s" : ""}`;
    if (days < 7) return `Hace ${days} día${days > 1 ? "s" : ""}`;
    return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
  };

  const unreadCount = notifications.filter(n => !n.read).length;

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
            Notificaciones
          </h1>
          <p className="text-slate-500">
            {unreadCount > 0 
              ? `${unreadCount} notificación${unreadCount > 1 ? "es" : ""} sin leer`
              : "Todas las notificaciones leídas"
            }
          </p>
        </div>
        {unreadCount > 0 && (
          <Button onClick={handleMarkAllRead} className="btn-secondary" data-testid="mark-all-read">
            <CheckCheck className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Marcar todas como leídas
          </Button>
        )}
      </div>

      {/* Notifications List */}
      {notifications.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Bell className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay notificaciones
          </h3>
          <p className="text-slate-500">
            Recibirás alertas cuando haya cambios de stock o precios en tus productos
          </p>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 divide-y divide-slate-100">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`flex items-start gap-4 p-4 transition-colors ${
                  !notification.read ? "bg-indigo-50/50" : "hover:bg-slate-50"
                }`}
                data-testid={`notification-${notification.id}`}
              >
                <div className="mt-0.5">
                  {getIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {getBadge(notification.type)}
                    {!notification.read && (
                      <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    )}
                  </div>
                  <p className={`text-sm ${notification.read ? "text-slate-600" : "text-slate-900 font-medium"}`}>
                    {notification.message}
                  </p>
                  {notification.product_name && (
                    <p className="text-xs text-slate-500 mt-1 font-mono">
                      {notification.product_name}
                    </p>
                  )}
                  <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                    <Clock className="w-3 h-3" strokeWidth={1.5} />
                    {formatDate(notification.created_at)}
                  </p>
                </div>
                {!notification.read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleMarkRead(notification.id)}
                    className="text-slate-400 hover:text-slate-600"
                    data-testid={`mark-read-${notification.id}`}
                  >
                    <Check className="w-4 h-4" strokeWidth={1.5} />
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Notifications;
