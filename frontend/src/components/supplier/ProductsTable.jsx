import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Checkbox } from "../ui/checkbox";
import { Badge } from "../ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import {
  Package,
  Eye,
  BookOpen,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Upload,
} from "lucide-react";

function getStockBadge(stock) {
  if (stock <= 0) return <span className="badge-error">Sin stock</span>;
  if (stock <= 5) return <span className="badge-warning">{stock} uds</span>;
  return <span className="badge-success">{stock} uds</span>;
}

export function ProductsTable({
  filteredProducts,
  totalProductsCount,
  selectedProducts,
  currentPage,
  totalProducts,
  totalPages,
  pageSize,
  onToggleSelection,
  onToggleSelectAll,
  onPageChange,
  onViewProduct,
  onAddToCatalog,
  onImport,
}) {
  if (filteredProducts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <Package className="w-10 h-10" strokeWidth={1.5} />
        </div>
        <h3
          className="text-lg font-semibold text-slate-900 mb-2"
          style={{ fontFamily: "Manrope, sans-serif" }}
        >
          {totalProductsCount === 0 ? "No hay productos" : "No se encontraron productos"}
        </h3>
        <p className="text-slate-500 mb-4">
          {totalProductsCount === 0
            ? "Importa productos de este proveedor para comenzar"
            : "Prueba con otros filtros de búsqueda"}
        </p>
        {totalProductsCount === 0 && (
          <Button onClick={onImport} className="btn-primary" data-testid="empty-import-btn">
            <Upload className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Importar Productos
          </Button>
        )}
      </div>
    );
  }

  return (
    <Card className="border-slate-200">
      <CardContent className="p-0 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="table-header">
              <TableHead className="w-[50px]">
                <Checkbox
                  checked={
                    selectedProducts.size === filteredProducts.length &&
                    filteredProducts.length > 0
                  }
                  onCheckedChange={onToggleSelectAll}
                  data-testid="select-all-checkbox"
                />
              </TableHead>
              <TableHead>Producto</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Categoría</TableHead>
              <TableHead className="text-right">Precio</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-center">En Productos</TableHead>
              <TableHead className="w-[100px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredProducts.map((product) => (
              <TableRow
                key={product.id}
                className={`table-row ${selectedProducts.has(product.id) ? "bg-indigo-50" : ""}`}
                data-testid={`product-row-${product.id}`}
              >
                <TableCell>
                  <Checkbox
                    checked={selectedProducts.has(product.id)}
                    onCheckedChange={() => onToggleSelection(product.id)}
                    data-testid={`select-product-${product.id}`}
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-3 max-w-[300px]">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-10 h-10 object-cover rounded-sm border border-slate-200"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-slate-100 rounded-sm flex items-center justify-center">
                        <Package className="w-5 h-5 text-slate-400" strokeWidth={1.5} />
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 truncate">{product.name}</p>
                      {product.brand && (
                        <p className="text-xs text-slate-500">{product.brand}</p>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-sm text-slate-600">{product.sku}</span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-slate-600">{product.category || "-"}</span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="font-mono font-semibold text-slate-900">
                    {product.price.toLocaleString("es-ES", {
                      style: "currency",
                      currency: "EUR",
                    })}
                  </span>
                </TableCell>
                <TableCell className="text-right">{getStockBadge(product.stock)}</TableCell>
                <TableCell className="text-center">
                  {product.is_selected ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Sí
                    </Badge>
                  ) : (
                    <Badge className="bg-slate-100 text-slate-500 border-0">
                      <XCircle className="w-3 h-3 mr-1" />
                      No
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewProduct(product)}
                      className="h-8 w-8 p-0"
                      data-testid={`view-product-${product.id}`}
                    >
                      <Eye className="w-4 h-4" strokeWidth={1.5} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onAddToCatalog(product.id)}
                      className="h-8 w-8 p-0 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                      data-testid={`add-to-catalog-${product.id}`}
                    >
                      <BookOpen className="w-4 h-4" strokeWidth={1.5} />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      {totalPages > 1 && (
        <div
          className="flex items-center justify-between px-4 py-3 border-t border-slate-200"
          data-testid="pagination"
        >
          <p className="text-sm text-slate-500">
            Mostrando {(currentPage - 1) * pageSize + 1} -{" "}
            {Math.min(currentPage * pageSize, totalProducts)} de{" "}
            {totalProducts.toLocaleString()} productos
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              data-testid="prev-page"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-slate-600 px-2">
              Página {currentPage} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              data-testid="next-page"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
