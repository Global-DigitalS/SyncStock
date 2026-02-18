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
  RefreshCw
} from "lucide-react";

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [stockAlerts, setStockAlerts] = useState({ low_stock: [], out_of_stock: [] });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, alertsRes] = await Promise.all([
        api.get("/dashboard/stats"),
        api.get("/dashboard/stock-alerts")
      ]);
      setStats(statsRes.data);
      setStockAlerts(alertsRes.data);
    } catch (error) {
      toast.error("Error al cargar el panel de control");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Proveedores",
      value: stats?.total_suppliers || 0,
      icon: Truck,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      link: "/suppliers"
    },
    {
      title: "Productos Totales",
      value: stats?.total_products || 0,
      icon: Package,
      color: "text-emerald-600",
      bgColor: "bg-emerald-50",
      link: "/products"
    },
    {
      title: "En Mi Catálogo",
      value: stats?.total_catalog_items || 0,
      icon: BookOpen,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
      link: "/catalog"
    },
    {
      title: "Stock Bajo",
      value: stats?.low_stock_count || 0,
      icon: AlertTriangle,
      color: "text-amber-600",
      bgColor: "bg-amber-50",
      link: "/products?stock=low"
    },
    {
      title: "Sin Stock",
      value: stats?.out_of_stock_count || 0,
      icon: PackageX,
      color: "text-rose-600",
      bgColor: "bg-rose-50",
      link: "/products?stock=out"
    },
    {
      title: "Cambios de Precio",
      value: stats?.recent_price_changes || 0,
      icon: TrendingUp,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
      link: "/price-history",
      subtitle: "últimos 7 días"
    }
  ];

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Panel de Control
        </h1>
        <p className="text-slate-500">
          Resumen de tu actividad y alertas importantes
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Link
              key={index}
              to={stat.link}
              className="stat-card group"
              data-testid={`stat-${stat.title.toLowerCase().replace(/ /g, '-')}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-sm ${stat.bgColor}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} strokeWidth={1.5} />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-400 transition-colors" />
              </div>
              <p className="numeric-value font-mono">{stat.value.toLocaleString()}</p>
              <p className="text-sm text-slate-500 mt-1">{stat.title}</p>
              {stat.subtitle && (
                <p className="text-xs text-slate-400 mt-0.5">{stat.subtitle}</p>
              )}
            </Link>
          );
        })}
      </div>

      {/* Alerts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Alert */}
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <AlertTriangle className="w-5 h-5 text-amber-500" strokeWidth={1.5} />
                Stock Bajo
              </CardTitle>
              <Badge variant="secondary" className="badge-warning">
                {stockAlerts.low_stock.length} productos
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {stockAlerts.low_stock.length === 0 ? (
              <p className="text-slate-500 text-sm py-4 text-center">
                No hay productos con stock bajo
              </p>
            ) : (
              <div className="space-y-3">
                {stockAlerts.low_stock.slice(0, 5).map((product) => (
                  <div
                    key={product.id}
                    className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">
                        {product.name}
                      </p>
                      <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
                    </div>
                    <div className="text-right">
                      <span className="badge-warning font-mono text-xs">
                        {product.stock} uds
                      </span>
                    </div>
                  </div>
                ))}
                {stockAlerts.low_stock.length > 5 && (
                  <Link
                    to="/products?stock=low"
                    className="block text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium py-2"
                  >
                    Ver todos ({stockAlerts.low_stock.length})
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Out of Stock Alert */}
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <PackageX className="w-5 h-5 text-rose-500" strokeWidth={1.5} />
                Sin Stock
              </CardTitle>
              <Badge variant="secondary" className="badge-error">
                {stockAlerts.out_of_stock.length} productos
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {stockAlerts.out_of_stock.length === 0 ? (
              <p className="text-slate-500 text-sm py-4 text-center">
                Todos los productos tienen stock disponible
              </p>
            ) : (
              <div className="space-y-3">
                {stockAlerts.out_of_stock.slice(0, 5).map((product) => (
                  <div
                    key={product.id}
                    className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">
                        {product.name}
                      </p>
                      <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
                    </div>
                    <div className="text-right">
                      <span className="badge-error font-mono text-xs">
                        Sin stock
                      </span>
                    </div>
                  </div>
                ))}
                {stockAlerts.out_of_stock.length > 5 && (
                  <Link
                    to="/products?stock=out"
                    className="block text-center text-sm text-indigo-600 hover:text-indigo-700 font-medium py-2"
                  >
                    Ver todos ({stockAlerts.out_of_stock.length})
                  </Link>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-6 border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Acciones Rápidas
          </CardTitle>
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
            <Link to="/export">
              <Button variant="outline" className="btn-secondary" data-testid="quick-export">
                <RefreshCw className="w-4 h-4 mr-2" strokeWidth={1.5} />
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
