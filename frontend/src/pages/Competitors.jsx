import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import { Plus, Loader2, Play, Download, Globe, Bell, ShieldCheck, BarChart3, Zap, Settings2 } from "lucide-react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
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
  CompetitorsTab,
  AlertsTab,
  MatchesTab,
  ReportTab,
  AutomationTab,
  DashboardTab,
  ConfigTab,
  CompetitorDialog,
  AlertDialog as AlertFormDialog,
  RuleDialog,
} from "../components/competitors";

// ==================== DEFAULTS ====================

const defaultCompetitorForm = { name: "", base_url: "", channel: "web_directa", country: "ES", active: true };
const defaultAlertForm = { sku: "", ean: "", alert_type: "competitor_cheaper", threshold: "", channel: "app", webhook_url: "", active: true };
const defaultRuleForm = { name: "", strategy: "match_cheapest", value: "", apply_to: "all", apply_to_value: "", min_price: "", max_price: "", catalog_id: "", priority: "0", active: true };

// ==================== COMPONENT ====================

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

  // Pending matches
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

  // Configuration state
  const [monitoringCatalog, setMonitoringCatalog] = useState(null);
  const [availableCatalogs, setAvailableCatalogs] = useState([]);
  const [configLoading, setConfigLoading] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);

  // Active tab
  const [activeTab, setActiveTab] = useState("competitors");

  // ==================== DATA FETCHING ====================

  const fetchCompetitors = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/competitors");
      setCompetitors(res.data);
    } catch { toast.error("Error al cargar competidores"); }
    finally { setLoading(false); }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await api.get("/competitors/alerts");
      setAlerts(res.data);
    } catch { toast.error("Error al cargar alertas"); }
  }, []);

  const fetchCrawlStatus = useCallback(async () => {
    try {
      const res = await api.get("/competitors/crawl/status");
      setCrawlStatus(res.data.competitors);
      setCrawlRunning(res.data.crawl_running);
    } catch { /* silent */ }
  }, []);

  const fetchPendingMatches = useCallback(async () => {
    try {
      const res = await api.get("/competitors/matches/pending?limit=20");
      setPendingMatches(res.data.matches);
      setPendingTotal(res.data.total);
    } catch { /* silent */ }
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
    } catch { toast.error("Error al cargar informe de posicionamiento"); }
    finally { setReportLoading(false); }
  }, [reportCategory, reportSupplier]);

  const fetchAutomationRules = useCallback(async () => {
    try {
      setAutomationLoading(true);
      const res = await api.get("/competitors/automation/rules");
      setAutomationRules(res.data.rules || []);
    } catch { toast.error("Error al cargar reglas de automatización"); }
    finally { setAutomationLoading(false); }
  }, []);

  const fetchDashboardOverview = useCallback(async () => {
    try {
      const res = await api.get("/competitors/dashboard/overview");
      setDashboardOverview(res.data);
    } catch { /* silent */ }
  }, []);

  const fetchDashboardTable = useCallback(async (page = 1, search = "") => {
    try {
      setDashboardLoading(true);
      const params = new URLSearchParams({ page, page_size: 20 });
      if (search) params.set("search", search);
      const res = await api.get(`/competitors/dashboard/table?${params.toString()}`);
      setDashboardTable(res.data.items || []);
      setDashboardTotal(res.data.total || 0);
    } catch { toast.error("Error al cargar tabla del dashboard"); }
    finally { setDashboardLoading(false); }
  }, []);

  const fetchEnrichedAlerts = useCallback(async () => {
    try {
      const res = await api.get("/competitors/dashboard/alerts/enriched");
      setEnrichedAlerts(res.data.alerts || []);
    } catch { /* silent */ }
  }, []);

  const fetchMonitoringCatalog = useCallback(async () => {
    try {
      setConfigLoading(true);
      const res = await api.get("/competitors/config/monitoring-catalog");
      setMonitoringCatalog(res.data);
    } catch { /* silent */ }
    finally { setConfigLoading(false); }
  }, []);

  const fetchAvailableCatalogs = useCallback(async () => {
    try {
      const res = await api.get("/competitors/config/available-catalogs");
      setAvailableCatalogs(res.data.catalogs || []);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchCompetitors();
    fetchAlerts();
    fetchCrawlStatus();
    fetchPendingMatches();
    fetchMonitoringCatalog();
    fetchAvailableCatalogs();
  }, [fetchCompetitors, fetchAlerts, fetchCrawlStatus, fetchPendingMatches, fetchMonitoringCatalog, fetchAvailableCatalogs]);

  const searchTimerRef = useRef(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => setDebouncedSearch(dashboardSearch), 400);
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
    setCompetitorForm({ name: competitor.name, base_url: competitor.base_url, channel: competitor.channel, country: competitor.country, active: competitor.active });
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
    } catch { toast.error("Error al eliminar competidor"); }
  };

  // ==================== CRAWL ====================

  const triggerCrawl = async (competitorId = null) => {
    try {
      setCrawlRunning(true);
      const params = competitorId ? `?competitor_id=${competitorId}` : "";
      await api.post(`/competitors/crawl${params}`);
      toast.success("Crawl iniciado en background");
      setTimeout(fetchCrawlStatus, 5000);
      setTimeout(fetchCrawlStatus, 15000);
      setTimeout(() => { fetchCrawlStatus(); fetchPendingMatches(); }, 30000);
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
    setAlertForm({ sku: alert.sku || "", ean: alert.ean || "", alert_type: alert.alert_type, threshold: alert.threshold?.toString() || "", channel: alert.channel, webhook_url: alert.webhook_url || "", active: alert.active });
    setShowAlertDialog(true);
  };

  const saveAlert = async () => {
    if (!alertForm.sku && !alertForm.ean) { toast.error("Debes indicar un SKU o EAN"); return; }
    try {
      setSaving(true);
      const data = { ...alertForm, threshold: alertForm.threshold ? parseFloat(alertForm.threshold) : null, sku: alertForm.sku || null, ean: alertForm.ean || null, webhook_url: alertForm.channel === "webhook" ? alertForm.webhook_url : null };
      if (selectedAlert) { await api.put(`/competitors/alerts/${selectedAlert.id}`, data); toast.success("Alerta actualizada"); }
      else { await api.post("/competitors/alerts", data); toast.success("Alerta creada"); }
      setShowAlertDialog(false);
      fetchAlerts();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar alerta");
    } finally { setSaving(false); }
  };

  const deleteAlert = async () => {
    if (!selectedAlert) return;
    try {
      await api.delete(`/competitors/alerts/${selectedAlert.id}`);
      toast.success("Alerta eliminada");
      setShowDeleteAlertDialog(false);
      setSelectedAlert(null);
      fetchAlerts();
    } catch { toast.error("Error al eliminar alerta"); }
  };

  // ==================== PENDING MATCHES ====================

  const reviewMatch = async (matchId, action) => {
    try {
      await api.put(`/competitors/matches/${matchId}?action=${action}`);
      toast.success(action === "confirm" ? "Match confirmado" : "Match rechazado");
      fetchPendingMatches();
    } catch { toast.error("Error al revisar el match"); }
  };

  // ==================== EXPORT ====================

  const exportPricesCSV = async () => {
    try {
      const res = await api.get("/competitors/export/prices?days=30", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `precios_competidores_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Exportación CSV descargada");
    } catch { toast.error("Error al exportar precios"); }
  };

  const exportPositioningCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (reportCategory) params.set("category", reportCategory);
      if (reportSupplier) params.set("supplier_id", reportSupplier);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await api.get(`/competitors/report/positioning/export${qs}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `informe_posicionamiento_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Informe CSV descargado");
    } catch { toast.error("Error al exportar informe"); }
  };

  // ==================== AUTOMATION CRUD ====================

  const openCreateRule = () => {
    setSelectedRule(null);
    setRuleForm(defaultRuleForm);
    setShowRuleDialog(true);
  };

  const openEditRule = (rule) => {
    setSelectedRule(rule);
    setRuleForm({ name: rule.name, strategy: rule.strategy, value: rule.value?.toString() || "", apply_to: rule.apply_to || "all", apply_to_value: rule.apply_to_value || "", min_price: rule.min_price?.toString() || "", max_price: rule.max_price?.toString() || "", catalog_id: rule.catalog_id || "", priority: rule.priority?.toString() || "0", active: rule.active });
    setShowRuleDialog(true);
  };

  const saveRule = async () => {
    if (!ruleForm.name.trim()) { toast.error("El nombre es obligatorio"); return; }
    if (!ruleForm.value || parseFloat(ruleForm.value) < 0) { toast.error("El valor debe ser un número >= 0"); return; }
    try {
      setSaving(true);
      const data = { name: ruleForm.name.trim(), strategy: ruleForm.strategy, value: parseFloat(ruleForm.value), apply_to: ruleForm.apply_to, apply_to_value: ruleForm.apply_to_value || null, min_price: ruleForm.min_price ? parseFloat(ruleForm.min_price) : 0, max_price: ruleForm.max_price ? parseFloat(ruleForm.max_price) : null, catalog_id: ruleForm.catalog_id || null, priority: parseInt(ruleForm.priority) || 0, active: ruleForm.active };
      if (selectedRule) { await api.put(`/competitors/automation/rules/${selectedRule.id}`, data); toast.success("Regla actualizada"); }
      else { await api.post("/competitors/automation/rules", data); toast.success("Regla creada"); }
      setShowRuleDialog(false);
      fetchAutomationRules();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar regla");
    } finally { setSaving(false); }
  };

  const deleteRule = async () => {
    if (!selectedRule) return;
    try {
      await api.delete(`/competitors/automation/rules/${selectedRule.id}`);
      toast.success("Regla eliminada");
      setShowDeleteRuleDialog(false);
      setSelectedRule(null);
      fetchAutomationRules();
    } catch { toast.error("Error al eliminar regla"); }
  };

  const runSimulation = async (ruleId = null) => {
    try {
      setSimulating(true);
      const params = ruleId ? `?rule_id=${ruleId}&limit=100` : "?limit=100";
      const res = await api.post(`/competitors/automation/simulate${params}`);
      setSimulation(res.data);
    } catch { toast.error("Error al simular automatización"); }
    finally { setSimulating(false); }
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
    } finally { setApplying(false); }
  };

  const saveMonitoringCatalog = async (catalogId) => {
    try {
      setSavingConfig(true);
      const res = await api.put("/competitors/config/monitoring-catalog", { catalog_id: catalogId });
      setMonitoringCatalog(res.data);
      toast.success("Catálogo de monitoreo actualizado");
    } catch { toast.error("Error al actualizar catálogo de monitoreo"); }
    finally { setSavingConfig(false); }
  };

  // ==================== RENDER ====================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Monitorización de Competidores</h1>
          <p className="text-sm text-muted-foreground">Compara precios con la competencia y configura alertas</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={exportPricesCSV}>
            <Download className="h-4 w-4 mr-2" />
            Exportar CSV
          </Button>
          <Button variant="outline" onClick={() => triggerCrawl()} disabled={crawlRunning || competitors.length === 0}>
            {crawlRunning ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
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
          <TabsTrigger value="competitors"><Globe className="h-4 w-4 mr-2" />Competidores ({competitors.length})</TabsTrigger>
          <TabsTrigger value="alerts"><Bell className="h-4 w-4 mr-2" />Alertas ({alerts.length})</TabsTrigger>
          <TabsTrigger value="matches"><ShieldCheck className="h-4 w-4 mr-2" />Revisión ({pendingTotal})</TabsTrigger>
          <TabsTrigger value="report" onClick={() => !report && fetchReport()}><BarChart3 className="h-4 w-4 mr-2" />Informes</TabsTrigger>
          <TabsTrigger value="automation" onClick={() => automationRules.length === 0 && fetchAutomationRules()}><Zap className="h-4 w-4 mr-2" />Automatización</TabsTrigger>
          <TabsTrigger value="dashboard"><BarChart3 className="h-4 w-4 mr-2" />Dashboard</TabsTrigger>
          <TabsTrigger value="config"><Settings2 className="h-4 w-4 mr-2" />Configuración</TabsTrigger>
        </TabsList>

        <TabsContent value="competitors" className="space-y-4">
          <CompetitorsTab
            competitors={competitors}
            loading={loading}
            onAdd={openCreateCompetitor}
            onEdit={openEditCompetitor}
            onDelete={(comp) => { setSelectedCompetitor(comp); setShowDeleteDialog(true); }}
            onCrawl={triggerCrawl}
          />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <AlertsTab
            alerts={alerts}
            onAdd={openCreateAlert}
            onEdit={openEditAlert}
            onDelete={(alert) => { setSelectedAlert(alert); setShowDeleteAlertDialog(true); }}
          />
        </TabsContent>

        <TabsContent value="matches" className="space-y-4">
          <MatchesTab pendingMatches={pendingMatches} pendingTotal={pendingTotal} onReview={reviewMatch} />
        </TabsContent>

        <TabsContent value="report" className="space-y-4">
          <ReportTab
            report={report}
            reportLoading={reportLoading}
            reportCategory={reportCategory}
            reportSupplier={reportSupplier}
            onCategoryChange={setReportCategory}
            onSupplierChange={setReportSupplier}
            onFetch={fetchReport}
            onExport={exportPositioningCSV}
          />
        </TabsContent>

        <TabsContent value="automation" className="space-y-4">
          <AutomationTab
            automationRules={automationRules}
            automationLoading={automationLoading}
            simulation={simulation}
            simulating={simulating}
            applying={applying}
            onAdd={openCreateRule}
            onEdit={openEditRule}
            onDelete={(rule) => { setSelectedRule(rule); setShowDeleteRuleDialog(true); }}
            onSimulate={runSimulation}
            onApply={applyAutomation}
          />
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-6">
          <DashboardTab
            dashboardOverview={dashboardOverview}
            dashboardTable={dashboardTable}
            dashboardLoading={dashboardLoading}
            dashboardSearch={dashboardSearch}
            dashboardPage={dashboardPage}
            dashboardTotal={dashboardTotal}
            enrichedAlerts={enrichedAlerts}
            onSearchChange={(v) => { setDashboardSearch(v); setDashboardPage(1); }}
            onPageChange={setDashboardPage}
          />
        </TabsContent>

        <TabsContent value="config" className="space-y-6">
          <ConfigTab
            monitoringCatalog={monitoringCatalog}
            availableCatalogs={availableCatalogs}
            configLoading={configLoading}
            savingConfig={savingConfig}
            onSelect={saveMonitoringCatalog}
          />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CompetitorDialog
        open={showCompetitorDialog}
        onOpenChange={setShowCompetitorDialog}
        isEdit={!!selectedCompetitor}
        form={competitorForm}
        onChange={setCompetitorForm}
        onSave={saveCompetitor}
        saving={saving}
      />

      <AlertFormDialog
        open={showAlertDialog}
        onOpenChange={setShowAlertDialog}
        isEdit={!!selectedAlert}
        form={alertForm}
        onChange={setAlertForm}
        onSave={saveAlert}
        saving={saving}
      />

      <RuleDialog
        open={showRuleDialog}
        onOpenChange={setShowRuleDialog}
        isEdit={!!selectedRule}
        form={ruleForm}
        onChange={setRuleForm}
        onSave={saveRule}
        saving={saving}
      />

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar competidor?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará <strong>{selectedCompetitor?.name}</strong> y todos sus snapshots. Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={deleteCompetitor} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showDeleteAlertDialog} onOpenChange={setShowDeleteAlertDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar alerta?</AlertDialogTitle>
            <AlertDialogDescription>Esta alerta dejará de monitorizar el producto. Esta acción no se puede deshacer.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={deleteAlert} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showDeleteRuleDialog} onOpenChange={setShowDeleteRuleDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar regla?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la regla <strong>{selectedRule?.name}</strong>. Los precios ya aplicados no se revertirán.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={deleteRule} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Competitors;
