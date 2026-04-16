import { Globe, Loader2, Plus, Play, Pencil, Trash2, MoreHorizontal } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { CrawlStatusBadge } from "./CrawlStatusBadge";

const getChannelLabel = (channels, value) => {
  const ch = channels.find((c) => c.value === value);
  return ch ? ch.label : value;
};

const CHANNELS = [
  { value: "amazon_es", label: "Amazon España" },
  { value: "pccomponentes", label: "PCComponentes" },
  { value: "mediamarkt", label: "MediaMarkt" },
  { value: "fnac", label: "Fnac" },
  { value: "el_corte_ingles", label: "El Corte Inglés" },
  { value: "worten", label: "Worten" },
  { value: "coolmod", label: "Coolmod" },
  { value: "ldlc", label: "LDLC" },
  { value: "alternate", label: "Alternate" },
  { value: "web_directa", label: "Web Directa" },
  { value: "otro", label: "Otro" },
];

export function CompetitorsTab({ competitors, loading, onAdd, onEdit, onDelete, onCrawl }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (competitors.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No hay competidores configurados</p>
        <p className="text-sm">Añade un competidor para empezar a comparar precios</p>
        <Button className="mt-4" onClick={onAdd}>
          <Plus className="h-4 w-4 mr-2" />
          Añadir Competidor
        </Button>
      </div>
    );
  }

  return (
    <div className="border rounded-lg">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nombre</TableHead>
            <TableHead>Canal</TableHead>
            <TableHead>País</TableHead>
            <TableHead>Último Crawl</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Snapshots</TableHead>
            <TableHead className="w-[70px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {competitors.map((comp) => (
            <TableRow key={comp.id}>
              <TableCell>
                <div>
                  <span className="font-medium">{comp.name}</span>
                  <p className="text-xs text-muted-foreground truncate max-w-[250px]">{comp.base_url}</p>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline">{getChannelLabel(CHANNELS, comp.channel)}</Badge>
              </TableCell>
              <TableCell>{comp.country}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {comp.last_crawl_at ? new Date(comp.last_crawl_at).toLocaleString("es-ES") : "Nunca"}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <CrawlStatusBadge status={comp.last_crawl_status} />
                  {!comp.active && <Badge variant="secondary">Inactivo</Badge>}
                </div>
              </TableCell>
              <TableCell>{comp.total_snapshots}</TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onCrawl(comp.id)}>
                      <Play className="h-4 w-4 mr-2" />
                      Scrapear ahora
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit(comp)}>
                      <Pencil className="h-4 w-4 mr-2" />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive" onClick={() => onDelete(comp)}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Eliminar
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
