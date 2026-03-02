import { useNavigate } from "react-router-dom";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import {
  Truck,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Server,
  FileText,
  Eye,
  Globe,
  Columns
} from "lucide-react";

const formatDate = (dateStr) => {
  if (!dateStr) return "Nunca";
  return new Date(dateStr).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const SupplierTable = ({ suppliers, onEdit, onMapping, onDelete, onCreate }) => {
  const navigate = useNavigate();

  if (suppliers.length === 0) {
    return (
      <div className="empty-state" data-testid="empty-suppliers">
        <div className="empty-state-icon">
          <Truck className="w-10 h-10" strokeWidth={1.5} />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          No hay proveedores
        </h3>
        <p className="text-slate-500 mb-4">
          Añade tu primer proveedor para comenzar a importar productos
        </p>
        <Button onClick={onCreate} className="btn-primary" data-testid="empty-add-supplier">
          <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
          Añadir Proveedor
        </Button>
      </div>
    );
  }

  return (
    <Card className="border-slate-200" data-testid="suppliers-table">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="table-header">
              <TableHead>Proveedor</TableHead>
              <TableHead>Formato</TableHead>
              <TableHead>Conexión</TableHead>
              <TableHead></TableHead>
              <TableHead className="text-right">Productos</TableHead>
              <TableHead>Última Sincronización</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {suppliers.map((supplier) => (
              <TableRow 
                key={supplier.id} 
                className="table-row" 
                data-testid={`supplier-row-${supplier.id}`}
              >
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-100 rounded-sm flex items-center justify-center">
                      <Truck className="w-5 h-5 text-slate-600" strokeWidth={1.5} />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{supplier.name}</p>
                      {supplier.description && (
                        <p className="text-sm text-slate-500 truncate max-w-[200px]">
                          {supplier.description}
                        </p>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="inline-flex items-center gap-1.5 px-2 py-1 bg-slate-100 rounded-sm text-xs font-medium text-slate-700 uppercase">
                    <FileText className="w-3.5 h-3.5" strokeWidth={1.5} />
                    {supplier.file_format || "CSV"}
                  </span>
                </TableCell>
                <TableCell>
                  {supplier.connection_type === "url" && supplier.file_url ? (
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-emerald-500" strokeWidth={1.5} />
                      <span className="text-sm text-slate-600 truncate max-w-[200px]" title={supplier.file_url}>
                        URL Directa
                      </span>
                    </div>
                  ) : supplier.ftp_host ? (
                    <div className="flex items-center gap-2">
                      <Server className="w-4 h-4 text-emerald-500" strokeWidth={1.5} />
                      <span className="text-sm text-slate-600 font-mono">
                        {supplier.ftp_schema?.toUpperCase() || "FTP"}://{supplier.ftp_host}:{supplier.ftp_port || 21}
                      </span>
                      {supplier.ftp_paths?.length > 0 && (
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full font-medium">
                          {supplier.ftp_paths.length} archivos
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-sm text-slate-400">No configurado</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/suppliers/${supplier.id}`)}
                    className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 font-medium"
                    data-testid={`view-catalog-${supplier.id}`}
                  >
                    <Eye className="w-4 h-4 mr-1.5" strokeWidth={1.5} />
                    Ver catálogo
                  </Button>
                </TableCell>
                <TableCell className="text-right">
                  <span className="font-mono text-slate-900">
                    {supplier.product_count.toLocaleString()}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-slate-500">
                    {formatDate(supplier.last_sync)}
                  </span>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0" 
                        data-testid={`supplier-menu-${supplier.id}`}
                      >
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem 
                        onClick={() => onEdit(supplier)} 
                        data-testid={`edit-supplier-${supplier.id}`}
                      >
                        <Pencil className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onMapping(supplier)} 
                        data-testid={`mapping-supplier-${supplier.id}`}
                      >
                        <Columns className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Mapear Columnas
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDelete(supplier)}
                        className="text-rose-600 focus:text-rose-600"
                        data-testid={`delete-supplier-${supplier.id}`}
                      >
                        <Trash2 className="w-4 h-4 mr-2" strokeWidth={1.5} />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default SupplierTable;
