import { ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";
import { cn } from "../../lib/utils";

const SortableHeader = ({
  column,
  label,
  currentSort,
  sortOrder,
  onSort,
  className
}) => {
  const isActive = currentSort === column;
  
  const handleClick = () => {
    if (isActive) {
      onSort(column, sortOrder === "asc" ? "desc" : "asc");
    } else {
      onSort(column, "asc");
    }
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "flex items-center gap-1 hover:text-indigo-600 transition-colors font-medium",
        isActive && "text-indigo-600",
        className
      )}
      data-testid={`sort-${column}`}
    >
      {label}
      {isActive ? (
        sortOrder === "asc" ? (
          <ArrowUp className="w-3 h-3" />
        ) : (
          <ArrowDown className="w-3 h-3" />
        )
      ) : (
        <ArrowUpDown className="w-3 h-3 opacity-40" />
      )}
    </button>
  );
};

export default SortableHeader;
