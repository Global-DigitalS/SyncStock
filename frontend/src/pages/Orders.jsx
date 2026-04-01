import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from "../components/ui/dialog";
import {
  ShoppingCart, Search, Filter, Eye, RotateCw, AlertCircle, CheckCircle, Clock, Package, Loader2
} from "lucide-react";
import { EmptyState } from "../components/shared/index";

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [pagination, setPagination] = useState({ skip: 0, limit: 20, total: 0 });

  // Fetch órdenes
  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        skip: pagination.skip,
        limit: pagination.limit
      };
      if (statusFilter !== "all") params.status = statusFilter;
      if (sourceFilter !== "all") params.source = sourceFilter;
      if (search) params.search = search;

      const res = await api.get("/orders", { params });
      setOrders(res.data.orders || []);
      setPagination(prev => ({ ...prev, total: res.data.total || 0 }));
    } catch (error) {
      toast.error("Error al cargar pedidos");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [pagination.skip, pagination.limit, statusFilter, sourceFilter, search]);

  // Fetch estadísticas
  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get("/orders/stats/summary");
      setStats(res.data);
    } catch (error) {
      console.error("Error al cargar estadísticas:", error);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [fetchOrders, fetchStats]);

  // Reintento de orden fallida
  const retryOrder = async (orderId) => {
    setRetrying(true);
    try {
      const res = await api.post(`/orders/${orderId}/retry`);
      toast.success("Pedido reenviado al CRM");
      await fetchOrders();
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(res.data);
      }
    } catch (error) {
      toast.error("Error al reintentar pedido");
      console.error(error);
    } finally {
      setRetrying(false);
    }
  };

  // Ver detalle
  const viewOrderDetail = async (order) => {
    try {
      const res = await api.get(`/orders/${order.id}`);
      setSelectedOrder(res.data);
      setShowDetail(true);
    } catch (error) {
      toast.error("Error al cargar detalle del pedido");
    }
  };

  // Mapeos para localización
  const statusMap = {
    pending: { label: "Pendiente", color: "bg-yellow-100 text-yellow-800" },
    processing: { label: "Procesando", color: "bg-blue-100 text-blue-800" },
    completed: { label: "Completado", color: "bg-green-100 text-green-800" },
    backorder: { label: "Sin stock", color: "bg-orange-100 text-orange-800" },
    error: { label: "Error", color: "bg-red-100 text-red-800" },
    duplicate: { label: "Duplicado", color: "bg-gray-100 text-gray-800" }
  };

  const sourceMap = {
    woocommerce: "WooCommerce",
    shopify: "Shopify",
    prestashop: "PrestaShop"
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4" />;
      case "error":
        return <AlertCircle className="w-4 h-4" />;
      case "processing":
        return <Loader2 className="w-4 h-4 animate-spin" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR"
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <ShoppingCart className="w-8 h-8" />
          Gestión de Pedidos
        </h1>
        <p className="text-slate-600 mt-1">
          Sincronización de pedidos de tiendas online a CRM
        </p>
      </div>

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.total || 0}</div>
                <div className="text-sm text-slate-600">Total de pedidos</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.completed || 0}</div>
                <div className="text-sm text-slate-600">Completados</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.failed || 0}</div>
                <div className="text-sm text-slate-600">Con error</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{stats.pending || 0}</div>
                <div className="text-sm text-slate-600">Pendientes</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar por cliente, ID de pedido..."
                className="pl-10"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPagination(prev => ({ ...prev, skip: 0 }));
                }}
              />
            </div>
            <Select value={statusFilter} onValueChange={(val) => {
              setStatusFilter(val);
              setPagination(prev => ({ ...prev, skip: 0 }));
            }}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                <SelectItem value="completed">Completado</SelectItem>
                <SelectItem value="processing">Procesando</SelectItem>
                <SelectItem value="pending">Pendiente</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="backorder">Sin stock</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sourceFilter} onValueChange={(val) => {
              setSourceFilter(val);
              setPagination(prev => ({ ...prev, skip: 0 }));
            }}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Plataforma" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas las plataformas</SelectItem>
                <SelectItem value="woocommerce">WooCommerce</SelectItem>
                <SelectItem value="shopify">Shopify</SelectItem>
                <SelectItem value="prestashop">PrestaShop</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de pedidos */}
      <Card>
        <CardHeader>
          <CardTitle>Pedidos Recientes</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
            </div>
          ) : orders.length === 0 ? (
            <EmptyState
              icon={ShoppingCart}
              title="No hay pedidos"
              description="Los pedidos sincronizados aparecerán aquí"
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID Externo</TableHead>
                    <TableHead>Plataforma</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Monto</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>CRM</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-mono text-sm">{order.sourceOrderId}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{sourceMap[order.source] || order.source}</Badge>
                      </TableCell>
                      <TableCell>{order.customer?.name || "N/A"}</TableCell>
                      <TableCell>{formatCurrency(order.totalAmount)}</TableCell>
                      <TableCell>
                        <Badge className={statusMap[order.status]?.color || ""}>
                          <span className="flex items-center gap-1">
                            {getStatusIcon(order.status)}
                            {statusMap[order.status]?.label || order.status}
                          </span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {order.crmData?.crm ? (
                          <Badge variant="secondary" className="bg-blue-50">
                            {order.crmData.crm.toUpperCase()}
                          </Badge>
                        ) : (
                          <span className="text-xs text-slate-500">Sin CRM</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-slate-600">
                        {formatDate(order.createdAt)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => viewOrderDetail(order)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {order.status === "error" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => retryOrder(order.id)}
                            disabled={retrying}
                            className="ml-1"
                          >
                            <RotateCw className="w-4 h-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Paginación */}
          {orders.length > 0 && (
            <div className="flex items-center justify-between mt-6 pt-6 border-t">
              <div className="text-sm text-slate-600">
                Mostrando {pagination.skip + 1}-{Math.min(pagination.skip + pagination.limit, pagination.total)} de {pagination.total} pedidos
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.skip === 0}
                  onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.skip + pagination.limit >= pagination.total}
                  onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de detalle */}
      {selectedOrder && (
        <OrderDetailDialog
          order={selectedOrder}
          open={showDetail}
          onOpenChange={setShowDetail}
          onRetry={() => retryOrder(selectedOrder.id)}
          retrying={retrying}
        />
      )}
    </div>
  );
};

// Componente de diálogo de detalle
const OrderDetailDialog = ({ order, open, onOpenChange, onRetry, retrying }) => {
  const statusMap = {
    pending: { label: "Pendiente", color: "bg-yellow-100 text-yellow-800" },
    processing: { label: "Procesando", color: "bg-blue-100 text-blue-800" },
    completed: { label: "Completado", color: "bg-green-100 text-green-800" },
    backorder: { label: "Sin stock", color: "bg-orange-100 text-orange-800" },
    error: { label: "Error", color: "bg-red-100 text-red-800" }
  };

  const sourceMap = {
    woocommerce: "WooCommerce",
    shopify: "Shopify",
    prestashop: "PrestaShop"
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR"
    }).format(value);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Detalle del Pedido</DialogTitle>
          <DialogDescription>
            ID: {order.sourceOrderId}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Cliente */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-sm mb-3">Cliente</h3>
              <div className="space-y-2 text-sm">
                <div><span className="text-slate-600">Nombre:</span> {order.customer?.name}</div>
                <div><span className="text-slate-600">Email:</span> {order.customer?.email}</div>
                <div><span className="text-slate-600">Teléfono:</span> {order.customer?.phone || "N/A"}</div>
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-sm mb-3">Información del Pedido</h3>
              <div className="space-y-2 text-sm">
                <div><span className="text-slate-600">Plataforma:</span> {sourceMap[order.source]}</div>
                <div><span className="text-slate-600">Estado:</span> <Badge className={statusMap[order.status]?.color}>{statusMap[order.status]?.label}</Badge></div>
                <div><span className="text-slate-600">Fecha:</span> {formatDate(order.createdAt)}</div>
              </div>
            </div>
          </div>

          {/* Dirección de envío */}
          <div>
            <h3 className="font-semibold text-sm mb-3">Dirección de Envío</h3>
            <div className="text-sm space-y-1 bg-slate-50 p-3 rounded">
              <div>{order.addresses?.shipping?.street}</div>
              <div>{order.addresses?.shipping?.zipCode} {order.addresses?.shipping?.city}</div>
              <div>{order.addresses?.shipping?.country}</div>
            </div>
          </div>

          {/* Ítems */}
          <div>
            <h3 className="font-semibold text-sm mb-3">Ítems del Pedido</h3>
            <div className="space-y-2">
              {order.items?.map((item, idx) => (
                <div key={idx} className="flex justify-between items-start p-3 bg-slate-50 rounded">
                  <div>
                    <div className="font-medium text-sm">{item.name}</div>
                    <div className="text-xs text-slate-600">SKU: {item.sku}</div>
                    <Badge variant="outline" className="mt-1 text-xs">
                      {item.status === "available" ? "Disponible" :
                       item.status === "backorder" ? "Sin stock" :
                       item.status === "not_found" ? "No encontrado" : item.status}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{item.quantity}x</div>
                    <div className="text-sm">{formatCurrency(item.price)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resumen */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-slate-600">Subtotal:</span>
              <span className="font-medium">{formatCurrency(order.totalAmount)}</span>
            </div>
            <div className="flex justify-between items-center font-semibold text-lg">
              <span>Total:</span>
              <span>{formatCurrency(order.totalAmount)}</span>
            </div>
          </div>

          {/* CRM Data */}
          {order.crmData && (
            <div>
              <h3 className="font-semibold text-sm mb-3">Información del CRM</h3>
              <div className="text-sm bg-blue-50 p-3 rounded space-y-1">
                <div><span className="text-slate-600">CRM:</span> {order.crmData.crm?.toUpperCase()}</div>
                {order.crmData.dolibarr_order_id && (
                  <div><span className="text-slate-600">ID Dolibarr:</span> {order.crmData.dolibarr_order_id}</div>
                )}
                {order.crmData.odoo_order_id && (
                  <div><span className="text-slate-600">ID Odoo:</span> {order.crmData.odoo_order_id}</div>
                )}
              </div>
            </div>
          )}

          {/* Error */}
          {order.error && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <div className="font-semibold text-sm text-red-800 mb-1">Error</div>
              <div className="text-sm text-red-700">{order.error.message}</div>
            </div>
          )}

          {/* Botones de acción */}
          <div className="flex gap-2 pt-4 border-t">
            {order.status === "error" && (
              <Button onClick={onRetry} disabled={retrying}>
                <RotateCw className="w-4 h-4 mr-2" />
                {retrying ? "Reenviando..." : "Reintentar"}
              </Button>
            )}
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cerrar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default Orders;
