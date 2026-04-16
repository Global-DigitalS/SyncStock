import { Clock } from "lucide-react";
import { Card, CardContent } from "../ui/card";

export function SyncStatusBanner({ syncStatus, supplier, formatDate }) {
  if (!syncStatus?.ftp_configured) return null;

  return (
    <Card className="border-emerald-200 bg-emerald-50 mb-6">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-emerald-600" strokeWidth={1.5} />
            <div>
              <p className="font-medium text-emerald-900">Sincronización automática activa</p>
              <p className="text-sm text-emerald-700">
                Próxima sincronización:{" "}
                {syncStatus.next_scheduled_sync
                  ? new Date(syncStatus.next_scheduled_sync).toLocaleString("es-ES")
                  : "Programada cada 12 horas"}
              </p>
            </div>
          </div>
          {supplier?.last_sync && (
            <div className="text-right">
              <p className="text-xs text-emerald-600">Última sincronización</p>
              <p className="text-sm font-medium text-emerald-900">{formatDate(supplier.last_sync)}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
