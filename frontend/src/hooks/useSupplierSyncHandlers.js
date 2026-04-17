import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../App";
import { useSyncProgress, SYNC_STEPS } from "../contexts/SyncProgressContext";

export function useSupplierSyncHandlers(supplierId, supplier, fetchData) {
  const [syncing, setSyncing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { startSync, completeSync, failSync } = useSyncProgress();

  const handleApplyPreset = useCallback(async () => {
    if (!supplier?.preset_id) return;
    setSyncing(true);
    try {
      await api.post(`/suppliers/${supplierId}/apply-preset`, { preset_id: supplier.preset_id });
      const syncRes = await api.post(`/suppliers/${supplierId}/sync`);
      if (syncRes.data.status === "queued") {
        toast.info("Plantilla aplicada. Sincronización iniciada en segundo plano...");
        toast.success("Sincronización completada");
      } else if (syncRes.data.imported + syncRes.data.updated > 0) {
        toast.success(`Plantilla aplicada y sincronización completada: ${syncRes.data.imported} nuevos, ${syncRes.data.updated} actualizados`);
      } else {
        toast.warning(syncRes.data.message || "Plantilla aplicada pero no se importaron productos.");
      }
      fetchData(1);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al aplicar la plantilla");
    } finally {
      setSyncing(false);
    }
  }, [supplierId, supplier, fetchData]);

  const handleSync = useCallback(async () => {
    const syncTitle = `Sincronizando ${supplier?.name || "Proveedor"}`;
    startSync(supplierId, syncTitle, SYNC_STEPS.supplier);
    setSyncing(true);
    try {
      const res = await api.post(`/suppliers/${supplierId}/sync`);
      if (res.data.status === "queued") return;
      if (res.data.needs_mapping) {
        toast.warning(res.data.message || "Se necesita configurar el mapeo de columnas", {
          duration: 8000,
          description: `Columnas detectadas: ${(res.data.detected_columns || []).slice(0, 5).join(", ")}...`,
        });
        completeSync(supplierId, "Requiere mapeo de columnas");
      } else if (res.data.status === "success" && res.data.imported + res.data.updated > 0) {
        completeSync(supplierId, `${res.data.imported} nuevos, ${res.data.updated} actualizados`);
      } else if (res.data.errors > 0 && res.data.imported + res.data.updated === 0) {
        toast.warning("Archivo descargado pero no se importaron productos. Verifica el mapeo de columnas.", { duration: 6000 });
        completeSync(supplierId, "Sin importaciones");
      } else {
        completeSync(supplierId, "Completado sin cambios");
      }
      fetchData();
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.response?.data?.detail || "Error en la sincronización";
      failSync(supplierId, errorMsg);
      toast.error(errorMsg);
    } finally {
      setSyncing(false);
    }
  }, [supplierId, supplier, fetchData, startSync, completeSync, failSync]);

  const handleFileUpload = useCallback(async (file) => {
    const validExtensions = [".csv", ".xlsx", ".xls", ".xml"];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf("."));
    if (!validExtensions.includes(ext)) {
      toast.error("Formato no soportado. Use CSV, XLSX, XLS o XML");
      return false;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post(`/products/import/${supplierId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`Importación completada: ${res.data.imported} nuevos, ${res.data.updated} actualizados`);
      fetchData();
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al importar productos");
      return false;
    } finally {
      setUploading(false);
    }
  }, [supplierId, fetchData]);

  return { syncing, uploading, handleSync, handleApplyPreset, handleFileUpload };
}
