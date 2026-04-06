import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  TrendingUp, TrendingDown, ArrowRight, Search, Calendar, Package, Eye, X
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from "recharts";
import { api } from "../App";
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

const PriceHistory = () => {
  const [history, setHistory] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState("30");
  const [search, setSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productTimeline, setProductTimeline] = useState(null);
  const [showProductChart, setShowProductChart] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [historyRes, topRes] = await Promise.all([
        api.get("/price-history", { params: { days: parseInt(days), limit: 200 } }),
        api.get("/price-history/top-products", { params: { days: parseInt(days) } })
      ]);
      setHistory(historyRes.data);
      setTopProducts(topRes.data);
    } catch (error) {
      toast.error("Error al cargar el historial de precios");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const viewProductChart = async (productName) => {
    setSelectedProduct(productName);
    setShowProductChart(true);
    try {
      const res = await api.get(`/price-history/product/${encodeURIComponent(productName)}`, {
        params: { days: 90 }
      });
      setProductTimeline(res.data);
    } catch (error) {
      toast.error("Error al cargar historial del producto");
    }
  };

  const filteredHistory = search
    ? history.filter(h => h.product_name.toLowerCase().includes(search.toLowerCase()))
    : history;

  const chartData = history.reduce((acc, item) => {
    const date = new Date(item.created_at).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
    const existing = acc.find(d => d.date === date);
    if (existing) {
      existing.changes += 1;
      existing.increases += item.change_percentage > 0 ? 1 : 0;
      existing.decreases += item.change_percentage < 0 ? 1 : 0;
    } else {
      acc.push({
        date,
        changes: 1,
        increases: item.change_percentage > 0 ? 1 : 0,
        decreases: item.change_percentage < 0 ? 1 : 0
      });
    }
    return acc;
  }, []).slice(-14);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  };

  const getChangeColor = (percentage) => {
    if (percentage > 0) return "text-rose-600";
    if (percentage < 0) return "text-emerald-600";
    return "text-slate-600";
  };

  const getChangeBadge = (percentage) => {
    if (percentage > 0) {
      return (
        <Badge className="badge-error flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />+{percentage.toFixed(1)}%
        </Badge>
      );
    }
    if (percentage < 0) {
      return (
        <Badge className="badge-success flex items-center gap-1">
          <TrendingDown className="w-3 h-3" />{percentage.toFixed(1)}%
        </Badge>
      );
    }
    return <Badge className="bg-slate-100 text-slate-600">0%</Badge>;
  };

  if (loading && history.length === 0) {
    return <div className="min-h-screen flex items-center justify-center"><div className="spinner"></div></div>;
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="price-history-title">
          Historial de Precios
        </h1>
        <p className="text-slate-500">Seguimiento de cambios de precios en tus productos</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Main Chart */}
        <Card className="border-slate-200 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Cambios de precio (últimos 14 días)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <div className="h-[220px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorIncreases" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorDecreases" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "6px" }} />
                    <Area type="monotone" dataKey="increases" stroke="#ef4444" fillOpacity={1} fill="url(#colorIncreases)" name="Subidas" />
                    <Area type="monotone" dataKey="decreases" stroke="#10b981" fillOpacity={1} fill="url(#colorDecreases)" name="Bajadas" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[220px] flex items-center justify-center text-slate-400">
                No hay datos para mostrar
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Productos más activos
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {topProducts.length === 0 ? (
              <div className="p-6 text-center text-slate-400">
                <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Sin datos</p>
              </div>
            ) : (
              <div className="divide-y">
                {topProducts.slice(0, 6).map((product, idx) => (
                  <div
                    key={idx}
                    className="px-4 py-3 hover:bg-slate-50 cursor-pointer flex items-center justify-between"
                    onClick={() => viewProductChart(product.product_name)}
                    data-testid={`top-product-${idx}`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{product.product_name}</p>
                      <p className="text-xs text-slate-500">{product.changes} cambios</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getChangeBadge(product.avg_change_percent)}
                      <Eye className="w-4 h-4 text-slate-300" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar por nombre de producto..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 input-base"
                data-testid="search-price-history"
              />
            </div>
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-full sm:w-[180px] input-base" data-testid="filter-days">
                <Calendar className="w-4 h-4 mr-2 text-slate-400" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Últimos 7 días</SelectItem>
                <SelectItem value="30">Últimos 30 días</SelectItem>
                <SelectItem value="90">Últimos 90 días</SelectItem>
                <SelectItem value="365">Último año</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* History Table */}
      {filteredHistory.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><TrendingUp className="w-10 h-10" /></div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay cambios de precios
          </h3>
          <p className="text-slate-500">
            {search ? "No se encontraron resultados" : `No se han detectado cambios en los últimos ${days} días`}
          </p>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Producto</TableHead>
                  <TableHead className="text-right">Precio Anterior</TableHead>
                  <TableHead className="text-center"></TableHead>
                  <TableHead className="text-right">Precio Nuevo</TableHead>
                  <TableHead className="text-center">Variación</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredHistory.map((item) => (
                  <TableRow key={item.id} className="table-row" data-testid={`history-row-${item.id}`}>
                    <TableCell>
                      <p className="font-medium text-slate-900 truncate max-w-[200px]">{item.product_name}</p>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-slate-500">
                        {item.old_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <ArrowRight className={`w-4 h-4 mx-auto ${getChangeColor(item.change_percentage)}`} />
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={`font-mono font-semibold ${getChangeColor(item.change_percentage)}`}>
                        {item.new_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">{getChangeBadge(item.change_percentage)}</TableCell>
                    <TableCell><span className="text-sm text-slate-500">{formatDate(item.created_at)}</span></TableCell>
                    <TableCell>
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => viewProductChart(item.product_name)}
                        className="h-8 w-8 p-0"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Product Chart Dialog */}
      <Dialog open={showProductChart} onOpenChange={setShowProductChart}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <span>Evolución de precio</span>
            </DialogTitle>
            <DialogDescription className="truncate">{selectedProduct}</DialogDescription>
          </DialogHeader>
          
          {productTimeline ? (
            <div className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Precio actual</p>
                  <p className="text-lg font-bold text-slate-900">
                    {productTimeline.current_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" }) || "-"}
                  </p>
                </div>
                <div className="bg-emerald-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Precio mínimo</p>
                  <p className="text-lg font-bold text-emerald-600">
                    {productTimeline.min_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" }) || "-"}
                  </p>
                </div>
                <div className="bg-rose-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Precio máximo</p>
                  <p className="text-lg font-bold text-rose-600">
                    {productTimeline.max_price?.toLocaleString("es-ES", { style: "currency", currency: "EUR" }) || "-"}
                  </p>
                </div>
              </div>

              {/* Chart */}
              {productTimeline.timeline && productTimeline.timeline.length > 0 ? (
                <div className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={productTimeline.timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "6px" }}
                        formatter={(value) => [value.toLocaleString("es-ES", { style: "currency", currency: "EUR" }), "Precio"]}
                      />
                      <Line type="stepAfter" dataKey="price" stroke="#4f46e5" strokeWidth={2} dot={{ fill: "#4f46e5" }} name="Precio" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-400">
                  <div className="text-center">
                    <TrendingUp className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No hay suficientes datos para la gráfica</p>
                  </div>
                </div>
              )}

              <p className="text-sm text-slate-500 text-center">
                {productTimeline.total_changes} cambios de precio en los últimos 90 días
              </p>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <div className="spinner"></div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PriceHistory;
