import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Plus,
  MoreHorizontal,
  Pencil,
  Trash2,
  Play,
  Eye,
  RefreshCw,
  Search,
  TrendingDown,
  TrendingUp,
  Minus,
  Bell,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Globe,
  ShieldCheck,
  Loader2,
  Download,
  BarChart3,
  Zap,
  ArrowDown,
  ArrowUp,
  Equal,
  Settings2,
  FlaskConical,
  Rocket,
} from "lucide-react";

// Canales válidos
const CHANNELS = [
  { value: "amazon_es", label: "Amazon España" },
  { value: "pccomponentes", label: "PCComponentes" },
  { value: "mediamarkt", label: "MediaMarkt" },
  { value: "fnac", label: "Fnac" },
  { value: "el_corte_ingles", label: "El Corte Inglés" },
  { value: "worten", label: "Worten" },
  { value: "coolmod", label: "Coolmod" },
  { value: "ldlc", label: "LDLC" },
  { value: "alternate", label: "Alternate" },
  { value: "web_directa", label: "Web Directa" },
  { value: "otro", label: "Otro" },
];

const ALERT_TYPES = [
  { value: "price_drop", label: "Bajada de precio (%)" },
  { value: "price_below", label: "Precio por debajo de..." },
  { value: "competitor_cheaper", label: "Competidor más barato" },
  { value: "any_change", label: "Cualquier cambio" },
];

const ALERT_CHANNELS = [
  { value: "app", label: "Notificación en la app" },
  { value: "email", label: "Email" },
  { value: "webhook", label: "Webhook" },
];

const getChannelLabel = (value) => {
  const ch = CHANNELS.find((c) => c.value === value);
  return ch ? ch.label : value;
};

const defaultCompetitorForm = {
  name: "",
  base_url: "",
  channel: "web_directa",
  country: "ES",
  active: true,
};

const defaultAlertForm = {
  sku: "",
  ean: "",
  alert_type: "competitor_cheaper",
  threshold: "",
  channel: "app",
  webhook_url: "",
  active: true,
};

const AUTOMATION_STRATEGIES = [
  { value: "match_cheapest", label: "Igualar al más barato" },
  { value: "undercut_by_amount", label: "Rebajar importe fijo" },
  { value: "undercut_by_percent", label: "Rebajar porcentaje" },
  { value: "margin_above_cost", label: "Margen sobre coste" },
  { value: "price_cap", label: "Techo de precio" },
];

const APPLY_TO_OPTIONS = [
  { value: "all", label: "Todos los productos" },
  { value: "category", label: "Categoría" },
  { value: "supplier", label: "Proveedor" },
  { value: "product", label: "Producto específico" },
];

const defaultRuleForm = {
  name: "",
  strategy: "match_cheapest",
  value: "",
  apply_to: "all",
  apply_to_value: "",
  min_price: "",
  max_price: "",
  catalog_id: "",
  priority: "0",
  active: true,
};

const Competitors = () => {
  // Competitors state
  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCompetitorDialog, setShowCompetitorDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);
  const [competitorForm, setCompetitorForm] = useState(defaultCompetitorForm);
  const [saving, setSaving] = useState(false);

  // Alerts state
  const [alerts, setAlerts] = useState([]);
  const [showAlertDialog, setShowAlertDialog] = useState(false);
  const [showDeleteAlertDialog, setShowDeleteAlertDialog] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alertForm, setAlertForm] = useState(defaultAlertForm);

  // Crawl state
  const [crawlStatus, setCrawlStatus] = useState(null);
  const [crawlRunning, setCrawlRunning] = useState(false);

  // Pending matches state
  const [pendingMatches, setPendingMatches] = useState([]);
  const [pendingTotal, setPendingTotal] = useState(0);

  // Report state
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportCategory, setReportCategory] = useState("");
  const [reportSupplier, setReportSupplier] = useState("");

  // Automation state
  const [automationRules, setAutomationRules] = useState([]);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [showDeleteRuleDialog, setShowDeleteRuleDialog] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);
  const [ruleForm, setRuleForm] = useState(defaultRuleForm);
  const [simulation, setSimulation] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [applying, setApplying] = useState(false);

  // Dashboard state
  const [dashboardOverview, setDashboardOverview] = useState(null);
  const [dashboardTable, setDashboardTable] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardSearch, setDashboardSearch] = useState("");
  const [dashboardPage, setDashboardPage] = useState(1);
  const [dashboardTotal, setDashboardTotal] = useState(0);
  const [enrichedAlerts, setEnrichedAlerts] = useState([]);

  // Active tab
  const [activeTab, setActiveTab] = useState("competitors");

  // ==================== DATA FETCHING ====================

  const fetchCompetitors = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/competitors");
      setCompetitors(res.data);
    } catch (error) {
      toast.error("Error al cargar competidores");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await api.get("/competitors/alerts");
      setAlerts(res.data);
    } catch (error) {
      toast.error("Error al cargar alertas");
    }
  }, []);

  const fetchCrawlStatus = useCallback(async () => {
    try {
      const res = await api.get("/competitors/crawl/status");
      setCrawlStatus(res.data.competitors);
      setCrawlRunning(res.data.crawl_running);
    } catch (error) {
      // silent
    }
  }, []);

  const fetchPendingMatches = useCallback(async () => {
    try {
      const res = await api.get("/competitors/matches/pending?limit=20");
      setPendingMatches(res.data.matches);
      setPendingTotal(res.data.total);
    } catch (error) {
      // silent
    }
  }, []);

  const fetchReport = useCallback(async () => {
    try {
      setReportLoading(true);
      const params = new URLSearchParams();
      if (reportCategory) params.set("category", reportCategory);
      if (reportSupplier) params.set("supplier_id", reportSupplier);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await api.get(`/competitors/report/positioning${qs}`);
      setReport(res.data);
    } catch (error) {
      toast.error("Error al cargar informe de posicionamiento");
    } finally {
      setReportLoading(false);
    }
  }, [reportCategory, reportSupplier]);

  const fetchAutomationRules = useCallback(async () => {
    try {
      setAutomationLoading(true);
      const res = await api.get("/competitors/automation/rules");
      setAutomationRules(res.data.rules || []);
    } catch (error) {
      toast.error("Error al cargar reglas de automatización");
    } finally {
      setAutomationLoading(false);
    }
  }, []);

  const fetchDashboardOverview = useCallback(async () => {
    try {
      const res = await api.get("/competitors/dashboard/overview");
      setDashboardOverview(res.data);
    } catch (error) {
      console.error("Error al cargar overview del dashboard:", error);
    }
  }, []);

  const fetchDashboardTable = useCallback(async (page = 1, search = "") => {
    try {
      setDashboardLoading(true);
      const params = new URLSearchParams();
      params.set("page", page);
      params.set("page_size", 20);
      if (search) params.set("search", search);
      const res = await api.get(`/competitors/dashboard/table?${params.toString()}`);
      setDashboardTable(res.data.items || []);
      setDashboardTotal(res.data.total || 0);
    } catch (error) {
      toast.error("Error al cargar tabla del dashboard");
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  const fetchEnrichedAlerts = useCallback(async () => {
    try {
      const res = await api.get("/competitors/dashboard/alerts/enriched");
      setEnrichedAlerts(res.data.alerts || []);
    } catch (error) {
      console.error("Error al cargar alertas enriquecidas:", error);
    }
  }, []);

  useEffect(() => {
    fetchCompetitors();
    fetchAlerts();
    fetchCrawlStatus();
    fetchPendingMatches();
  }, [fetchCompetitors, fetchAlerts, fetchCrawlStatus, fetchPendingMatches]);

  // Load dashboard data when tab is active
  const searchTimerRef = useRef(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce de búsqueda: esperar 400ms tras última pulsación
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setDebouncedSearch(dashboardSearch);
    }, 400);
    return () => clearTimeout(searchTimerRef.current);
  }, [dashboardSearch]);

  useEffect(() => {
    if (activeTab === "dashboard") {
      fetchDashboardOverview();
      fetchDashboardTable(dashboardPage, debouncedSearch);
      fetchEnrichedAlerts();
    }
  }, [activeTab, dashboardPage, debouncedSearch, fetchDashboardOverview, fetchDashboardTable, fetchEnrichedAlerts]);

  // ==================== COMPETITOR CRUD ====================

  const openCreateCompetitor = () => {
    setSelectedCompetitor(null);
    setCompetitorForm(defaultCompetitorForm);
    setShowCompetitorDialog(true);
  };

  const openEditCompetitor = (competitor) => {
    setSelectedCompetitor(competitor);
    setCompetitorForm({
      name: competitor.name,
      base_url: competitor.base_url,
      channel: competitor.channel,
      country: competitor.country,
      active: competitor.active,
    });
    setShowCompetitorDialog(true);
  };

  const saveCompetitor = async () => {
    if (!competitorForm.name.trim() || !competitorForm.base_url.trim()) {
      toast.error("Nombre y URL son obligatorios");
      return;
    }
    try {
      setSaving(true);
      if (selectedCompetitor) {
        await api.put(`/competitors/${selectedCompetitor.id}`, competitorForm);
        toast.success("Competidor actualizado");
      } else {
        await api.post("/competitors", competitorForm);
        toast.success("Competidor creado");
      }
      setShowCompetitorDialog(false);
      fetchCompetitors();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar competidor");
    } finally {
      setSaving(false);
    }
  };

  const deleteCompetitor = async () => {
    if (!selectedCompetitor) return;
    try {
      await api.delete(`/competitors/${selectedCompetitor.id}`);
      toast.success("Competidor eliminado");
      setShowDeleteDialog(false);
      setSelectedCompetitor(null);
      fetchCompetitors();
    } catch (error) {
      toast.error("Error al eliminar competidor");
    }
  };

  // ==================== CRAWL ====================

  const triggerCrawl = async (competitorId = null) => {
    try {
      setCrawlRunning(true);
      const params = competitorId ? `?competitor_id=${competitorId}` : "";
      await api.post(`/competitors/crawl${params}`);
      toast.success("Crawl iniciado en background");
      // Poll status after a few seconds
      setTimeout(fetchCrawlStatus, 5000);
      setTimeout(fetchCrawlStatus, 15000);
      setTimeout(() => {
        fetchCrawlStatus();
        fetchPendingMatches();
      }, 30000);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al iniciar el crawl");
      setCrawlRunning(false);
    }
  };

  // ==================== ALERTS CRUD ====================

  const openCreateAlert = () => {
    setSelectedAlert(null);
    setAlertForm(defaultAlertForm);
    setShowAlertDialog(true);
  };

  const openEditAlert = (alert) => {
    setSelectedAlert(alert);
    setAlertForm({
      sku: alert.sku || "",
      ean: alert.ean || "",
      alert_type: alert.alert_type,
      threshold: alert.threshold?.toString() || "",
      channel: alert.channel,
      webhook_url: alert.webhook_url || "",
      active: alert.active,
    });
    setShowAlertDialog(true);
  };

  const saveAlert = async () => {
    if (!alertForm.sku && !alertForm.ean) {
      toast.error("Debes indicar un SKU o EAN");
      return;
    }
    try {
      setSaving(true);
      const data = {
        ...alertForm,
        threshold: alertForm.threshold ? parseFloat(alertForm.threshold) : null,
        sku: alertForm.sku || null,
        ean: alertForm.ean || null,
        webhook_url: alertForm.channel === "webhook" ? alertForm.webhook_url : null,
      };
      if (selectedAlert) {
        await api.put(`/competitors/alerts/${selectedAlert.id}`, data);
        toast.success("Alerta actualizada");
      } else {
        await api.post("/competitors/alerts", data);
        toast.success("Alerta creada");
      }
      setShowAlertDialog(false);
      fetchAlerts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar alerta");
    } finally {
      setSaving(false);
    }
  };

  const deleteAlert = async () => {
    if (!selectedAlert) return;
    try {
      await api.delete(`/competitors/alerts/${selectedAlert.id}`);
      toast.success("Alerta eliminada");
      setShowDeleteAlertDialog(false);
      setSelectedAlert(null);
      fetchAlerts();
    } catch (error) {
      toast.error("Error al eliminar alerta");
    }
  };

  // ==================== PENDING MATCHES ====================

  const reviewMatch = async (matchId, action) => {
    try {
      await api.put(`/competitors/matches/${matchId}?action=${action}`);
      toast.success(action === "confirm" ? "Match confirmado" : "Match rechazado");
      fetchPendingMatches();
    } catch (error) {
      toast.error("Error al revisar el match");
    }
  };

  // ==================== EXPORT ====================

  const exportPricesCSV = async () => {
    try {
      const res = await api.get("/competitors/export/prices?days=30", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `precios_competidores_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Exportación CSV descargada");
    } catch (error) {
      toast.error("Error al exportar precios");
    }
  };

  const exportPositioningCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (reportCategory) params.set("category", reportCategory);
      if (reportSupplier) params.set("supplier_id", reportSupplier);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await api.get(`/competitors/report/positioning/export${qs}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `informe_posicionamiento_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Informe CSV descargado");
    } catch (error) {
      toast.error("Error al exportar informe");
    }
  };

  // ==================== AUTOMATION CRUD ====================

  const openCreateRule = () => {
    setSelectedRule(null);
    setRuleForm(defaultRuleForm);
    setShowRuleDialog(true);
  };

  const openEditRule = (rule) => {
    setSelectedRule(rule);
    setRuleForm({
      name: rule.name,
      strategy: rule.strategy,
      value: rule.value?.toString() || "",
      apply_to: rule.apply_to || "all",
      apply_to_value: rule.apply_to_value || "",
      min_price: rule.min_price?.toString() || "",
      max_price: rule.max_price?.toString() || "",
      catalog_id: rule.catalog_id || "",
      priority: rule.priority?.toString() || "0",
      active: rule.active,
    });
    setShowRuleDialog(true);
  };

  const saveRule = async () => {
    if (!ruleForm.name.trim()) {
      toast.error("El nombre es obligatorio");
      return;
    }
    if (!ruleForm.value || parseFloat(ruleForm.value) < 0) {
      toast.error("El valor debe ser un número >= 0");
      return;
    }
    try {
      setSaving(true);
      const data = {
        name: ruleForm.name.trim(),
        strategy: ruleForm.strategy,
        value: parseFloat(ruleForm.value),
        apply_to: ruleForm.apply_to,
        apply_to_value: ruleForm.apply_to_value || null,
        min_price: ruleForm.min_price ? parseFloat(ruleForm.min_price) : 0,
        max_price: ruleForm.max_price ? parseFloat(ruleForm.max_price) : null,
        catalog_id: ruleForm.catalog_id || null,
        priority: parseInt(ruleForm.priority) || 0,
        active: ruleForm.active,
      };
      if (selectedRule) {
        await api.put(`/competitors/automation/rules/${selectedRule.id}`, data);
        toast.success("Regla actualizada");
      } else {
        await api.post("/competitors/automation/rules", data);
        toast.success("Regla creada");
      }
      setShowRuleDialog(false);
      fetchAutomationRules();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar regla");
    } finally {
      setSaving(false);
    }
  };

  const deleteRule = async () => {
    if (!selectedRule) return;
    try {
      await api.delete(`/competitors/automation/rules/${selectedRule.id}`);
      toast.success("Regla eliminada");
      setShowDeleteRuleDialog(false);
      setSelectedRule(null);
      fetchAutomationRules();
    } catch (error) {
      toast.error("Error al eliminar regla");
    }
  };

  const runSimulation = async (ruleId = null) => {
    try {
      setSimulating(true);
      const params = ruleId ? `?rule_id=${ruleId}&limit=100` : "?limit=100";
      const res = await api.post(`/competitors/automation/simulate${params}`);
      setSimulation(res.data);
    } catch (error) {
      toast.error("Error al simular automatización");
    } finally {
      setSimulating(false);
    }
  };

  const applyAutomation = async (ruleId = null) => {
    try {
      setApplying(true);
      const params = ruleId ? `?rule_id=${ruleId}` : "";
      const res = await api.post(`/competitors/automation/apply${params}`);
      toast.success(res.data.message || "Automatización aplicada");
      setSimulation(null);
      fetchAutomationRules();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al aplicar automatización");
    } finally {
      setApplying(false);
    }
  };

  // ==================== RENDER ====================

  const CrawlStatusBadge = ({ status }) => {
    if (!status) return <Badge variant="outline">Sin datos</Badge>;
    const map = {
      success: { label: "OK", variant: "default", icon: CheckCircle2 },
      partial: { label: "Parcial", variant: "secondary", icon: AlertTriangle },
      error: { label: "Error", variant: "destructive", icon: XCircle },
    };
    const info = map[status] || map.error;
    const Icon = info.icon;
    return (
      <Badge variant={info.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {info.label}
      </Badge>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Monitorización de Competidores</h1>
          <p className="text-sm text-muted-foreground">
            Compara precios con la competencia y configura alertas
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={exportPricesCSV}>
            <Download className="h-4 w-4 mr-2" />
            Exportar CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => triggerCrawl()}
            disabled={crawlRunning || competitors.length === 0}
          >
            {crawlRunning ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            {crawlRunning ? "Scraping..." : "Iniciar Scraping"}
          </Button>
          <Button onClick={openCreateCompetitor}>
            <Plus className="h-4 w-4 mr-2" />
            Añadir Competidor
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="competitors">
            <Globe className="h-4 w-4 mr-2" />
            Competidores ({competitors.length})
          </TabsTrigger>
          <TabsTrigger value="alerts">
            <Bell className="h-4 w-4 mr-2" />
            Alertas ({alerts.length})
          </TabsTrigger>
          <TabsTrigger value="matches">
            <ShieldCheck className="h-4 w-4 mr-2" />
            Revisión ({pendingTotal})
          </TabsTrigger>
          <TabsTrigger value="report" onClick={() => !report && fetchReport()}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Informes
          </TabsTrigger>
          <TabsTrigger value="automation" onClick={() => automationRules.length === 0 && fetchAutomationRules()}>
            <Zap className="h-4 w-4 mr-2" />
            Automatización
          </TabsTrigger>
          <TabsTrigger value="dashboard">
            <BarChart3 className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
        </TabsList>

        {/* ==================== TAB: COMPETITORS ==================== */}
        <TabsContent value="competitors" className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : competitors.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay competidores configurados</p>
              <p className="text-sm">Añade un competidor para empezar a comparar precios</p>
              <Button className="mt-4" onClick={openCreateCompetitor}>
                <Plus className="h-4 w-4 mr-2" />
                Añadir Competidor
              </Button>
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nombre</TableHead>
                    <TableHead>Canal</TableHead>
                    <TableHead>País</TableHead>
                    <TableHead>Último Crawl</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Snapshots</TableHead>
                    <TableHead className="w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {competitors.map((comp) => (
                    <TableRow key={comp.id}>
                      <TableCell>
                        <div>
                          <span className="font-medium">{comp.name}</span>
                          <p className="text-xs text-muted-foreground truncate max-w-[250px]">
                            {comp.base_url}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{getChannelLabel(comp.channel)}</Badge>
                      </TableCell>
                      <TableCell>{comp.country}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {comp.last_crawl_at
                          ? new Date(comp.last_crawl_at).toLocaleString("es-ES")
                          : "Nunca"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <CrawlStatusBadge status={comp.last_crawl_status} />
                          {!comp.active && (
                            <Badge variant="secondary">Inactivo</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{comp.total_snapshots}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => triggerCrawl(comp.id)}>
                              <Play className="h-4 w-4 mr-2" />
                              Scrapear ahora
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openEditCompetitor(comp)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => {
                                setSelectedCompetitor(comp);
                                setShowDeleteDialog(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* ==================== TAB: ALERTS ==================== */}
        <TabsContent value="alerts" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={openCreateAlert}>
              <Plus className="h-4 w-4 mr-2" />
              Nueva Alerta
            </Button>
          </div>

          {alerts.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay alertas configuradas</p>
              <p className="text-sm">Crea alertas para recibir notificaciones de cambios de precio</p>
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Producto</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Umbral</TableHead>
                    <TableHead>Canal</TableHead>
                    <TableHead>Disparos</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>
                        <span className="font-mono text-sm">
                          {alert.sku || alert.ean || "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        {ALERT_TYPES.find((t) => t.value === alert.alert_type)?.label || alert.alert_type}
                      </TableCell>
                      <TableCell>
                        {alert.threshold != null ? (
                          alert.alert_type === "price_below"
                            ? `${alert.threshold}€`
                            : `${alert.threshold}%`
                        ) : "—"}
                      </TableCell>
                      <TableCell>
                        {ALERT_CHANNELS.find((c) => c.value === alert.channel)?.label || alert.channel}
                      </TableCell>
                      <TableCell>{alert.trigger_count}</TableCell>
                      <TableCell>
                        <Badge variant={alert.active ? "default" : "secondary"}>
                          {alert.active ? "Activa" : "Inactiva"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditAlert(alert)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => {
                                setSelectedAlert(alert);
                                setShowDeleteAlertDialog(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* ==================== TAB: PENDING MATCHES ==================== */}
        <TabsContent value="matches" className="space-y-4">
          {pendingMatches.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <ShieldCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay matches pendientes</p>
              <p className="text-sm">
                Los matches de baja confianza aparecerán aquí para tu revisión
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                {pendingTotal} matches pendientes de revisión
              </p>
              {pendingMatches.map((match) => (
                <div
                  key={match.id}
                  className="border rounded-lg p-4 flex items-center justify-between gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm truncate">
                        {match.product_name || match.sku}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        Score: {(match.match_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      Candidato: {match.candidate_name}
                    </p>
                    {match.candidate_url && (
                      <a
                        href={match.candidate_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-500 hover:underline truncate block"
                      >
                        {match.candidate_url}
                      </a>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-green-600"
                      onClick={() => reviewMatch(match.id, "confirm")}
                    >
                      <CheckCircle2 className="h-4 w-4 mr-1" />
                      Confirmar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600"
                      onClick={() => reviewMatch(match.id, "reject")}
                    >
                      <XCircle className="h-4 w-4 mr-1" />
                      Rechazar
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ==================== TAB: REPORT ==================== */}
        <TabsContent value="report" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Input
                placeholder="Filtrar por categoría..."
                value={reportCategory}
                onChange={(e) => setReportCategory(e.target.value)}
                className="w-48"
              />
              <Input
                placeholder="ID de proveedor..."
                value={reportSupplier}
                onChange={(e) => setReportSupplier(e.target.value)}
                className="w-48"
              />
              <Button variant="outline" onClick={fetchReport} disabled={reportLoading}>
                {reportLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={exportPositioningCSV} disabled={!report}>
              <Download className="h-4 w-4 mr-2" />
              Exportar Informe
            </Button>
          </div>

          {reportLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : !report ? (
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Informe de posicionamiento competitivo</p>
              <p className="text-sm">Pulsa el botón de búsqueda para generar el informe</p>
              <Button className="mt-4" onClick={fetchReport}>
                <BarChart3 className="h-4 w-4 mr-2" />
                Generar Informe
              </Button>
            </div>
          ) : (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="border rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold">{report.summary?.total || 0}</p>
                  <p className="text-xs text-muted-foreground">Analizados</p>
                </div>
                <div className="border rounded-lg p-4 text-center bg-green-50 dark:bg-green-950">
                  <p className="text-2xl font-bold text-green-600">{report.summary?.cheaper || 0}</p>
                  <p className="text-xs text-green-600">Más baratos</p>
                </div>
                <div className="border rounded-lg p-4 text-center bg-blue-50 dark:bg-blue-950">
                  <p className="text-2xl font-bold text-blue-600">{report.summary?.equal || 0}</p>
                  <p className="text-xs text-blue-600">Igual precio</p>
                </div>
                <div className="border rounded-lg p-4 text-center bg-red-50 dark:bg-red-950">
                  <p className="text-2xl font-bold text-red-600">{report.summary?.expensive || 0}</p>
                  <p className="text-xs text-red-600">Más caros</p>
                </div>
                <div className="border rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-muted-foreground">{report.summary?.no_data || 0}</p>
                  <p className="text-xs text-muted-foreground">Sin datos</p>
                </div>
              </div>

              {/* Report table */}
              {report.items?.length > 0 ? (
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Producto</TableHead>
                        <TableHead>Mi precio</TableHead>
                        <TableHead>Mejor competidor</TableHead>
                        <TableHead>Posición</TableHead>
                        <TableHead>Diferencia</TableHead>
                        <TableHead>Comp.</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.items.slice(0, 100).map((item, idx) => (
                        <TableRow key={idx}>
                          <TableCell>
                            <div>
                              <span className="font-medium text-sm">{item.product_name}</span>
                              <p className="text-xs text-muted-foreground font-mono">
                                {item.sku || item.ean}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell className="font-medium">{item.my_price?.toFixed(2)}€</TableCell>
                          <TableCell>
                            <div>
                              <span className="font-medium">{item.best_competitor_price?.toFixed(2)}€</span>
                              <p className="text-xs text-muted-foreground">{item.best_competitor_name}</p>
                            </div>
                          </TableCell>
                          <TableCell>
                            {item.position === "cheaper" && (
                              <Badge className="bg-green-100 text-green-700 gap-1">
                                <ArrowDown className="h-3 w-3" />Más barato
                              </Badge>
                            )}
                            {item.position === "equal" && (
                              <Badge variant="secondary" className="gap-1">
                                <Equal className="h-3 w-3" />Igual
                              </Badge>
                            )}
                            {item.position === "expensive" && (
                              <Badge variant="destructive" className="gap-1">
                                <ArrowUp className="h-3 w-3" />Más caro
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {item.price_difference != null && (
                              <span className={item.price_difference > 0 ? "text-red-600" : "text-green-600"}>
                                {item.price_difference > 0 ? "+" : ""}{item.price_difference?.toFixed(2)}€
                                <span className="text-xs ml-1">
                                  ({item.price_difference_percent > 0 ? "+" : ""}{item.price_difference_percent?.toFixed(1)}%)
                                </span>
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">{item.competitors_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No hay datos de posicionamiento disponibles
                </p>
              )}
            </>
          )}
        </TabsContent>

        {/* ==================== TAB: AUTOMATION ==================== */}
        <TabsContent value="automation" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button onClick={openCreateRule}>
                <Plus className="h-4 w-4 mr-2" />
                Nueva Regla
              </Button>
              <Button
                variant="outline"
                onClick={() => runSimulation()}
                disabled={simulating || automationRules.length === 0}
              >
                {simulating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FlaskConical className="h-4 w-4 mr-2" />
                )}
                Simular
              </Button>
              <Button
                variant="default"
                onClick={() => {
                  if (window.confirm("¿Aplicar todas las reglas activas? Los precios se actualizarán.")) {
                    applyAutomation();
                  }
                }}
                disabled={applying || automationRules.length === 0}
              >
                {applying ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Rocket className="h-4 w-4 mr-2" />
                )}
                Aplicar
              </Button>
            </div>
          </div>

          {/* Simulation results */}
          {simulation && (
            <div className="border rounded-lg p-4 bg-amber-50 dark:bg-amber-950 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <FlaskConical className="h-4 w-4" />
                  Resultado de la simulación
                </h3>
                <Badge variant="outline">
                  {simulation.total_changes} cambios · {simulation.rules_evaluated} reglas
                </Badge>
              </div>
              {simulation.changes?.length > 0 ? (
                <div className="border rounded-lg bg-background">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Producto</TableHead>
                        <TableHead>Precio actual</TableHead>
                        <TableHead>Nuevo precio</TableHead>
                        <TableHead>Cambio</TableHead>
                        <TableHead>Regla</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {simulation.changes.slice(0, 50).map((ch, idx) => (
                        <TableRow key={idx}>
                          <TableCell>
                            <span className="text-sm">{ch.product_name}</span>
                            <p className="text-xs text-muted-foreground font-mono">{ch.sku || ch.ean}</p>
                          </TableCell>
                          <TableCell>{ch.current_price?.toFixed(2)}€</TableCell>
                          <TableCell className="font-medium">{ch.new_price?.toFixed(2)}€</TableCell>
                          <TableCell>
                            <span className={ch.change_amount < 0 ? "text-green-600" : "text-red-600"}>
                              {ch.change_amount > 0 ? "+" : ""}{ch.change_amount?.toFixed(2)}€
                              <span className="text-xs ml-1">({ch.change_percent > 0 ? "+" : ""}{ch.change_percent?.toFixed(1)}%)</span>
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs">{ch.rule_name}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No hay cambios que aplicar con las reglas actuales</p>
              )}
            </div>
          )}

          {/* Rules list */}
          {automationLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : automationRules.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay reglas de automatización</p>
              <p className="text-sm">Crea reglas para ajustar precios automáticamente según la competencia</p>
              <Button className="mt-4" onClick={openCreateRule}>
                <Plus className="h-4 w-4 mr-2" />
                Nueva Regla
              </Button>
            </div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nombre</TableHead>
                    <TableHead>Estrategia</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Aplica a</TableHead>
                    <TableHead>Prioridad</TableHead>
                    <TableHead>Último uso</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {automationRules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell className="font-medium">{rule.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {AUTOMATION_STRATEGIES.find((s) => s.value === rule.strategy)?.label || rule.strategy}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {rule.strategy === "price_cap" || rule.strategy === "undercut_by_amount"
                          ? `${rule.value}€`
                          : `${rule.value}%`}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {APPLY_TO_OPTIONS.find((a) => a.value === rule.apply_to)?.label || rule.apply_to}
                          {rule.apply_to_value && (
                            <span className="text-xs text-muted-foreground ml-1">({rule.apply_to_value})</span>
                          )}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">{rule.priority}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {rule.last_applied_at
                          ? new Date(rule.last_applied_at).toLocaleString("es-ES")
                          : "Nunca"}
                        {rule.products_affected > 0 && (
                          <p className="text-xs">{rule.products_affected} productos</p>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={rule.active ? "default" : "secondary"}>
                          {rule.active ? "Activa" : "Inactiva"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => runSimulation(rule.id)}>
                              <FlaskConical className="h-4 w-4 mr-2" />
                              Simular esta regla
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openEditRule(rule)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => {
                                setSelectedRule(rule);
                                setShowDeleteRuleDialog(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* ==================== TAB: DASHBOARD ==================== */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Overview KPIs */}
          {dashboardOverview && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="border rounded-lg p-4 space-y-2">
                <p className="text-sm text-muted-foreground">Competidores Activos</p>
                <p className="text-3xl font-bold">{dashboardOverview.active_competitors || 0}</p>
              </div>
              <div className="border rounded-lg p-4 space-y-2">
                <p className="text-sm text-muted-foreground">Alertas Activas</p>
                <p className="text-3xl font-bold text-amber-600">{dashboardOverview.active_alerts || 0}</p>
              </div>
              <div className="border rounded-lg p-4 space-y-2">
                <p className="text-sm text-muted-foreground">SKUs Monitorizados</p>
                <p className="text-3xl font-bold">{dashboardOverview.monitored_skus || 0}</p>
              </div>
              <div className="border rounded-lg p-4 space-y-2">
                <p className="text-sm text-muted-foreground">Snapshots (7d)</p>
                <p className="text-3xl font-bold">{dashboardOverview.snapshots_last_7d || 0}</p>
              </div>
              <div className="border rounded-lg p-4 space-y-2">
                <p className="text-sm text-muted-foreground">Más Baratos (24h)</p>
                <p className="text-3xl font-bold text-red-600">{dashboardOverview.competitors_cheaper_24h || 0}</p>
              </div>
            </div>
          )}

          {/* Price Comparison Table */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Comparativa de Precios</h3>
              <Input
                placeholder="Buscar por SKU o nombre..."
                value={dashboardSearch}
                onChange={(e) => {
                  setDashboardSearch(e.target.value);
                  setDashboardPage(1);
                }}
                className="max-w-xs"
              />
            </div>

            {dashboardLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : dashboardTable.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No hay datos de precios disponibles</p>
                <p className="text-sm">Ejecuta un scraping para cargar datos de competidores</p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>SKU / Nombre</TableHead>
                      <TableHead>EAN</TableHead>
                      <TableHead className="text-right">Mi Precio</TableHead>
                      <TableHead className="text-right">Mejor Competencia</TableHead>
                      <TableHead className="text-center">Brecha (€)</TableHead>
                      <TableHead className="text-center">Brecha (%)</TableHead>
                      <TableHead className="text-center">Margen %</TableHead>
                      <TableHead className="text-center">Cambio 24h</TableHead>
                      <TableHead className="text-center">Competidores</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dashboardTable.map((item) => (
                      <TableRow key={item.sku}>
                        <TableCell>
                          <div>
                            <span className="font-medium">{item.sku}</span>
                            <p className="text-xs text-muted-foreground truncate max-w-[250px]">
                              {item.name}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {item.ean || "-"}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          €{item.my_price?.toFixed(2) || "-"}
                        </TableCell>
                        <TableCell className="text-right font-medium text-red-600">
                          €{item.best_competitor_price?.toFixed(2) || "-"}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge
                            variant={
                              item.gap_eur > 0
                                ? "default"
                                : item.gap_eur < 0
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {item.gap_eur > 0 ? "+" : ""}
                            €{item.gap_eur?.toFixed(2) || "0"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          {item.gap_percent > 0 ? (
                            <div className="flex items-center justify-center gap-1 text-green-600">
                              <ArrowUp className="h-3 w-3" />
                              {item.gap_percent.toFixed(1)}%
                            </div>
                          ) : item.gap_percent < 0 ? (
                            <div className="flex items-center justify-center gap-1 text-red-600">
                              <ArrowDown className="h-3 w-3" />
                              {Math.abs(item.gap_percent).toFixed(1)}%
                            </div>
                          ) : (
                            <Equal className="h-4 w-4 mx-auto text-muted-foreground" />
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline">
                            {item.margin_percent?.toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center text-sm">
                          {item.price_change_24h_percent > 0 ? (
                            <div className="flex items-center justify-center gap-1 text-green-600">
                              <TrendingUp className="h-3 w-3" />
                              +{item.price_change_24h_percent.toFixed(1)}%
                            </div>
                          ) : item.price_change_24h_percent < 0 ? (
                            <div className="flex items-center justify-center gap-1 text-red-600">
                              <TrendingDown className="h-3 w-3" />
                              {item.price_change_24h_percent.toFixed(1)}%
                            </div>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center text-sm font-medium">
                          {item.competitors?.length || 0}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Pagination */}
            {dashboardTable.length > 0 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Mostrando {(dashboardPage - 1) * 20 + 1} a{" "}
                  {Math.min(dashboardPage * 20, dashboardTotal)} de {dashboardTotal} productos
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setDashboardPage((p) => Math.max(1, p - 1))}
                    disabled={dashboardPage === 1}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setDashboardPage((p) =>
                        Math.ceil(dashboardTotal / 20) > p ? p + 1 : p
                      )
                    }
                    disabled={dashboardPage >= Math.ceil(dashboardTotal / 20)}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Enriched Alerts */}
          <div className="space-y-4">
            <h3 className="font-semibold">Alertas Enriquecidas Recientes</h3>
            {enrichedAlerts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground border rounded-lg">
                <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No hay alertas recientes</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {enrichedAlerts.map((alert) => (
                  <div key={alert.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold">{alert.title}</h4>
                        <p className="text-xs text-muted-foreground">
                          {alert.sku} {alert.ean && `• ${alert.ean}`}
                        </p>
                      </div>
                      <Badge
                        variant={
                          alert.context?.action === "AUTO_REPRICE"
                            ? "default"
                            : alert.context?.action === "MANUAL_REVIEW"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {alert.context?.action || "INFO"}
                      </Badge>
                    </div>

                    <p className="text-sm">{alert.message_short}</p>

                    {alert.context && (
                      <div className="grid grid-cols-2 gap-2 text-xs border-t pt-2">
                        <div>
                          <p className="text-muted-foreground">Mi Precio</p>
                          <p className="font-semibold">€{alert.context.your_price?.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Competencia</p>
                          <p className="font-semibold">€{alert.context.best_competitor_price?.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Cambio</p>
                          <p className="font-semibold">
                            {alert.context.delta_percent > 0 ? "+" : ""}
                            {alert.context.delta_percent?.toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Posición</p>
                          <p className="font-semibold">
                            {alert.context.your_position || "N/A"}
                          </p>
                        </div>
                        {alert.context.trend && (
                          <div className="col-span-2">
                            <p className="text-muted-foreground">Tendencia</p>
                            <div className="flex items-center gap-1">
                              {alert.context.trend === "UPTREND" ? (
                                <>
                                  <TrendingUp className="h-3 w-3 text-red-600" />
                                  <span className="font-semibold text-red-600">Al alza</span>
                                </>
                              ) : alert.context.trend === "DOWNTREND" ? (
                                <>
                                  <TrendingDown className="h-3 w-3 text-green-600" />
                                  <span className="font-semibold text-green-600">A la baja</span>
                                </>
                              ) : (
                                <>
                                  <Equal className="h-3 w-3 text-muted-foreground" />
                                  <span className="font-semibold">Estable</span>
                                </>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {alert.context?.suggested_price && (
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                        <p className="text-xs text-muted-foreground">Precio Sugerido</p>
                        <p className="font-semibold text-blue-600">
                          €{alert.context.suggested_price.toFixed(2)}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* ==================== COMPETITOR DIALOG ==================== */}
      <Dialog open={showCompetitorDialog} onOpenChange={setShowCompetitorDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {selectedCompetitor ? "Editar Competidor" : "Nuevo Competidor"}
            </DialogTitle>
            <DialogDescription>
              Configura un competidor para monitorizar sus precios
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nombre *</Label>
              <Input
                placeholder="Ej: Amazon España"
                value={competitorForm.name}
                onChange={(e) =>
                  setCompetitorForm({ ...competitorForm, name: e.target.value })
                }
              />
            </div>
            <div>
              <Label>URL base *</Label>
              <Input
                placeholder="https://www.ejemplo.com"
                value={competitorForm.base_url}
                onChange={(e) =>
                  setCompetitorForm({ ...competitorForm, base_url: e.target.value })
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Canal</Label>
                <Select
                  value={competitorForm.channel}
                  onValueChange={(val) =>
                    setCompetitorForm({ ...competitorForm, channel: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((ch) => (
                      <SelectItem key={ch.value} value={ch.value}>
                        {ch.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>País</Label>
                <Input
                  placeholder="ES"
                  value={competitorForm.country}
                  maxLength={2}
                  onChange={(e) =>
                    setCompetitorForm({
                      ...competitorForm,
                      country: e.target.value.toUpperCase(),
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCompetitorDialog(false)}
            >
              Cancelar
            </Button>
            <Button onClick={saveCompetitor} disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {selectedCompetitor ? "Guardar" : "Crear"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== ALERT DIALOG ==================== */}
      <Dialog open={showAlertDialog} onOpenChange={setShowAlertDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {selectedAlert ? "Editar Alerta" : "Nueva Alerta de Precio"}
            </DialogTitle>
            <DialogDescription>
              Configura cuándo quieres recibir notificaciones
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>SKU</Label>
                <Input
                  placeholder="SKU del producto"
                  value={alertForm.sku}
                  onChange={(e) =>
                    setAlertForm({ ...alertForm, sku: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>EAN</Label>
                <Input
                  placeholder="EAN / código de barras"
                  value={alertForm.ean}
                  onChange={(e) =>
                    setAlertForm({ ...alertForm, ean: e.target.value })
                  }
                />
              </div>
            </div>
            <div>
              <Label>Tipo de alerta</Label>
              <Select
                value={alertForm.alert_type}
                onValueChange={(val) =>
                  setAlertForm({ ...alertForm, alert_type: val })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALERT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {(alertForm.alert_type === "price_drop" ||
              alertForm.alert_type === "price_below") && (
              <div>
                <Label>
                  {alertForm.alert_type === "price_below"
                    ? "Precio umbral (€)"
                    : "Porcentaje de bajada (%)"}
                </Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder={
                    alertForm.alert_type === "price_below" ? "99.99" : "10"
                  }
                  value={alertForm.threshold}
                  onChange={(e) =>
                    setAlertForm({ ...alertForm, threshold: e.target.value })
                  }
                />
              </div>
            )}
            <div>
              <Label>Canal de notificación</Label>
              <Select
                value={alertForm.channel}
                onValueChange={(val) =>
                  setAlertForm({ ...alertForm, channel: val })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALERT_CHANNELS.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {alertForm.channel === "webhook" && (
              <div>
                <Label>URL del Webhook</Label>
                <Input
                  placeholder="https://tu-servidor.com/webhook"
                  value={alertForm.webhook_url}
                  onChange={(e) =>
                    setAlertForm({ ...alertForm, webhook_url: e.target.value })
                  }
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAlertDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={saveAlert} disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {selectedAlert ? "Guardar" : "Crear"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== DELETE COMPETITOR DIALOG ==================== */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar competidor?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará <strong>{selectedCompetitor?.name}</strong> y todos sus
              snapshots de precios. Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteCompetitor}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ==================== DELETE ALERT DIALOG ==================== */}
      <AlertDialog
        open={showDeleteAlertDialog}
        onOpenChange={setShowDeleteAlertDialog}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar alerta?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta alerta dejará de monitorizar el producto. Esta acción no se
              puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteAlert}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ==================== AUTOMATION RULE DIALOG ==================== */}
      <Dialog open={showRuleDialog} onOpenChange={setShowRuleDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {selectedRule ? "Editar Regla" : "Nueva Regla de Automatización"}
            </DialogTitle>
            <DialogDescription>
              Define cómo se ajustarán los precios automáticamente
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nombre *</Label>
              <Input
                placeholder="Ej: Igualar Amazon en electrónica"
                value={ruleForm.name}
                onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Estrategia *</Label>
                <Select
                  value={ruleForm.strategy}
                  onValueChange={(val) => setRuleForm({ ...ruleForm, strategy: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AUTOMATION_STRATEGIES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>
                  Valor * {ruleForm.strategy === "undercut_by_amount" || ruleForm.strategy === "price_cap" ? "(€)" : "(%)"}
                </Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder={ruleForm.strategy === "match_cheapest" ? "0" : "5"}
                  value={ruleForm.value}
                  onChange={(e) => setRuleForm({ ...ruleForm, value: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Aplica a</Label>
                <Select
                  value={ruleForm.apply_to}
                  onValueChange={(val) => setRuleForm({ ...ruleForm, apply_to: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {APPLY_TO_OPTIONS.map((a) => (
                      <SelectItem key={a.value} value={a.value}>
                        {a.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {ruleForm.apply_to !== "all" && (
                <div>
                  <Label>Valor del filtro</Label>
                  <Input
                    placeholder={ruleForm.apply_to === "category" ? "Electrónica" : "ID..."}
                    value={ruleForm.apply_to_value}
                    onChange={(e) => setRuleForm({ ...ruleForm, apply_to_value: e.target.value })}
                  />
                </div>
              )}
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Precio mín (€)</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0"
                  value={ruleForm.min_price}
                  onChange={(e) => setRuleForm({ ...ruleForm, min_price: e.target.value })}
                />
              </div>
              <div>
                <Label>Precio máx (€)</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="Sin límite"
                  value={ruleForm.max_price}
                  onChange={(e) => setRuleForm({ ...ruleForm, max_price: e.target.value })}
                />
              </div>
              <div>
                <Label>Prioridad</Label>
                <Input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={ruleForm.priority}
                  onChange={(e) => setRuleForm({ ...ruleForm, priority: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRuleDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={saveRule} disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {selectedRule ? "Guardar" : "Crear"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ==================== DELETE RULE DIALOG ==================== */}
      <AlertDialog open={showDeleteRuleDialog} onOpenChange={setShowDeleteRuleDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar regla?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la regla <strong>{selectedRule?.name}</strong>. Los precios
              ya aplicados no se revertirán.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteRule}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Competitors;
