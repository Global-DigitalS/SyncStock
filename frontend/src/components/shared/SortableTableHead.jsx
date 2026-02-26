/**
 * Componente reutilizable para encabezados de tabla ordenables.
 * Muestra el icono de ordenación apropiado según el estado.
 */
import { TableHead } from "../ui/table";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

const SortableTableHead = ({
  column,
  label,
  sortBy,
  sortOrder,
  onSort,
  className = "",
  align = "left",
}) => {
  const isActive = sortBy === column;
  
  const handleClick = () => {
    onSort(column);
  };

  const alignClass = align === "right" ? "ml-auto" : align === "center" ? "mx-auto" : "";

  return (
    <TableHead className={className}>
      <button
        onClick={handleClick}
        className={`flex items-center gap-1 hover:text-indigo-600 transition-colors ${alignClass}`}
        data-testid={`sort-${column}`}
      >
        {label}
        {isActive ? (
          sortOrder === "asc" ? (
            <ArrowUp className="w-4 h-4" />
          ) : (
            <ArrowDown className="w-4 h-4" />
          )
        ) : (
          <ArrowUpDown className="w-4 h-4 opacity-40" />
        )}
      </button>
    </TableHead>
  );
};

export default SortableTableHead;
