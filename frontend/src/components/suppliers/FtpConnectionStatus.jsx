import { CheckCircle, WifiOff } from "lucide-react";
import { Badge } from "../ui/badge";

const FtpConnectionStatus = ({ status }) => {
  if (!status) return null;

  return (
    <div className={`p-3 rounded-lg border ${
      status.connected 
        ? "bg-emerald-50 border-emerald-200" 
        : "bg-rose-50 border-rose-200"
    }`} data-testid="ftp-connection-status">
      <div className="flex items-start gap-3">
        {status.connected ? (
          <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
        ) : (
          <WifiOff className="w-5 h-5 text-rose-500 flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <p className={`font-medium text-sm ${
            status.connected ? "text-emerald-800" : "text-rose-800"
          }`}>
            {status.connected ? "Conexión exitosa" : "Error de conexión"}
          </p>
          <p className="text-xs text-slate-600 mt-0.5">{status.message}</p>
          {status.connected && (
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline" className="text-xs">
                {status.protocol}
              </Badge>
              {status.mode && (
                <Badge variant="outline" className="text-xs">
                  Modo {status.mode}
                </Badge>
              )}
              {status.files_in_root !== undefined && (
                <Badge variant="outline" className="text-xs">
                  {status.files_in_root} items en raíz
                </Badge>
              )}
            </div>
          )}
          {status.suggestion && (
            <p className="text-xs text-amber-700 mt-2 bg-amber-50 px-2 py-1 rounded">
              💡 {status.suggestion}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default FtpConnectionStatus;
