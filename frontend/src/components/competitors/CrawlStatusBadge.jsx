import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "../ui/badge";

export function CrawlStatusBadge({ status }) {
  if (!status) return <Badge variant="outline">Sin datos</Badge>;
  const map = {
    success: { label: "OK", variant: "default", icon: CheckCircle2 },
    partial: { label: "Parcial", variant: "secondary", icon: AlertTriangle },
    error: { label: "Error", variant: "destructive", icon: XCircle },
  };
  const info = map[status] || map.error;
  const Icon = info.icon;
  return (
    <Badge variant={info.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {info.label}
    </Badge>
  );
}
