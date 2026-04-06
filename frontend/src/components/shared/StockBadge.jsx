import { AlertTriangle, Package, Check } from "lucide-react";
import { Badge } from "../ui/badge";

const StockBadge = ({ stock, className }) => {
  if (stock <= 0) {
    return (
      <Badge className={`bg-rose-100 text-rose-700 ${className || ""}`}>
        <AlertTriangle className="w-3 h-3 mr-1" />
        Sin stock
      </Badge>
    );
  }
  
  if (stock <= 5) {
    return (
      <Badge className={`bg-amber-100 text-amber-700 ${className || ""}`}>
        <AlertTriangle className="w-3 h-3 mr-1" />
        {stock} uds
      </Badge>
    );
  }
  
  return (
    <Badge className={`bg-emerald-100 text-emerald-700 ${className || ""}`}>
      <Check className="w-3 h-3 mr-1" />
      {stock} uds
    </Badge>
  );
};

export default StockBadge;
