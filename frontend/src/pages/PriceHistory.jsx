import { useState, useEffect, useCallback } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Search,
  Filter,
  Calendar
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const PriceHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState("30");
  const [search, setSearch] = useState("");

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/price-history", { params: { days: parseInt(days) } });
      setHistory(res.data);
    } catch (error) {
      toast.error("Error al cargar el historial de precios");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const filteredHistory = search
    ? history.filter(h => 
        h.product_name.toLowerCase().includes(search.toLowerCase())
      )
    : history;

  // Prepare chart data (last 7 unique dates)
  const chartData = history.reduce((acc, item) => {
    const date = new Date(item.created_at).toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
    const existing = acc.find(d => d.date === date);
    if (existing) {
      existing.changes += 1;
    } else {
      acc.push({ date, changes: 1 });
    }
    return acc;
  }, []).slice(-7);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
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
          <TrendingUp className="w-3 h-3" strokeWidth={1.5} />
          +{percentage.toFixed(1)}%
        </Badge>
      );
    }
    if (percentage < 0) {
      return (
        <Badge className="badge-success flex items-center gap-1">
          <TrendingDown className="w-3 h-3" strokeWidth={1.5} />
          {percentage.toFixed(1)}%
        </Badge>
      );
    }
    return <Badge className="bg-slate-100 text-slate-600">0%</Badge>;
  };

  if (loading && history.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Historial de Precios
        </h1>
        <p className="text-slate-500">
          Seguimiento de cambios de precios en tus productos
        </p>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <Card className="border-slate-200 mb-6">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Cambios de precio por día
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "4px",
                      fontFamily: "Inter, sans-serif"
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="changes"
                    stroke="#4f46e5"
                    strokeWidth={2}
                    dot={{ fill: "#4f46e5", strokeWidth: 2 }}
                    name="Cambios"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" strokeWidth={1.5} />
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
                <Calendar className="w-4 h-4 mr-2 text-slate-400" strokeWidth={1.5} />
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
          <div className="empty-state-icon">
            <TrendingUp className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay cambios de precios
          </h3>
          <p className="text-slate-500">
            {search ? "No se encontraron resultados para tu búsqueda" : `No se han detectado cambios de precios en los últimos ${days} días`}
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
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredHistory.map((item) => (
                  <TableRow key={item.id} className="table-row" data-testid={`history-row-${item.id}`}>
                    <TableCell>
                      <p className="font-medium text-slate-900">{item.product_name}</p>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-slate-500">
                        {item.old_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <ArrowRight className={`w-4 h-4 mx-auto ${getChangeColor(item.change_percentage)}`} strokeWidth={1.5} />
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={`font-mono font-semibold ${getChangeColor(item.change_percentage)}`}>
                        {item.new_price.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      {getChangeBadge(item.change_percentage)}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-slate-500">{formatDate(item.created_at)}</span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PriceHistory;
