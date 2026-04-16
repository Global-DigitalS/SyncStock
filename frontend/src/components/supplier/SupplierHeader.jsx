import { Truck, ArrowLeft, RefreshCw, Zap, Upload } from "lucide-react";
import { Button } from "../ui/button";

export function SupplierHeader({ supplier, syncing, onBack, onSync, onUpload }) {
  const showSyncBtn = supplier?.connection_type === "url" || supplier?.ftp_host;

  return (
    <div className="mb-6">
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-4 text-slate-600 hover:text-slate-900"
        data-testid="back-to-suppliers"
      >
        <ArrowLeft className="w-4 h-4 mr-2" strokeWidth={1.5} />
        Volver a Proveedores
      </Button>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-indigo-100 rounded-sm flex items-center justify-center">
            <Truck className="w-7 h-7 text-indigo-600" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
              {supplier?.name}
            </h1>
            {supplier?.description && (
              <p className="text-slate-500">{supplier.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {showSyncBtn && (
            <Button
              onClick={onSync}
              disabled={syncing}
              variant="outline"
              className="btn-secondary"
              data-testid="sync-btn"
            >
              {syncing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" strokeWidth={1.5} />
                  Sincronizando...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" strokeWidth={1.5} />
                  {supplier?.connection_type === "url" ? "Sincronizar URL" : "Sincronizar FTP"}
                </>
              )}
            </Button>
          )}
          <Button onClick={onUpload} className="btn-primary" data-testid="import-products-btn">
            <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Importar Archivo
          </Button>
        </div>
      </div>
    </div>
  );
}
