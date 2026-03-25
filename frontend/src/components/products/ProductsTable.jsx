import { Checkbox } from "../ui/checkbox";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";
import { Eye, BookOpen, Star, AlertTriangle, Check, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";

const SortableHeader = ({ column, label, currentSort, sortOrder, onSort }) => {
  const isActive = currentSort === column;
  return (
    <button
      onClick={() => onSort(column)}
      className={`flex items-center gap-1 hover:text-indigo-600 transition-colors font-medium ${isActive ? "text-indigo-600" : ""}`}
      data-testid={`sort-${column}`}
    >
      {label}
      {isActive ? (
        sortOrder === "asc" ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
      ) : (
        <ArrowUpDown className="w-3 h-3 opacity-40" />
      )}
    </button>
  );
};

const StockBadge = ({ stock }) => {
  if (stock <= 0) {
    return (
      <Badge className="bg-rose-100 text-rose-700">
        <AlertTriangle className="w-3 h-3 mr-1" />Sin stock
      </Badge>
    );
  }
  if (stock <= 5) {
    return (
      <Badge className="bg-amber-100 text-amber-700">
        <AlertTriangle className="w-3 h-3 mr-1" />{stock} uds
      </Badge>
    );
  }
  return (
    <Badge className="bg-emerald-100 text-emerald-700">
      <Check className="w-3 h-3 mr-1" />{stock} uds
    </Badge>
  );
};

const COMPLETION_FIELDS = [
  { key: "name", label: "Nombre" },
  { key: "ean", label: "EAN" },
  { key: "description", label: "Descripción" },
  { key: "short_description", label: "Descripción corta" },
  { key: "long_description", label: "Descripción larga" },
  { key: "category", label: "Categoría" },
  { key: "brand", label: "Marca" },
  { key: "image_url", label: "Imagen" },
  { key: "weight", label: "Peso" },
  { key: "best_price", label: "Precio", check: (v) => v != null && v > 0 },
  { key: "total_stock", label: "Stock", check: (v) => v != null && v > 0 },
];

const getProductCompletion = (product) => {
  const results = COMPLETION_FIELDS.map((field) => {
    const value = product[field.key];
    const filled = field.check
      ? field.check(value)
      : value != null && value !== "" && value !== 0;
    return { ...field, filled };
  });
  const filledCount = results.filter((r) => r.filled).length;
  const percentage = Math.round((filledCount / results.length) * 100);
  return { percentage, results };
};

const getCompletionColor = (pct) => {
  if (pct >= 80) return { bar: "bg-emerald-500", text: "text-emerald-700" };
  if (pct >= 50) return { bar: "bg-amber-500", text: "text-amber-700" };
  return { bar: "bg-rose-500", text: "text-rose-700" };
};

const ProductCompletionBar = ({ product }) => {
  const { percentage, results } = getProductCompletion(product);
  const colors = getCompletionColor(percentage);
  const missing = results.filter((r) => !r.filled);

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2 min-w-[100px] cursor-default">
            <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${colors.bar}`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className={`text-xs font-semibold ${colors.text} w-8 text-right`}>
              {percentage}%
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[220px]">
          <p className="font-semibold text-xs mb-1">
            Completado: {percentage}%
          </p>
          {missing.length > 0 ? (
            <div className="text-xs">
              <p className="text-slate-400 mb-0.5">Campos vacíos:</p>
              <ul className="list-disc pl-3 space-y-0">
                {missing.map((f) => (
                  <li key={f.key}>{f.label}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-xs text-emerald-400">Todos los campos completos</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const ProductsTable = ({
  products,
  selectedProducts,
  onSelectAll,
  onSelectProduct,
  onOpenDetail,
  onAddToCatalog,
  sortBy,
  sortOrder,
  onSort
}) => {
  const allSelected = products.length > 0 && selectedProducts.size === products.length;

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50">
            <TableHead className="w-12">
              <Checkbox
                checked={allSelected}
                onCheckedChange={onSelectAll}
                data-testid="select-all-products"
              />
            </TableHead>
            <TableHead>
              <SortableHeader column="name" label="Producto" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
            </TableHead>
            <TableHead>
              <SortableHeader column="ean" label="EAN" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
            </TableHead>
            <TableHead>
              <SortableHeader column="best_price" label="Mejor Precio" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
            </TableHead>
            <TableHead>
              <SortableHeader column="total_stock" label="Stock Total" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
            </TableHead>
            <TableHead>
              <SortableHeader column="supplier_count" label="Proveedores" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
            </TableHead>
            <TableHead className="w-[130px]">Completado</TableHead>
            <TableHead className="w-28">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {products.map((product) => {
            const isSelected = selectedProducts.has(product.ean);
            const bestOffer = product.suppliers.find(s => s.is_best_offer);

            return (
              <TableRow
                key={product.ean}
                className={`hover:bg-slate-50 transition-colors ${isSelected ? "bg-indigo-50" : ""}`}
                data-testid={`product-row-${product.ean}`}
              >
                <TableCell>
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={(checked) => onSelectProduct(product.ean, checked)}
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
                      {product.image_url ? (
                        <img src={product.image_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-slate-400 text-xs">IMG</span>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 truncate max-w-xs" title={product.name}>
                        {product.name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {product.brand && (
                          <span className="text-xs text-slate-500">{product.brand}</span>
                        )}
                        {bestOffer && (
                          <Badge className="bg-emerald-100 text-emerald-700 text-xs">
                            <Star className="w-3 h-3 mr-1 fill-emerald-500" />
                            {bestOffer.supplier_name}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-sm text-slate-600">{product.ean}</span>
                </TableCell>
                <TableCell>
                  <span className="font-semibold text-slate-900">€{product.best_price.toFixed(2)}</span>
                </TableCell>
                <TableCell>
                  <StockBadge stock={product.total_stock} />
                </TableCell>
                <TableCell>
                  <Badge className="bg-slate-100 text-slate-600">
                    {product.supplier_count}
                  </Badge>
                </TableCell>
                <TableCell>
                  <ProductCompletionBar product={product} />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => onOpenDetail(product)}
                      data-testid={`view-product-${product.ean}`}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => onAddToCatalog([product.ean])}
                      data-testid={`add-to-catalog-${product.ean}`}
                    >
                      <BookOpen className="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

export default ProductsTable;
