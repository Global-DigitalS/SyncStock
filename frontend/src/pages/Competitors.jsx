import { useState, useEffect, useCallback } from "react";
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

  useEffect(() => {
    fetchCompetitors();
    fetchAlerts();
    fetchCrawlStatus();
    fetchPendingMatches();
  }, [fetchCompetitors, fetchAlerts, fetchCrawlStatus, fetchPendingMatches]);

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
    </div>
  );
};

export default Competitors;
