import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  RefreshCw, CheckCircle, XCircle, AlertTriangle, Clock, Calendar,
  TrendingUp, Package, Truck, Timer
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { api } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "../components/ui/table";

const SyncHistory = () => {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    supplier_id: "",
    status: "",
    days: "30"
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { days: parseInt(filters.days) };
      if (filters.supplier_id) params.supplier_id = filters.supplier_id;
      if (filters.status) params.status = filters.status;
      
      const [historyRes, statsRes, suppliersRes] = await Promise.all([
        api.get("/sync-history", { params }),
        api.get("/sync-history/stats", { params: { days: parseInt(filters.days) } }),
        api.get("/suppliers")
      ]);
      
      setHistory(historyRes.data);
      setStats(statsRes.data);
      setSuppliers(suppliersRes.data);
    } catch (error) {
      toast.error("Error al cargar el historial de sincronizaciones");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "success":
        return <Badge className="bg-emerald-100 text-emerald-700 border-0"><CheckCircle className="w-3 h-3 mr-1" />Exitoso</Badge>;
      case "error":
        return <Badge className="bg-rose-100 text-rose-700 border-0"><XCircle className="w-3 h-3 mr-1" />Error</Badge>;
      case "partial":
        return <Badge className="bg-amber-100 text-amber-700 border-0"><AlertTriangle className="w-3 h-3 mr-1" />Parcial</Badge>;
      default:
        return <Badge className="bg-slate-100 text-slate-700 border-0">{status}</Badge>;
    }
  };

  const getSyncTypeBadge = (type) => {
    if (type === "scheduled") {
      return <Badge className="bg-blue-100 text-blue-700 border-0"><Clock className="w-3 h-3 mr-1" />Programado</Badge>;
    }
    return <Badge className="bg-slate-100 text-slate-700 border-0"><RefreshCw className="w-3 h-3 mr-1" />Manual</Badge>;
  };

  // Prepare chart data
  const chartData = stats?.daily_stats?.map(d => ({
    date: new Date(d.date).toLocaleDateString("es-ES", { day: "2-digit", month: "short" }),
    exitosas: d.success,
    errores: d.errors,
    total: d.count
  })) || [];

  if (loading && history.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }} data-testid="sync-history-title">
          Historial de Sincronizaciones
        </h1>
        <p className="text-slate-500">
          Registro detallado de todas las sincronizaciones de proveedores
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-indigo-500" />
                <div>
                  <p className="text-xs text-slate-500">Total</p>
                  <p className="text-xl font-bold text-slate-900">{stats.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <div>
                  <p className="text-xs text-slate-500">Exitosas</p>
                  <p className="text-xl font-bold text-emerald-600">{stats.success}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-rose-500" />
                <div>
                  <p className="text-xs text-slate-500">Errores</p>
                  <p className="text-xl font-bold text-rose-600">{stats.errors}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <div>
                  <p className="text-xs text-slate-500">Parciales</p>
                  <p className="text-xl font-bold text-amber-600">{stats.partial}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-xs text-slate-500">Importados</p>
                  <p className="text-xl font-bold text-blue-600">{stats.total_imported.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-purple-500" />
                <div>
                  <p className="text-xs text-slate-500">Actualizados</p>
                  <p className="text-xl font-bold text-purple-600">{stats.total_updated.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-slate-500" />
                <div>
                  <p className="text-xs text-slate-500">Errores prod.</p>
                  <p className="text-xl font-bold text-slate-600">{stats.total_errors.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Timer className="w-5 h-5 text-indigo-500" />
                <div>
                  <p className="text-xs text-slate-500">Tiempo med.</p>
                  <p className="text-xl font-bold text-indigo-600">{formatDuration(stats.avg_duration)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart */}
      {chartData.length > 0 && (
        <Card className="border-slate-200 mb-6">
          <CardHeader>
            <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Sincronizaciones por día
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "4px"
                    }}
                  />
                  <Legend />
                  <Bar dataKey="exitosas" fill="#10b981" name="Exitosas" />
                  <Bar dataKey="errores" fill="#ef4444" name="Errores" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="border-slate-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select
              value={filters.supplier_id || "all"}
              onValueChange={(value) => setFilters({ ...filters, supplier_id: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full sm:w-[200px] input-base" data-testid="filter-supplier">
                <Truck className="w-4 h-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Todos los proveedores" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los proveedores</SelectItem>
                {suppliers.map((s) => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.status || "all"}
              onValueChange={(value) => setFilters({ ...filters, status: value === "all" ? "" : value })}
            >
              <SelectTrigger className="w-full sm:w-[150px] input-base" data-testid="filter-status">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                <SelectItem value="success">Exitoso</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="partial">Parcial</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.days}
              onValueChange={(value) => setFilters({ ...filters, days: value })}
            >
              <SelectTrigger className="w-full sm:w-[150px] input-base" data-testid="filter-days">
                <Calendar className="w-4 h-4 mr-2 text-slate-400" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Últimos 7 días</SelectItem>
                <SelectItem value="30">Últimos 30 días</SelectItem>
                <SelectItem value="90">Últimos 90 días</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={fetchData} variant="outline" className="btn-secondary">
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* History Table */}
      {history.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <RefreshCw className="w-10 h-10" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            No hay sincronizaciones
          </h3>
          <p className="text-slate-500">
            El historial de sincronizaciones aparecerá aquí cuando sincronices proveedores
          </p>
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead>Proveedor</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Importados</TableHead>
                  <TableHead className="text-right">Actualizados</TableHead>
                  <TableHead className="text-right">Errores</TableHead>
                  <TableHead className="text-right">Duración</TableHead>
                  <TableHead>Fecha</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.id} className="table-row" data-testid={`sync-row-${item.id}`}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Truck className="w-4 h-4 text-slate-400" />
                        <span className="font-medium text-slate-900">{item.supplier_name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{getSyncTypeBadge(item.sync_type)}</TableCell>
                    <TableCell>{getStatusBadge(item.status)}</TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-emerald-600">{item.imported}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-blue-600">{item.updated}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={`font-mono ${item.errors > 0 ? "text-rose-600" : "text-slate-400"}`}>{item.errors}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-mono text-slate-600">{formatDuration(item.duration_seconds)}</span>
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

export default SyncHistory;
