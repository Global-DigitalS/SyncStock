import { useState, useCallback } from "react";

/**
 * Hook para gestionar el estado de uno o varios diálogos/modales.
 *
 * @param {string[]} dialogNames - Nombres de los diálogos a controlar.
 *
 * @returns {Object} Con las propiedades:
 *   - `isOpen(name)`         → boolean
 *   - `open(name, item?)`    → abre el diálogo y guarda el ítem seleccionado
 *   - `close(name)`          → cierra el diálogo y limpia el ítem
 *   - `closeAll()`           → cierra todos
 *   - `selected`             → ítem actualmente seleccionado (compartido entre diálogos)
 *
 * Uso:
 *   const dialogs = useDialogState(["create", "edit", "delete"]);
 *
 *   // Abrir con ítem:
 *   dialogs.open("edit", product);
 *
 *   // Leer estado:
 *   <Dialog open={dialogs.isOpen("edit")} onOpenChange={(v) => !v && dialogs.close("edit")}>
 *
 *   // Acceder al ítem seleccionado:
 *   const product = dialogs.selected;
 */
export function useDialogState(dialogNames = []) {
  const initial = Object.fromEntries(dialogNames.map((name) => [name, false]));
  const [openMap, setOpenMap] = useState(initial);
  const [selected, setSelected] = useState(null);

  const isOpen = useCallback((name) => Boolean(openMap[name]), [openMap]);

  const open = useCallback((name, item = null) => {
    setSelected(item);
    setOpenMap((prev) => ({ ...prev, [name]: true }));
  }, []);

  const close = useCallback((name) => {
    setOpenMap((prev) => ({ ...prev, [name]: false }));
    setSelected(null);
  }, []);

  const closeAll = useCallback(() => {
    setOpenMap(Object.fromEntries(dialogNames.map((n) => [n, false])));
    setSelected(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { isOpen, open, close, closeAll, selected };
}
