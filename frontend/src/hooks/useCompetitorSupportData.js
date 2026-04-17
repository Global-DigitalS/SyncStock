import { useState, useCallback, useRef, useEffect } from "react";
import { toast } from "sonner";
import { api } from "../App";

export function useCompetitorSupportData() {
  const [crawlStatus, setCrawlStatus] = useState(null);
  const [crawlRunning, setCrawlRunning] = useState(false);
  const [pendingMatches, setPendingMatches] = useState([]);
  const [pendingTotal, setPendingTotal] = useState(0);
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportCategory, setReportCategory] = useState("");
  const [reportSupplier, setReportSupplier] = useState("");
  const [dashboardOverview, setDashboardOverview] = useState(null);
  const [dashboardTable, setDashboardTable] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardSearch, setDashboardSearch] = useState("");
  const [dashboardPage, setDashboardPage] = useState(1);
  const [dashboardTotal, setDashboardTotal] = useState(0);
  const [enrichedAlerts, setEnrichedAlerts] = useState([]);
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const searchTimerRef = useRef(null);
  const [monitoringCatalog, setMonitoringCatalog] = useState(null);
  const [availableCatalogs, setAvailableCatalogs] = useState([]);
  const [configLoading, setConfigLoading] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);

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

  const triggerCrawl = useCallback(async (competitorId = null) => {
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
  }, [fetchCrawlStatus, fetchPendingMatches]);

  const reviewMatch = useCallback(async (matchId, action) => {
    try {
      await api.put(`/competitors/matches/${matchId}?action=${action}`);
      toast.success(action === "confirm" ? "Match confirmado" : "Match rechazado");
      fetchPendingMatches();
    } catch { toast.error("Error al revisar el match"); }
  }, [fetchPendingMatches]);

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

  const exportPricesCSV = useCallback(async () => {
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
  }, []);

  const exportPositioningCSV = useCallback(async () => {
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
  }, [reportCategory, reportSupplier]);

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

  const saveMonitoringCatalog = useCallback(async (catalogId) => {
    try {
      setSavingConfig(true);
      const res = await api.put("/competitors/config/monitoring-catalog", { catalog_id: catalogId });
      setMonitoringCatalog(res.data);
      toast.success("Catálogo de monitoreo actualizado");
    } catch { toast.error("Error al actualizar catálogo de monitoreo"); }
    finally { setSavingConfig(false); }
  }, []);

  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => setDebouncedSearch(dashboardSearch), 400);
    return () => clearTimeout(searchTimerRef.current);
  }, [dashboardSearch]);

  useEffect(() => {
    fetchCrawlStatus();
    fetchPendingMatches();
    fetchMonitoringCatalog();
    fetchAvailableCatalogs();
  }, [fetchCrawlStatus, fetchPendingMatches, fetchMonitoringCatalog, fetchAvailableCatalogs]);

  return {
    crawlStatus, crawlRunning,
    fetchCrawlStatus, triggerCrawl,
    pendingMatches, pendingTotal,
    reviewMatch,
    report, reportLoading,
    reportCategory, setReportCategory,
    reportSupplier, setReportSupplier,
    fetchReport, exportPricesCSV, exportPositioningCSV,
    dashboardOverview, dashboardTable, dashboardLoading,
    dashboardSearch, setDashboardSearch,
    dashboardPage, setDashboardPage,
    dashboardTotal, enrichedAlerts, debouncedSearch,
    fetchDashboardOverview, fetchDashboardTable, fetchEnrichedAlerts,
    monitoringCatalog, availableCatalogs,
    configLoading, savingConfig,
    saveMonitoringCatalog,
  };
}
