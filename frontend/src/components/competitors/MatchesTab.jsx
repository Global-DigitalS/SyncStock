import { ShieldCheck, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";

export function MatchesTab({ pendingMatches, pendingTotal, onReview }) {
  if (pendingMatches.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <ShieldCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No hay matches pendientes</p>
        <p className="text-sm">Los matches de baja confianza aparecerán aquí para tu revisión</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">{pendingTotal} matches pendientes de revisión</p>
      {pendingMatches.map((match) => (
        <div key={match.id} className="border rounded-lg p-4 flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-sm truncate">{match.product_name || match.sku}</span>
              <Badge variant="outline" className="text-xs">
                Score: {(match.match_score * 100).toFixed(0)}%
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground truncate">Candidato: {match.candidate_name}</p>
            {match.candidate_url && (
              <a
                href={match.candidate_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:underline truncate block"
              >
                {match.candidate_url}
              </a>
            )}
          </div>
          <div className="flex gap-2 shrink-0">
            <Button size="sm" variant="outline" className="text-green-600" onClick={() => onReview(match.id, "confirm")}>
              <CheckCircle2 className="h-4 w-4 mr-1" />
              Confirmar
            </Button>
            <Button size="sm" variant="outline" className="text-red-600" onClick={() => onReview(match.id, "reject")}>
              <XCircle className="h-4 w-4 mr-1" />
              Rechazar
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
