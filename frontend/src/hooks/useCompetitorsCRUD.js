import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";

const defaultCompetitorForm = { name: "", base_url: "", channel: "web_directa", country: "ES", active: true };

export function useCompetitorsCRUD(onRefresh) {
  const [showCompetitorDialog, setShowCompetitorDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);
  const [competitorForm, setCompetitorForm] = useState(defaultCompetitorForm);
  const [saving, setSaving] = useState(false);

  const openCreateCompetitor = useCallback(() => {
    setSelectedCompetitor(null);
    setCompetitorForm(defaultCompetitorForm);
    setShowCompetitorDialog(true);
  }, []);

  const openEditCompetitor = useCallback((competitor) => {
    setSelectedCompetitor(competitor);
    setCompetitorForm({ name: competitor.name, base_url: competitor.base_url, channel: competitor.channel, country: competitor.country, active: competitor.active });
    setShowCompetitorDialog(true);
  }, []);

  const saveCompetitor = useCallback(async () => {
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
      onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar competidor");
    } finally {
      setSaving(false);
    }
  }, [competitorForm, selectedCompetitor, onRefresh]);

  const deleteCompetitor = useCallback(async () => {
    if (!selectedCompetitor) return;
    try {
      await api.delete(`/competitors/${selectedCompetitor.id}`);
      toast.success("Competidor eliminado");
      setShowDeleteDialog(false);
      setSelectedCompetitor(null);
      onRefresh();
    } catch { toast.error("Error al eliminar competidor"); }
  }, [selectedCompetitor, onRefresh]);

  return {
    showCompetitorDialog, setShowCompetitorDialog,
    showDeleteDialog, setShowDeleteDialog,
    selectedCompetitor, setSelectedCompetitor,
    competitorForm, setCompetitorForm,
    saving,
    openCreateCompetitor, openEditCompetitor,
    saveCompetitor, deleteCompetitor,
  };
}
