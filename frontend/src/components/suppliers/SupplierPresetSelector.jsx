import { useState, useEffect } from "react";
import { Zap, ChevronDown, ChevronUp, Check } from "lucide-react";
import { api } from "../../App";

const SupplierPresetSelector = ({ onApplyPreset, selectedId }) => {
  const [presets, setPresets] = useState([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.get("/suppliers/presets")
      .then((res) => setPresets(res.data))
      .catch(() => {});
  }, []);

  // Auto-expand if a preset is already selected so the user can see it
  useEffect(() => {
    if (selectedId) setExpanded(true);
  }, [selectedId]);

  if (!presets.length) return null;

  const activePreset = presets.find((p) => p.id === selectedId);

  return (
    <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/40 p-3">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center justify-between w-full text-sm font-medium text-slate-700 dark:text-slate-300"
      >
        <span className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-500" />
          {activePreset ? (
            <span className="flex items-center gap-1.5">
              Plantilla aplicada:
              <span className="font-semibold text-green-700 dark:text-green-400">
                {activePreset.name}
              </span>
              <Check className="w-3.5 h-3.5 text-green-500" />
            </span>
          ) : (
            "Usar plantilla de proveedor conocido"
          )}
        </span>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {presets.map((preset) => {
            const isActive = preset.id === selectedId;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => onApplyPreset(preset)}
                className={`flex items-start gap-2 rounded-md border px-3 py-2 text-left transition-colors ${
                  isActive
                    ? "border-green-400 bg-green-50 dark:border-green-600 dark:bg-green-950/30"
                    : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30"
                }`}
              >
                {isActive ? (
                  <Check className="w-4 h-4 mt-0.5 text-green-500 shrink-0" />
                ) : (
                  <Zap className="w-4 h-4 mt-0.5 text-amber-400 shrink-0" />
                )}
                <div>
                  <p className={`text-sm font-medium ${isActive ? "text-green-800 dark:text-green-200" : "text-slate-800 dark:text-slate-200"}`}>
                    {preset.name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {preset.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SupplierPresetSelector;
