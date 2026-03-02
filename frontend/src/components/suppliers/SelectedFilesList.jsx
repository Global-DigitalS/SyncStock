import { FileArchive, X } from "lucide-react";

const ROLE_LABELS = {
  products: "Productos",
  prices: "Precios",
  stock: "Stock",
  prices_qb: "Precios Vol.",
  kit: "Kits",
  min_qty: "Cant. Mín.",
  other: "Otro"
};

const ROLE_COLORS = {
  products: "bg-indigo-100 text-indigo-700",
  prices: "bg-emerald-100 text-emerald-700",
  stock: "bg-amber-100 text-amber-700",
  prices_qb: "bg-purple-100 text-purple-700",
  kit: "bg-slate-100 text-slate-700",
  min_qty: "bg-blue-100 text-blue-700",
  other: "bg-slate-100 text-slate-700"
};

const SelectedFilesList = ({ files, onRemove, onUpdateRole }) => {
  if (files.length === 0) return null;

  return (
    <div className="p-3 bg-indigo-50/50 border-b border-slate-200" data-testid="selected-files-list">
      <p className="text-xs font-medium text-slate-600 mb-2">
        Archivos seleccionados para sincronización:
      </p>
      <div className="space-y-1.5">
        {files.map((file) => (
          <div 
            key={file.path} 
            className="flex items-center gap-2 bg-white rounded-md px-3 py-2 border border-slate-200"
          >
            <FileArchive className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <span className="text-xs font-mono text-slate-700 flex-1 truncate">
              {file.label || file.path}
            </span>
            <select
              value={file.role}
              onChange={(e) => onUpdateRole(file.path, e.target.value)}
              className="text-xs border border-slate-200 rounded px-2 py-1 bg-white"
              data-testid={`file-role-${file.path}`}
            >
              {Object.entries(ROLE_LABELS).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[file.role] || ROLE_COLORS.other}`}>
              {ROLE_LABELS[file.role] || file.role}
            </span>
            <button 
              type="button" 
              onClick={() => onRemove(file.path)}
              className="text-slate-400 hover:text-rose-500 transition-colors" 
              data-testid={`remove-file-${file.path}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export { ROLE_LABELS, ROLE_COLORS };
export default SelectedFilesList;
