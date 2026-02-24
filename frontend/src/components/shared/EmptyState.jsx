import { Package, FileUp, AlertCircle } from "lucide-react";

const EmptyState = ({
  icon: Icon = Package,
  title,
  description,
  action,
  className
}) => {
  return (
    <div className={`empty-state ${className || ""}`}>
      <Icon className="w-16 h-16 text-slate-300 mb-4" />
      <h3 className="text-xl font-semibold text-slate-900 mb-2">{title}</h3>
      {description && <p className="text-slate-500 mb-4">{description}</p>}
      {action}
    </div>
  );
};

export default EmptyState;
