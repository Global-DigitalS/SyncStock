import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Truck,
  Package,
  BookOpen,
  AlertTriangle,
  TrendingUp,
  Bell,
  ArrowRight,
  PackageX,
  RefreshCw,
  ShoppingCart,
  Wifi,
  WifiOff,
  Zap,
  Clock,
  Upload,
  ExternalLink
} from "lucide-react";

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [stockAlerts, setStockAlerts] = useState({ low_stock: [], out_of_stock: [] });
  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, alertsRes, syncRes] = await Promise.all([
        api.get("/dashboard/stats"),
        api.get("/dashboard/stock-alerts"),
        api.get("/dashboard/sync-status")
      ]);
      setStats(statsRes.data);
      setStockAlerts(alertsRes.data);
      setSyncStatus(syncRes.data);
    } catch (error) {
      toast.error("Error al cargar el panel de control");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatDate = (dateStr) => {
    if (!dateStr) return "Nunca";
    const date = new Date(dateStr);
    return date.toLocaleString("es-ES", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  const statCards = [
    { title: "Proveedores", value: stats?.total_suppliers || 0, icon: Truck, color: "text-blue-600", bgColor: "bg-blue-50", link: "/suppliers" },
    { title: "Productos", value: stats?.total_products || 0, icon: Package, color: "text-emerald-600", bgColor: "bg-emerald-50", link: "/products" },
    { title: "Catálogos", value: stats?.total_catalogs || 0, icon: BookOpen, color: "text-indigo-600", bgColor: "bg-indigo-50", link: "/catalogs" },
    { title: "Stock Bajo", value: stats?.low_stock_count || 0, icon: AlertTriangle, color: "text-amber-600", bgColor: "bg-amber-50", link: "/products?stock=low" },
    { title: "Sin Stock", value: stats?.out_of_stock_count || 0, icon: PackageX, color: "text-rose-600", bgColor: "bg-rose-50", link: "/products?stock=out" },
    { title: "Cambios Precio", value: stats?.recent_price_changes || 0, icon: TrendingUp, color: "text-purple-600", bgColor: "bg-purple-50", link: "/price-history", subtitle: "últimos 7 días" },
  ];

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Panel de Control
        </h1>
        <p className="text-slate-500">Resumen de tu actividad y alertas importantes</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Link key={index} to={stat.link} className="stat-card group" data-testid={`stat-${stat.title.toLowerCase().replace(/ /g, '-')}`}>
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-sm ${stat.bgColor}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} strokeWidth={1.5} />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-400 transition-colors" />
              </div>
              <p className="numeric-value font-mono">{stat.value.toLocaleString()}</p>
              <p className="text-sm text-slate-500 mt-1">{stat.title}</p>
              {stat.subtitle && <p className="text-xs text-slate-400 mt-0.5">{stat.subtitle}</p>}
            </Link>
          );
        })}
      </div>

      {/* WooCommerce Sync Status */}
      {(stats?.woocommerce_stores > 0 || (syncStatus?.woocommerce_stores?.length > 0)) && (
        <Card className="border-slate-200 mb-6" data-testid="woocommerce-sync-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <ShoppingCart className="w-5 h-5 text-purple-500" strokeWidth={1.5} />
                Sincronización WooCommerce
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge className="bg-purple-100 text-purple-700 border-0">
                  {stats?.woocommerce_stores || 0} tiendas
                </Badge>
                {stats?.woocommerce_auto_sync > 0 && (
                  <Badge className="bg-emerald-100 text-emerald-700 border-0">
                    <Zap className="w-3 h-3 mr-1" />
                    {stats.woocommerce_auto_sync} auto-sync
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="p-3 bg-slate-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-slate-900 font-mono">{stats?.woocommerce_stores || 0}</p>
                <p className="text-xs text-slate-500">Tiendas</p>
              </div>
              <div className="p-3 bg-emerald-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-emerald-700 font-mono">{stats?.woocommerce_connected || 0}</p>
                <p className="text-xs text-emerald-600">Conectadas</p>
              </div>
              <div className="p-3 bg-indigo-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-indigo-700 font-mono">{stats?.woocommerce_auto_sync || 0}</p>
                <p className="text-xs text-indigo-600">Auto-Sync</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-700 font-mono">{stats?.woocommerce_total_synced || 0}</p>
                <p className="text-xs text-purple-600">Productos Sync</p>
              </div>
            </div>

            {syncStatus?.woocommerce_stores?.length > 0 && (
              <div className="space-y-2">
                {syncStatus.woocommerce_stores.map((store) => (
                  <div key={store.id} className="flex items-center justify-between p-3 border border-slate-100 rounded-lg hover:bg-slate-50 transition-colors" data-testid={`dashboard-wc-${store.id}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${store.is_connected ? 'bg-emerald-100' : 'bg-slate-100'}`}>
                        {store.is_connected ? <Wifi className="w-4 h-4 text-emerald-600" /> : <WifiOff className="w-4 h-4 text-slate-400" />}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{store.name}</p>
                        <p className="text-xs text-slate-500">{store.store_url?.replace(/^https?:\/\//, '').slice(0, 30)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {store.catalog_name && (
                        <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">
                          <BookOpen className="w-3 h-3 mr-1" />
                          {store.catalog_name}
                        </Badge>
                      )}
                      {store.auto_sync_enabled ? (
                        <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">
                          <Zap className="w-3 h-3 mr-1" />
                          Activo
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-slate-400 text-xs">
                          <Clock className="w-3 h-3 mr-1" />
                          Manual
                        </Badge>
                      )}
                      <div className="text-right">
                        <p className="text-xs font-mono text-slate-700">{store.products_synced} prod.</p>
                        <p className="text-xs text-slate-400">{formatDate(store.last_sync)}</p>
                      </div>
                    </div>
                  </div>
                ))}
                <Link to="/woocommerce" className="block text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium py-2">
                  Gestionar tiendas WooCommerce <ArrowRight className="w-3 h-3 inline ml-1" />
                </Link>
              </div>
            )}

            {(!syncStatus?.woocommerce_stores || syncStatus.woocommerce_stores.length === 0) && (
              <div className="text-center py-4">
                <p className="text-sm text-slate-500 mb-2">No hay tiendas WooCommerce configuradas</p>
                <Link to="/woocommerce">
                  <Button size="sm" className="btn-primary">
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    Configurar Tienda
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Alerts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <AlertTriangle className="w-5 h-5 text-amber-500" strokeWidth={1.5} />
                Stock Bajo
              </CardTitle>
              <Badge variant="secondary" className="badge-warning">{stockAlerts.low_stock.length} productos</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {stockAlerts.low_stock.length === 0 ? (
              <p className="text-slate-500 text-sm py-4 text-center">No hay productos con stock bajo</p>
            ) : (
              <div className="space-y-3">
                {stockAlerts.low_stock.slice(0, 5).map((product) => (
                  <div key={product.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{product.name}</p>
                      <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
                    </div>
                    <span className="badge-warning font-mono text-xs">{product.stock} uds</span>
                  </div>
                ))}
                {stockAlerts.low_stock.length > 5 && (
                  <Link to="/products?stock=low" className="block text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium py-2">
                    Ver todos ({stockAlerts.low_stock.length})
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <PackageX className="w-5 h-5 text-rose-500" strokeWidth={1.5} />
                Sin Stock
              </CardTitle>
              <Badge variant="secondary" className="badge-error">{stockAlerts.out_of_stock.length} productos</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {stockAlerts.out_of_stock.length === 0 ? (
              <p className="text-slate-500 text-sm py-4 text-center">Todos los productos tienen stock disponible</p>
            ) : (
              <div className="space-y-3">
                {stockAlerts.out_of_stock.slice(0, 5).map((product) => (
                  <div key={product.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{product.name}</p>
                      <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
                    </div>
                    <span className="badge-error font-mono text-xs">Sin stock</span>
                  </div>
                ))}
                {stockAlerts.out_of_stock.length > 5 && (
                  <Link to="/products?stock=out" className="block text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium py-2">
                    Ver todos ({stockAlerts.out_of_stock.length})
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Notifications */}
      {syncStatus?.recent_notifications?.length > 0 && (
        <Card className="border-slate-200 mb-6" data-testid="recent-notifications-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <Bell className="w-5 h-5 text-indigo-500" strokeWidth={1.5} />
                Actividad Reciente
              </CardTitle>
              <Link to="/notifications" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                Ver todas
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {syncStatus.recent_notifications.map((notif) => (
                <div key={notif.id} className={`flex items-start gap-3 p-2 rounded-lg ${notif.read ? 'bg-white' : 'bg-indigo-50'}`}>
                  <div className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 ${
                    notif.type === 'sync_complete' ? 'bg-emerald-500' :
                    notif.type === 'sync_error' ? 'bg-rose-500' :
                    notif.type === 'stock_out' ? 'bg-rose-500' :
                    notif.type === 'stock_low' ? 'bg-amber-500' :
                    'bg-indigo-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-700">{notif.message}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{formatDate(notif.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Link to="/suppliers">
              <Button variant="outline" className="btn-secondary" data-testid="quick-add-supplier">
                <Truck className="w-4 h-4 mr-2" strokeWidth={1.5} />
                Añadir Proveedor
              </Button>
            </Link>
            <Link to="/products">
              <Button variant="outline" className="btn-secondary" data-testid="quick-import-products">
                <Package className="w-4 h-4 mr-2" strokeWidth={1.5} />
                Importar Productos
              </Button>
            </Link>
            <Link to="/woocommerce">
              <Button variant="outline" className="btn-secondary" data-testid="quick-woocommerce">
                <ShoppingCart className="w-4 h-4 mr-2" strokeWidth={1.5} />
                WooCommerce
              </Button>
            </Link>
            <Link to="/export">
              <Button variant="outline" className="btn-secondary" data-testid="quick-export">
                <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
                Exportar Catálogo
              </Button>
            </Link>
            <Link to="/notifications">
              <Button variant="outline" className="btn-secondary relative" data-testid="quick-notifications">
                <Bell className="w-4 h-4 mr-2" strokeWidth={1.5} />
                Notificaciones
                {stats?.unread_notifications > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 text-white text-xs rounded-full flex items-center justify-center">
                    {stats.unread_notifications > 9 ? "9+" : stats.unread_notifications}
                  </span>
                )}
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
