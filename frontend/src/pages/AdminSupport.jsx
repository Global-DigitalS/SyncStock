import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  TicketCheck, ArrowLeft, Send, Clock, CheckCircle2, MessageSquare,
  AlertCircle, HelpCircle, CreditCard, Lightbulb, ChevronRight,
  User, Shield, Inbox, Star, RefreshCw, Filter, Search, Eye,
  MailOpen, Reply, XCircle, LifeBuoy
} from "lucide-react";
import { useAuth, api } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Input } from "../components/ui/input";

// ==================== CONSTANTS ====================

const STATUS_CONFIG = {
  received: { label: "Recibido", color: "bg-blue-100 text-blue-700", icon: Inbox },
  reviewing: { label: "Revisando", color: "bg-amber-100 text-amber-700", icon: Eye },
  replied: { label: "Respondido", color: "bg-indigo-100 text-indigo-700", icon: Reply },
  resolved: { label: "Resuelto", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
  closed: { label: "Cerrado", color: "bg-slate-100 text-slate-600", icon: XCircle },
};

const PRIORITY_CONFIG = {
  urgent: { label: "Urgente", color: "bg-red-100 text-red-700", dot: "bg-red-500" },
  normal: { label: "Normal", color: "bg-blue-100 text-blue-700", dot: "bg-blue-500" },
  low: { label: "Baja", color: "bg-slate-100 text-slate-600", dot: "bg-slate-400" },
};

const TYPE_LABELS = {
  technical: "Problema técnico",
  usage: "Consulta de uso",
  billing: "Facturación",
  feedback: "Sugerencia",
  other: "Otro",
};

const TYPE_ICONS = {
  technical: AlertCircle,
  usage: HelpCircle,
  billing: CreditCard,
  feedback: Lightbulb,
  other: MessageSquare,
};

// ==================== STAT CARD ====================

const StatCard = ({ icon: Icon, value, label, color, bg }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${bg}`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <div>
          <p className="text-2xl font-bold text-slate-900">{value}</p>
          <p className="text-xs text-slate-500">{label}</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// ==================== TICKET DETAIL ====================

const AdminTicketDetail = ({ ticket, onBack, onUpdate }) => {
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [changingStatus, setChangingStatus] = useState(false);

  const handleSendReply = async () => {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const res = await api.post(`/support/admin/tickets/${ticket.id}/messages`, {
        content: reply.trim(),
      });
      toast.success("Respuesta enviada");
      setReply("");
      onUpdate(res.data);
    } catch {
      toast.error("Error al enviar respuesta");
    } finally {
      setSending(false);
    }
  };

  const handleChangeStatus = async (newStatus) => {
    setChangingStatus(true);
    try {
      const res = await api.put(`/support/admin/tickets/${ticket.id}`, {
        status: newStatus,
      });
      toast.success(`Estado cambiado a "${STATUS_CONFIG[newStatus]?.label}"`);
      onUpdate(res.data);
    } catch {
      toast.error("Error al cambiar estado");
    } finally {
      setChangingStatus(false);
    }
  };

  const statusCfg = STATUS_CONFIG[ticket.status] || {};
  const priorityCfg = PRIORITY_CONFIG[ticket.priority] || {};
  const TypeIcon = TYPE_ICONS[ticket.type] || MessageSquare;

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a tickets
        </button>
        <Badge variant="outline" className={statusCfg.color}>
          {statusCfg.label}
        </Badge>
      </div>

      {/* Ticket info card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-slate-400">#{ticket.ticket_number}</span>
                <Badge variant="outline" className={priorityCfg.color}>
                  {priorityCfg.label}
                </Badge>
                <Badge variant="outline" className="text-slate-600">
                  <TypeIcon className="w-3 h-3 mr-1" />
                  {TYPE_LABELS[ticket.type] || ticket.type}
                </Badge>
              </div>
              <CardTitle className="text-lg">{ticket.subject}</CardTitle>
            </div>
            {ticket.rating && (
              <div className="flex items-center gap-1 text-amber-500">
                <Star className="w-4 h-4 fill-current" />
                <span className="text-sm font-medium">{ticket.rating}/5</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="border-t pt-4">
          {/* User info */}
          <div className="flex items-center gap-3 mb-4 p-3 bg-slate-50 rounded-lg">
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-slate-500" />
            </div>
            <div className="text-sm">
              <p className="font-medium text-slate-800">{ticket.user_name || "Usuario"}</p>
              <p className="text-slate-500">{ticket.user_email || "—"}</p>
            </div>
            <div className="ml-auto text-right text-xs text-slate-400">
              <p>Creado: {new Date(ticket.created_at).toLocaleString("es-ES")}</p>
              {ticket.updated_at && (
                <p>Actualizado: {new Date(ticket.updated_at).toLocaleString("es-ES")}</p>
              )}
            </div>
          </div>

          {/* Change status */}
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-500 mb-2">Cambiar estado</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(STATUS_CONFIG).map(([key, cfg]) => {
                const StatusIcon = cfg.icon;
                return (
                  <Button
                    key={key}
                    size="sm"
                    variant={ticket.status === key ? "default" : "outline"}
                    className={ticket.status === key ? "btn-primary" : ""}
                    disabled={ticket.status === key || changingStatus}
                    onClick={() => handleChangeStatus(key)}
                  >
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {cfg.label}
                  </Button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Messages thread */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Conversación ({ticket.messages?.length || 0})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {ticket.messages?.map((msg) => {
            const isSupport = msg.author_role === "support";
            return (
              <div
                key={msg.id}
                className={`p-4 rounded-lg border ${
                  isSupport
                    ? "bg-indigo-50 border-indigo-200 ml-6"
                    : "bg-white border-slate-200 mr-6"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      isSupport ? "bg-indigo-200" : "bg-slate-200"
                    }`}
                  >
                    {isSupport ? (
                      <Shield className="w-3 h-3 text-indigo-600" />
                    ) : (
                      <User className="w-3 h-3 text-slate-500" />
                    )}
                  </div>
                  <span className="text-sm font-medium text-slate-700">{msg.author}</span>
                  <span className="text-xs text-slate-400 ml-auto">
                    {new Date(msg.created_at).toLocaleString("es-ES")}
                  </span>
                </div>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">{msg.content}</p>
              </div>
            );
          })}

          {/* Reply box */}
          <div className="pt-4 border-t border-slate-100 space-y-3">
            <Textarea
              placeholder="Escribe tu respuesta al usuario..."
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              rows={3}
              className="resize-none"
            />
            <div className="flex justify-end">
              <Button
                className="btn-primary"
                disabled={!reply.trim() || sending}
                onClick={handleSendReply}
              >
                {sending ? (
                  <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Enviar respuesta
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== MAIN PAGE ====================

const AdminSupport = () => {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.append("status", filterStatus);
      if (filterType) params.append("type", filterType);
      if (filterPriority) params.append("priority", filterPriority);

      const [ticketsRes, statsRes] = await Promise.all([
        api.get(`/support/admin/tickets?${params.toString()}`),
        api.get("/support/admin/stats"),
      ]);
      setTickets(ticketsRes.data);
      setStats(statsRes.data);
    } catch {
      toast.error("Error al cargar tickets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role !== "superadmin") return;
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStatus, filterType, filterPriority, user]);

  const handleUpdateTicket = (updated) => {
    setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    setSelectedTicket(updated);
  };

  const handleSelectTicket = async (ticket) => {
    try {
      const res = await api.get(`/support/admin/tickets/${ticket.id}`);
      setSelectedTicket(res.data);
    } catch {
      toast.error("Error al cargar detalle del ticket");
    }
  };

  // Guard
  if (user?.role !== "superadmin") {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-slate-500">Acceso restringido a superadministradores</p>
      </div>
    );
  }

  // Ticket detail view
  if (selectedTicket) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
            Gestión de Soporte
          </h1>
          <p className="text-slate-500 mt-1 text-sm">Detalle del ticket</p>
        </div>
        <AdminTicketDetail
          ticket={selectedTicket}
          onBack={() => setSelectedTicket(null)}
          onUpdate={handleUpdateTicket}
        />
      </div>
    );
  }

  // Filter tickets by search
  const filteredTickets = searchTerm
    ? tickets.filter(
        (t) =>
          t.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          t.ticket_number?.toString().includes(searchTerm) ||
          t.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          t.user_email?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : tickets;

  // Split by open/closed
  const openStatuses = ["received", "reviewing", "replied"];
  const openTickets = filteredTickets.filter((t) => openStatuses.includes(t.status));
  const closedTickets = filteredTickets.filter((t) => !openStatuses.includes(t.status));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
            Gestión de Soporte
          </h1>
          <p className="text-slate-500 mt-1">Visualiza y responde los tickets de los usuarios</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            icon={TicketCheck}
            value={stats.total}
            label="Total tickets"
            color="text-indigo-600"
            bg="bg-indigo-50"
          />
          <StatCard
            icon={Inbox}
            value={stats.by_status?.received || 0}
            label="Recibidos"
            color="text-blue-600"
            bg="bg-blue-50"
          />
          <StatCard
            icon={Eye}
            value={stats.by_status?.reviewing || 0}
            label="Revisando"
            color="text-amber-600"
            bg="bg-amber-50"
          />
          <StatCard
            icon={Reply}
            value={stats.by_status?.replied || 0}
            label="Respondidos"
            color="text-indigo-600"
            bg="bg-indigo-50"
          />
          <StatCard
            icon={CheckCircle2}
            value={(stats.by_status?.resolved || 0) + (stats.by_status?.closed || 0)}
            label="Cerrados"
            color="text-emerald-600"
            bg="bg-emerald-50"
          />
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Filter className="w-4 h-4" />
              Filtros:
            </div>

            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar por asunto, nº, usuario..."
                className="pl-9 h-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <select
              className="h-9 px-3 rounded-md border border-slate-200 text-sm bg-white"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="">Todos los estados</option>
              {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
                <option key={key} value={key}>{cfg.label}</option>
              ))}
            </select>

            <select
              className="h-9 px-3 rounded-md border border-slate-200 text-sm bg-white"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="">Todos los tipos</option>
              {Object.entries(TYPE_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>

            <select
              className="h-9 px-3 rounded-md border border-slate-200 text-sm bg-white"
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
            >
              <option value="">Todas las prioridades</option>
              {Object.entries(PRIORITY_CONFIG).map(([key, cfg]) => (
                <option key={key} value={key}>{cfg.label}</option>
              ))}
            </select>

            {(filterStatus || filterType || filterPriority || searchTerm) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setFilterStatus("");
                  setFilterType("");
                  setFilterPriority("");
                  setSearchTerm("");
                }}
              >
                Limpiar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Ticket list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
        </div>
      ) : (
        <Tabs defaultValue="open">
          <TabsList className="grid w-full grid-cols-2 lg:w-[300px]">
            <TabsTrigger value="open">
              <Inbox className="w-4 h-4 mr-2" />
              Abiertos ({openTickets.length})
            </TabsTrigger>
            <TabsTrigger value="closed">
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Cerrados ({closedTickets.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="open" className="mt-4">
            <TicketTable tickets={openTickets} onSelect={handleSelectTicket} />
          </TabsContent>
          <TabsContent value="closed" className="mt-4">
            <TicketTable tickets={closedTickets} onSelect={handleSelectTicket} />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

// ==================== TICKET TABLE ====================

const TicketTable = ({ tickets, onSelect }) => {
  if (!tickets.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <TicketCheck className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-slate-700 font-medium">Sin tickets</h3>
        <p className="text-slate-400 text-sm mt-1">No hay tickets en esta categoría</p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th className="text-left px-4 py-3 font-medium text-slate-500">Ticket</th>
            <th className="text-left px-4 py-3 font-medium text-slate-500 hidden md:table-cell">Usuario</th>
            <th className="text-left px-4 py-3 font-medium text-slate-500 hidden sm:table-cell">Tipo</th>
            <th className="text-left px-4 py-3 font-medium text-slate-500">Estado</th>
            <th className="text-left px-4 py-3 font-medium text-slate-500 hidden sm:table-cell">Prioridad</th>
            <th className="text-left px-4 py-3 font-medium text-slate-500 hidden lg:table-cell">Fecha</th>
            <th className="px-4 py-3 w-8"></th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => {
            const statusCfg = STATUS_CONFIG[ticket.status] || {};
            const priorityCfg = PRIORITY_CONFIG[ticket.priority] || {};
            return (
              <tr
                key={ticket.id}
                onClick={() => onSelect(ticket)}
                className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <div>
                    <span className="text-xs font-mono text-slate-400 block">#{ticket.ticket_number}</span>
                    <p className="font-medium text-slate-800 truncate max-w-[250px]">{ticket.subject}</p>
                  </div>
                </td>
                <td className="px-4 py-3 hidden md:table-cell">
                  <div>
                    <p className="text-slate-700 truncate max-w-[150px]">{ticket.user_name || "—"}</p>
                    <p className="text-xs text-slate-400 truncate max-w-[150px]">{ticket.user_email || ""}</p>
                  </div>
                </td>
                <td className="px-4 py-3 hidden sm:table-cell">
                  <span className="text-slate-600 text-xs">{TYPE_LABELS[ticket.type] || ticket.type}</span>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="outline" className={`text-xs ${statusCfg.color}`}>
                    {statusCfg.label}
                  </Badge>
                </td>
                <td className="px-4 py-3 hidden sm:table-cell">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${priorityCfg.dot}`} />
                    <span className="text-xs text-slate-600">{priorityCfg.label}</span>
                  </div>
                </td>
                <td className="px-4 py-3 hidden lg:table-cell text-xs text-slate-400">
                  {new Date(ticket.created_at).toLocaleDateString("es-ES", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  })}
                </td>
                <td className="px-4 py-3">
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default AdminSupport;
