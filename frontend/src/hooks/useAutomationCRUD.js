import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";

const defaultRuleForm = { name: "", strategy: "match_cheapest", value: "", apply_to: "all", apply_to_value: "", min_price: "", max_price: "", catalog_id: "", priority: "0", active: true };

export function useAutomationCRUD() {
  const [automationRules, setAutomationRules] = useState([]);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [showDeleteRuleDialog, setShowDeleteRuleDialog] = useState(false);
  const [selectedRule, setSelectedRule] = useState(null);
  const [ruleForm, setRuleForm] = useState(defaultRuleForm);
  const [simulation, setSimulation] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchAutomationRules = useCallback(async () => {
    try {
      setAutomationLoading(true);
      const res = await api.get("/competitors/automation/rules");
      setAutomationRules(res.data.rules || []);
    } catch { toast.error("Error al cargar reglas de automatización"); }
    finally { setAutomationLoading(false); }
  }, []);

  const openCreateRule = useCallback(() => {
    setSelectedRule(null);
    setRuleForm(defaultRuleForm);
    setShowRuleDialog(true);
  }, []);

  const openEditRule = useCallback((rule) => {
    setSelectedRule(rule);
    setRuleForm({ name: rule.name, strategy: rule.strategy, value: rule.value?.toString() || "", apply_to: rule.apply_to || "all", apply_to_value: rule.apply_to_value || "", min_price: rule.min_price?.toString() || "", max_price: rule.max_price?.toString() || "", catalog_id: rule.catalog_id || "", priority: rule.priority?.toString() || "0", active: rule.active });
    setShowRuleDialog(true);
  }, []);

  const saveRule = useCallback(async () => {
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
  }, [ruleForm, selectedRule, fetchAutomationRules]);

  const deleteRule = useCallback(async () => {
    if (!selectedRule) return;
    try {
      await api.delete(`/competitors/automation/rules/${selectedRule.id}`);
      toast.success("Regla eliminada");
      setShowDeleteRuleDialog(false);
      setSelectedRule(null);
      fetchAutomationRules();
    } catch { toast.error("Error al eliminar regla"); }
  }, [selectedRule, fetchAutomationRules]);

  const runSimulation = useCallback(async (ruleId = null) => {
    try {
      setSimulating(true);
      const params = ruleId ? `?rule_id=${ruleId}&limit=100` : "?limit=100";
      const res = await api.post(`/competitors/automation/simulate${params}`);
      setSimulation(res.data);
    } catch { toast.error("Error al simular automatización"); }
    finally { setSimulating(false); }
  }, []);

  const applyAutomation = useCallback(async (ruleId = null) => {
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
  }, [fetchAutomationRules]);

  return {
    automationRules, automationLoading,
    showRuleDialog, setShowRuleDialog,
    showDeleteRuleDialog, setShowDeleteRuleDialog,
    selectedRule, setSelectedRule,
    ruleForm, setRuleForm,
    simulation, simulating, applying, saving,
    fetchAutomationRules,
    openCreateRule, openEditRule,
    saveRule, deleteRule,
    runSimulation, applyAutomation,
  };
}
