import { useState, useEffect } from "react";
import { useAsyncData } from "../hooks/useAsyncData";
import { useCompetitorsCRUD } from "../hooks/useCompetitorsCRUD";
import { useAlertsCRUD } from "../hooks/useAlertsCRUD";
import { useAutomationCRUD } from "../hooks/useAutomationCRUD";
import { useCompetitorSupportData } from "../hooks/useCompetitorSupportData";
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

const Competitors = () => {
  const [activeTab, setActiveTab] = useState("competitors");

  const { data: competitors, loading, reload: fetchCompetitors } = useAsyncData(
    async () => {
      try {
        const res = await api.get("/competitors");
        return res.data;
      } catch { toast.error("Error al cargar competidores"); return []; }
    },
    [],
    { initialData: [] }
  );

  const comp = useCompetitorsCRUD(fetchCompetitors);
  const alertsCRUD = useAlertsCRUD();
  const automation = useAutomationCRUD();
  const support = useCompetitorSupportData();

  const {
    fetchDashboardOverview, fetchDashboardTable, fetchEnrichedAlerts,
    dashboardPage, debouncedSearch,
  } = support;

  useEffect(() => {
    alertsCRUD.fetchAlerts();
  }, [alertsCRUD.fetchAlerts]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (activeTab === "dashboard") {
      fetchDashboardOverview();
      fetchDashboardTable(dashboardPage, debouncedSearch);
      fetchEnrichedAlerts();
    }
  }, [activeTab, dashboardPage, debouncedSearch, fetchDashboardOverview, fetchDashboardTable, fetchEnrichedAlerts]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Monitorización de Competidores</h1>
          <p className="text-sm text-muted-foreground">Compara precios con la competencia y configura alertas</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={support.exportPricesCSV}>
            <Download className="h-4 w-4 mr-2" />
            Exportar CSV
          </Button>
          <Button variant="outline" onClick={() => support.triggerCrawl()} disabled={support.crawlRunning || competitors.length === 0}>
            {support.crawlRunning ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
            {support.crawlRunning ? "Scraping..." : "Iniciar Scraping"}
          </Button>
          <Button onClick={comp.openCreateCompetitor}>
            <Plus className="h-4 w-4 mr-2" />
            Añadir Competidor
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="competitors"><Globe className="h-4 w-4 mr-2" />Competidores ({competitors.length})</TabsTrigger>
          <TabsTrigger value="alerts"><Bell className="h-4 w-4 mr-2" />Alertas ({alertsCRUD.alerts.length})</TabsTrigger>
          <TabsTrigger value="matches"><ShieldCheck className="h-4 w-4 mr-2" />Revisión ({support.pendingTotal})</TabsTrigger>
          <TabsTrigger value="report" onClick={() => !support.report && support.fetchReport()}><BarChart3 className="h-4 w-4 mr-2" />Informes</TabsTrigger>
          <TabsTrigger value="automation" onClick={() => automation.automationRules.length === 0 && automation.fetchAutomationRules()}><Zap className="h-4 w-4 mr-2" />Automatización</TabsTrigger>
          <TabsTrigger value="dashboard"><BarChart3 className="h-4 w-4 mr-2" />Dashboard</TabsTrigger>
          <TabsTrigger value="config"><Settings2 className="h-4 w-4 mr-2" />Configuración</TabsTrigger>
        </TabsList>

        <TabsContent value="competitors" className="space-y-4">
          <CompetitorsTab
            competitors={competitors}
            loading={loading}
            onAdd={comp.openCreateCompetitor}
            onEdit={comp.openEditCompetitor}
            onDelete={(c) => { comp.setSelectedCompetitor(c); comp.setShowDeleteDialog(true); }}
            onCrawl={support.triggerCrawl}
          />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <AlertsTab
            alerts={alertsCRUD.alerts}
            onAdd={alertsCRUD.openCreateAlert}
            onEdit={alertsCRUD.openEditAlert}
            onDelete={(a) => { alertsCRUD.setSelectedAlert(a); alertsCRUD.setShowDeleteAlertDialog(true); }}
          />
        </TabsContent>

        <TabsContent value="matches" className="space-y-4">
          <MatchesTab pendingMatches={support.pendingMatches} pendingTotal={support.pendingTotal} onReview={support.reviewMatch} />
        </TabsContent>

        <TabsContent value="report" className="space-y-4">
          <ReportTab
            report={support.report}
            reportLoading={support.reportLoading}
            reportCategory={support.reportCategory}
            reportSupplier={support.reportSupplier}
            onCategoryChange={support.setReportCategory}
            onSupplierChange={support.setReportSupplier}
            onFetch={support.fetchReport}
            onExport={support.exportPositioningCSV}
          />
        </TabsContent>

        <TabsContent value="automation" className="space-y-4">
          <AutomationTab
            automationRules={automation.automationRules}
            automationLoading={automation.automationLoading}
            simulation={automation.simulation}
            simulating={automation.simulating}
            applying={automation.applying}
            onAdd={automation.openCreateRule}
            onEdit={automation.openEditRule}
            onDelete={(rule) => { automation.setSelectedRule(rule); automation.setShowDeleteRuleDialog(true); }}
            onSimulate={automation.runSimulation}
            onApply={automation.applyAutomation}
          />
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-6">
          <DashboardTab
            dashboardOverview={support.dashboardOverview}
            dashboardTable={support.dashboardTable}
            dashboardLoading={support.dashboardLoading}
            dashboardSearch={support.dashboardSearch}
            dashboardPage={support.dashboardPage}
            dashboardTotal={support.dashboardTotal}
            enrichedAlerts={support.enrichedAlerts}
            onSearchChange={(v) => { support.setDashboardSearch(v); support.setDashboardPage(1); }}
            onPageChange={support.setDashboardPage}
          />
        </TabsContent>

        <TabsContent value="config" className="space-y-6">
          <ConfigTab
            monitoringCatalog={support.monitoringCatalog}
            availableCatalogs={support.availableCatalogs}
            configLoading={support.configLoading}
            savingConfig={support.savingConfig}
            onSelect={support.saveMonitoringCatalog}
          />
        </TabsContent>
      </Tabs>

      {/* Form Dialogs */}
      <CompetitorDialog
        open={comp.showCompetitorDialog}
        onOpenChange={comp.setShowCompetitorDialog}
        isEdit={!!comp.selectedCompetitor}
        form={comp.competitorForm}
        onChange={comp.setCompetitorForm}
        onSave={comp.saveCompetitor}
        saving={comp.saving}
      />

      <AlertFormDialog
        open={alertsCRUD.showAlertDialog}
        onOpenChange={alertsCRUD.setShowAlertDialog}
        isEdit={!!alertsCRUD.selectedAlert}
        form={alertsCRUD.alertForm}
        onChange={alertsCRUD.setAlertForm}
        onSave={alertsCRUD.saveAlert}
        saving={alertsCRUD.saving}
      />

      <RuleDialog
        open={automation.showRuleDialog}
        onOpenChange={automation.setShowRuleDialog}
        isEdit={!!automation.selectedRule}
        form={automation.ruleForm}
        onChange={automation.setRuleForm}
        onSave={automation.saveRule}
        saving={automation.saving}
      />

      {/* Delete Dialogs */}
      <AlertDialog open={comp.showDeleteDialog} onOpenChange={comp.setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar competidor?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará <strong>{comp.selectedCompetitor?.name}</strong> y todos sus snapshots. Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={comp.deleteCompetitor} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={alertsCRUD.showDeleteAlertDialog} onOpenChange={alertsCRUD.setShowDeleteAlertDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar alerta?</AlertDialogTitle>
            <AlertDialogDescription>Esta alerta dejará de monitorizar el producto. Esta acción no se puede deshacer.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={alertsCRUD.deleteAlert} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={automation.showDeleteRuleDialog} onOpenChange={automation.setShowDeleteRuleDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar regla?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la regla <strong>{automation.selectedRule?.name}</strong>. Los precios ya aplicados no se revertirán.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={automation.deleteRule} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Competitors;
