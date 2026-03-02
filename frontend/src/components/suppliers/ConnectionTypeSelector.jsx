import { Server, Globe } from "lucide-react";
import { Label } from "../ui/label";

const ConnectionTypeSelector = ({ value, onChange }) => {
  return (
    <div className="p-3 bg-slate-50 rounded-sm mb-4" data-testid="connection-type-selector">
      <Label className="text-sm font-medium mb-3 block">Tipo de conexión</Label>
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onChange("ftp")}
          className={`p-3 rounded-lg border-2 text-left transition-all ${
            value === "ftp" 
              ? "border-indigo-500 bg-indigo-50" 
              : "border-slate-200 hover:border-slate-300"
          }`}
          data-testid="connection-type-ftp"
        >
          <div className="flex items-center gap-2 mb-1">
            <Server className={`w-4 h-4 ${value === "ftp" ? "text-indigo-600" : "text-slate-400"}`} />
            <span className={`font-medium ${value === "ftp" ? "text-indigo-900" : "text-slate-700"}`}>
              FTP / SFTP
            </span>
          </div>
          <p className="text-xs text-slate-500">Conexión a servidor FTP del proveedor</p>
        </button>
        <button
          type="button"
          onClick={() => onChange("url")}
          className={`p-3 rounded-lg border-2 text-left transition-all ${
            value === "url" 
              ? "border-indigo-500 bg-indigo-50" 
              : "border-slate-200 hover:border-slate-300"
          }`}
          data-testid="connection-type-url"
        >
          <div className="flex items-center gap-2 mb-1">
            <Globe className={`w-4 h-4 ${value === "url" ? "text-indigo-600" : "text-slate-400"}`} />
            <span className={`font-medium ${value === "url" ? "text-indigo-900" : "text-slate-700"}`}>
              URL Directa
            </span>
          </div>
          <p className="text-xs text-slate-500">Descargar desde URL HTTP/HTTPS</p>
        </button>
      </div>
    </div>
  );
};

export default ConnectionTypeSelector;
