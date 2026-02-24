import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { 
  Truck, RefreshCw, Settings, Trash2, Package, 
  Globe, Server, CheckCircle, XCircle, AlertCircle, Clock
} from "lucide-react";

const SyncStatusBadge = ({ supplier }) => {
  const lastSync = supplier.last_sync ? new Date(supplier.last_sync) : null;
  const isRecent = lastSync && (Date.now() - lastSync.getTime()) < 24 * 60 * 60 * 1000;

  if (!lastSync) {
    return (
      <Badge className="bg-slate-100 text-slate-600">
        <Clock className="w-3 h-3 mr-1" />
        Sin sincronizar
      </Badge>
    );
  }

  if (isRecent) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700">
        <CheckCircle className="w-3 h-3 mr-1" />
        Actualizado
      </Badge>
    );
  }

  return (
    <Badge className="bg-amber-100 text-amber-700">
      <AlertCircle className="w-3 h-3 mr-1" />
      Desactualizado
    </Badge>
  );
};

const SupplierCard = ({
  supplier,
  onSync,
  onEdit,
  onDelete,
  onOpenMapping,
  syncing
}) => {
  const isUrl = supplier.connection_type === "url";
  const productCount = supplier.product_count || 0;

  return (
    <Card 
      className="border-slate-200 hover:border-indigo-200 transition-all duration-200 hover:shadow-md"
      data-testid={`supplier-card-${supplier.id}`}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isUrl ? "bg-blue-100" : "bg-indigo-100"
            }`}>
              {isUrl ? (
                <Globe className="w-6 h-6 text-blue-600" />
              ) : (
                <Server className="w-6 h-6 text-indigo-600" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {supplier.name}
              </h3>
              <p className="text-sm text-slate-500">
                {isUrl ? "Conexión URL" : `FTP: ${supplier.ftp_host}`}
              </p>
            </div>
          </div>
          <SyncStatusBadge supplier={supplier} />
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Package className="w-4 h-4" />
              <span className="text-xs">Productos</span>
            </div>
            <p className="text-lg font-semibold text-slate-900">{productCount.toLocaleString()}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-xs">Última sync</span>
            </div>
            <p className="text-sm font-medium text-slate-900">
              {supplier.last_sync 
                ? new Date(supplier.last_sync).toLocaleDateString("es-ES", { day: "2-digit", month: "short" })
                : "Nunca"
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onSync(supplier)}
            disabled={syncing === supplier.id}
            data-testid={`sync-supplier-${supplier.id}`}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${syncing === supplier.id ? "animate-spin" : ""}`} />
            {syncing === supplier.id ? "Sincronizando..." : "Sincronizar"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenMapping(supplier)}
            data-testid={`mapping-supplier-${supplier.id}`}
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(supplier)}
            data-testid={`edit-supplier-${supplier.id}`}
          >
            <Truck className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-rose-500 hover:text-rose-700 hover:bg-rose-50"
            onClick={() => onDelete(supplier)}
            data-testid={`delete-supplier-${supplier.id}`}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SupplierCard;
