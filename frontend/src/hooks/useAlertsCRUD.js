import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";

const defaultAlertForm = { sku: "", ean: "", alert_type: "competitor_cheaper", threshold: "", channel: "app", webhook_url: "", active: true };

export function useAlertsCRUD() {
  const [alerts, setAlerts] = useState([]);
  const [showAlertDialog, setShowAlertDialog] = useState(false);
  const [showDeleteAlertDialog, setShowDeleteAlertDialog] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alertForm, setAlertForm] = useState(defaultAlertForm);
  const [saving, setSaving] = useState(false);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await api.get("/competitors/alerts");
      setAlerts(res.data);
    } catch { toast.error("Error al cargar alertas"); }
  }, []);

  const openCreateAlert = useCallback(() => {
    setSelectedAlert(null);
    setAlertForm(defaultAlertForm);
    setShowAlertDialog(true);
  }, []);

  const openEditAlert = useCallback((alert) => {
    setSelectedAlert(alert);
    setAlertForm({ sku: alert.sku || "", ean: alert.ean || "", alert_type: alert.alert_type, threshold: alert.threshold?.toString() || "", channel: alert.channel, webhook_url: alert.webhook_url || "", active: alert.active });
    setShowAlertDialog(true);
  }, []);

  const saveAlert = useCallback(async () => {
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
  }, [alertForm, selectedAlert, fetchAlerts]);

  const deleteAlert = useCallback(async () => {
    if (!selectedAlert) return;
    try {
      await api.delete(`/competitors/alerts/${selectedAlert.id}`);
      toast.success("Alerta eliminada");
      setShowDeleteAlertDialog(false);
      setSelectedAlert(null);
      fetchAlerts();
    } catch { toast.error("Error al eliminar alerta"); }
  }, [selectedAlert, fetchAlerts]);

  return {
    alerts,
    showAlertDialog, setShowAlertDialog,
    showDeleteAlertDialog, setShowDeleteAlertDialog,
    selectedAlert, setSelectedAlert,
    alertForm, setAlertForm,
    saving,
    fetchAlerts,
    openCreateAlert, openEditAlert,
    saveAlert, deleteAlert,
  };
}
