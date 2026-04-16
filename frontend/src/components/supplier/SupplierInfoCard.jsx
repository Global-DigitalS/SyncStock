import { FileText, Globe, Server } from "lucide-react";
import { Card, CardContent } from "../ui/card";

export function SupplierInfoCard({ supplier, totalProducts, productsLength, formatDate }) {
  return (
    <Card className="border-slate-200 mb-6">
      <CardContent className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-slate-500">Formato de archivo</p>
            <div className="flex items-center gap-1.5 mt-1">
              <FileText className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
              <span className="font-medium uppercase text-sm">{supplier?.file_format || "CSV"}</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-500">Tipo de conexión</p>
            <div className="flex items-center gap-1.5 mt-1">
              {supplier?.connection_type === "url" ? (
                <>
                  <Globe className={`w-4 h-4 ${supplier?.file_url ? "text-emerald-500" : "text-slate-300"}`} strokeWidth={1.5} />
                  <span className="text-sm">URL Directa</span>
                </>
              ) : (
                <>
                  <Server className={`w-4 h-4 ${supplier?.ftp_host ? "text-emerald-500" : "text-slate-300"}`} strokeWidth={1.5} />
                  <span className="text-sm font-mono">{supplier?.ftp_host || "No configurado"}</span>
                </>
              )}
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-500">Productos</p>
            <p className="font-mono text-xl font-semibold text-slate-900">
              {totalProducts > 0 ? totalProducts.toLocaleString() : productsLength.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Última sincronización</p>
            <p className="text-sm text-slate-700">{formatDate(supplier?.last_sync)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
