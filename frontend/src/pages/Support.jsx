import { useState, useEffect } from "react";
import { useAuth, api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Textarea } from "../components/ui/textarea";
import {
  TicketCheck, Plus, ArrowLeft, Send, Clock, CheckCircle2, MessageSquare,
  AlertCircle, HelpCircle, CreditCard, Lightbulb, Paperclip, Star,
  RefreshCw, ChevronRight, User, Shield, RotateCcw, Inbox
} from "lucide-react";

// ==================== CONSTANTS ====================

const TICKET_TYPES = [
  {
    value: "technical",
    label: "Tengo un problema técnico",
    icon: AlertCircle,
    color: "text-red-500",
    bg: "bg-red-50 border-red-200 hover:bg-red-100",
    activeBg: "bg-red-100 border-red-400",
    description: "Errores, fallos o comportamientos inesperados",
  },
  {
    value: "usage",
    label: "Tengo una duda de uso",
    icon: HelpCircle,
    color: "text-blue-500",
    bg: "bg-blue-50 border-blue-200 hover:bg-blue-100",
    activeBg: "bg-blue-100 border-blue-400",
    description: "¿Cómo funciona algo? ¿Cómo lo configuro?",
  },
  {
    value: "billing",
    label: "Mi cuenta o facturación",
    icon: CreditCard,
    color: "text-amber-500",
    bg: "bg-amber-50 border-amber-200 hover:bg-amber-100",
    activeBg: "bg-amber-100 border-amber-400",
    description: "Pagos, facturas, suscripciones o cargos",
  },
  {
    value: "feedback",
    label: "Quiero dar feedback",
    icon: Lightbulb,
    color: "text-green-500",
    bg: "bg-green-50 border-green-200 hover:bg-green-100",
    activeBg: "bg-green-100 border-green-400",
    description: "Sugerencias, mejoras o ideas",
  },
  {
    value: "other",
    label: "Otro",
    icon: Paperclip,
    color: "text-slate-500",
    bg: "bg-slate-50 border-slate-200 hover:bg-slate-100",
    activeBg: "bg-slate-100 border-slate-400",
    description: "Cualquier otra consulta",
  },
];

const PRIORITIES = [
  {
    value: "urgent",
    label: "Urgente",
    desc: "No puedo trabajar",
    color: "bg-red-100 text-red-700 border-red-300",
    dot: "bg-red-500",
  },
  {
    value: "normal",
    label: "Normal",
    desc: "Me afecta pero puedo continuar",
    color: "bg-amber-100 text-amber-700 border-amber-300",
    dot: "bg-amber-500",
  },
  {
    value: "low",
    label: "Sin prisa",
    desc: "Cuando podáis",
    color: "bg-green-100 text-green-700 border-green-300",
    dot: "bg-green-500",
  },
];

const STATUS_CONFIG = {
  received: { label: "Recibido", color: "bg-blue-100 text-blue-700", icon: Inbox },
  reviewing: { label: "En revisión", color: "bg-amber-100 text-amber-700", icon: Clock },
  replied: { label: "Respondido", color: "bg-purple-100 text-purple-700", icon: MessageSquare },
  resolved: { label: "Resuelto", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  closed: { label: "Cerrado", color: "bg-slate-100 text-slate-600", icon: TicketCheck },
};

const TYPE_LABELS = {
  technical: "Problema técnico",
  usage: "Duda de uso",
  billing: "Cuenta / Facturación",
  feedback: "Feedback",
  other: "Otro",
};

// ==================== SUB-COMPONENTS ====================

const StatusBadge = ({ status }) => {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.received;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
};

const PriorityDot = ({ priority }) => {
  const cfg = PRIORITIES.find((p) => p.value === priority);
  if (!cfg) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-slate-500">
      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
};

const StarRating = ({ value, onChange, readOnly = false }) => (
  <div className="flex gap-1">
    {[1, 2, 3, 4, 5].map((star) => (
      <button
        key={star}
        type="button"
        disabled={readOnly}
        onClick={() => !readOnly && onChange && onChange(star)}
        className={`transition-colors ${readOnly ? "cursor-default" : "cursor-pointer hover:text-amber-400"} ${
          star <= value ? "text-amber-400" : "text-slate-300"
        }`}
      >
        <Star className="w-6 h-6 fill-current" />
      </button>
    ))}
  </div>
);

// ==================== TICKET DETAIL VIEW ====================

const TicketDetail = ({ ticket, onBack, onRefresh }) => {
  const { user } = useAuth();
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [rating, setRating] = useState(ticket.rating || 0);
  const [ratingComment, setRatingComment] = useState(ticket.rating_comment || "");
  const [submittingRating, setSubmittingRating] = useState(false);
  const [reopening, setReopening] = useState(false);

  const isClosed = ticket.status === "closed" || ticket.status === "resolved";

  const sendMessage = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      await api.post(`/support/tickets/${ticket.id}/messages`, { content: message });
      toast.success("Mensaje enviado");
      setMessage("");
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al enviar el mensaje");
    } finally {
      setSending(false);
    }
  };

  const submitRating = async () => {
    if (!rating) {
      toast.error("Selecciona una valoración");
      return;
    }
    setSubmittingRating(true);
    try {
      await api.post(`/support/tickets/${ticket.id}/rate`, {
        rating,
        comment: ratingComment,
      });
      toast.success("Valoración enviada. ¡Gracias!");
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al enviar la valoración");
    } finally {
      setSubmittingRating(false);
    }
  };

  const handleReopen = async () => {
    setReopening(true);
    try {
      await api.post(`/support/tickets/${ticket.id}/reopen`);
      toast.success("Ticket reabierto");
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al reabrir el ticket");
    } finally {
      setReopening(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Volver
        </Button>
        <div className="flex-1" />
        <StatusBadge status={ticket.status} />
      </div>

      {/* Ticket info */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-mono text-slate-400 mb-1">#{ticket.ticket_number}</p>
              <CardTitle className="text-lg">{ticket.subject}</CardTitle>
            </div>
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            <span className="text-xs text-slate-500">
              <span className="font-medium text-slate-700">Tipo:</span>{" "}
              {TYPE_LABELS[ticket.type] || ticket.type}
            </span>
            <PriorityDot priority={ticket.priority} />
            <span className="text-xs text-slate-500">
              {new Date(ticket.created_at).toLocaleDateString("es-ES", {
                day: "2-digit", month: "short", year: "numeric",
              })}
            </span>
          </div>
        </CardHeader>
      </Card>

      {/* Messages thread */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-700">
            Hilo de conversación
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {ticket.messages?.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.author_role === "support" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.author_role === "support"
                    ? "bg-indigo-100"
                    : "bg-slate-200"
                }`}
              >
                {msg.author_role === "support" ? (
                  <Shield className="w-4 h-4 text-indigo-600" />
                ) : (
                  <User className="w-4 h-4 text-slate-600" />
                )}
              </div>
              <div
                className={`flex-1 max-w-[85%] ${msg.author_role === "support" ? "items-end" : ""}`}
              >
                <div
                  className={`rounded-lg p-3 ${
                    msg.author_role === "support"
                      ? "bg-indigo-50 border border-indigo-100"
                      : "bg-slate-50 border border-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-slate-700">{msg.author}</span>
                    {msg.author_role === "support" && (
                      <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 text-indigo-600 border-indigo-200">
                        Soporte
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{msg.content}</p>
                </div>
                <p className="text-[10px] text-slate-400 mt-1 px-1">
                  {new Date(msg.created_at).toLocaleString("es-ES", {
                    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          ))}
        </CardContent>

        {/* Reply box */}
        {!isClosed && (
          <div className="px-6 pb-6 pt-2 border-t border-slate-100">
            <Label className="text-xs font-medium text-slate-600 mb-2 block">
              Tu respuesta
            </Label>
            <Textarea
              placeholder="Escribe tu mensaje aquí..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              className="resize-none"
            />
            <div className="flex justify-end mt-2">
              <Button
                size="sm"
                className="btn-primary"
                onClick={sendMessage}
                disabled={sending || !message.trim()}
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
        )}
      </Card>

      {/* Rating (only for resolved/closed without rating) */}
      {isClosed && !ticket.rating && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Star className="w-4 h-4 text-amber-400" />
              ¿Quedó resuelta tu consulta?
            </CardTitle>
            <CardDescription>Tu valoración nos ayuda a mejorar el soporte</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <StarRating value={rating} onChange={setRating} />
            <Textarea
              placeholder="Comentario opcional..."
              value={ratingComment}
              onChange={(e) => setRatingComment(e.target.value)}
              rows={2}
              className="resize-none"
            />
            <Button
              size="sm"
              onClick={submitRating}
              disabled={submittingRating || !rating}
              className="btn-primary"
            >
              {submittingRating ? (
                <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
              ) : (
                <Star className="w-4 h-4 mr-2" />
              )}
              Enviar valoración
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Show existing rating */}
      {ticket.rating && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <StarRating value={ticket.rating} readOnly />
              {ticket.rating_comment && (
                <p className="text-sm text-slate-600 italic">"{ticket.rating_comment}"</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Reopen button */}
      {isClosed && (
        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={handleReopen} disabled={reopening}>
            <RotateCcw className="w-4 h-4 mr-2" />
            {reopening ? "Reabriendo..." : "Reabrir ticket"}
          </Button>
        </div>
      )}
    </div>
  );
};

// ==================== CREATE TICKET FORM ====================

const CreateTicketForm = ({ onCreated, onCancel, userData }) => {
  const [step, setStep] = useState(1); // 1: type selection, 2: form
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    type: "",
    subject: "",
    description: "",
    priority: "normal",
    section: "",
    what_tried: "",
    what_happened: "",
    when_started: "",
    is_recurring: null,
  });

  const selectedType = TICKET_TYPES.find((t) => t.value === form.type);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!form.subject.trim() || !form.description.trim()) {
      toast.error("El asunto y la descripción son obligatorios");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/support/tickets", form);
      toast.success(`Ticket ${res.data.ticket_number} creado correctamente`);
      onCreated(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al crear el ticket");
    } finally {
      setSubmitting(false);
    }
  };

  if (step === 1) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">¿En qué podemos ayudarte?</h2>
          <p className="text-sm text-slate-500 mt-1">Selecciona el tipo de consulta</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {TICKET_TYPES.map((type) => {
            const Icon = type.icon;
            const isSelected = form.type === type.value;
            return (
              <button
                key={type.value}
                type="button"
                onClick={() => {
                  handleChange("type", type.value);
                  setStep(2);
                }}
                className={`flex items-start gap-4 p-4 rounded-lg border-2 text-left transition-all ${
                  isSelected ? type.activeBg : type.bg
                }`}
              >
                <Icon className={`w-6 h-6 mt-0.5 flex-shrink-0 ${type.color}`} />
                <div>
                  <p className="font-medium text-slate-800 text-sm">{type.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{type.description}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 ml-auto mt-0.5 flex-shrink-0" />
              </button>
            );
          })}
        </div>

        <div className="flex justify-end">
          <Button variant="ghost" onClick={onCancel}>Cancelar</Button>
        </div>
      </div>
    );
  }

  // Step 2: Form
  return (
    <div className="space-y-6">
      {/* Selected type pill */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Cambiar tipo
        </button>
        {selectedType && (
          <Badge variant="outline" className={`${selectedType.color}`}>
            <selectedType.icon className={`w-3 h-3 mr-1 ${selectedType.color}`} />
            {selectedType.label}
          </Badge>
        )}
      </div>

      {/* Auto-filled user info */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="p-4">
          <p className="text-xs font-medium text-slate-500 mb-2">Datos del solicitante</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-slate-400 text-xs">Nombre</span>
              <p className="font-medium text-slate-800">{userData?.name || "—"}</p>
            </div>
            <div>
              <span className="text-slate-400 text-xs">Email</span>
              <p className="font-medium text-slate-800">{userData?.email || "—"}</p>
            </div>
            {userData?.company && (
              <div>
                <span className="text-slate-400 text-xs">Empresa</span>
                <p className="font-medium text-slate-800">{userData.company}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Subject */}
      <div className="space-y-2">
        <Label htmlFor="subject">Asunto *</Label>
        <Input
          id="subject"
          placeholder="Resume tu consulta en una frase"
          value={form.subject}
          onChange={(e) => handleChange("subject", e.target.value)}
          maxLength={200}
        />
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Descripción *</Label>
        <Textarea
          id="description"
          placeholder={
            form.type === "technical"
              ? "Describe el problema con el mayor detalle posible..."
              : form.type === "usage"
              ? "Describe tu duda..."
              : "Describe tu consulta..."
          }
          value={form.description}
          onChange={(e) => handleChange("description", e.target.value)}
          rows={4}
          className="resize-none"
        />
      </div>

      {/* Technical extra fields */}
      {form.type === "technical" && (
        <div className="space-y-4 p-4 bg-red-50 rounded-lg border border-red-100">
          <p className="text-xs font-semibold text-red-700">Información adicional del problema técnico</p>

          <div className="space-y-2">
            <Label htmlFor="what_tried" className="text-xs">¿Qué estabas intentando hacer?</Label>
            <Input
              id="what_tried"
              placeholder="Ej: Sincronizar el proveedor X"
              value={form.what_tried}
              onChange={(e) => handleChange("what_tried", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="what_happened" className="text-xs">¿Qué ocurrió en su lugar?</Label>
            <Input
              id="what_happened"
              placeholder="Ej: Aparece un error en pantalla"
              value={form.what_happened}
              onChange={(e) => handleChange("what_happened", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="when_started" className="text-xs">¿Cuándo empezó el problema?</Label>
            <Input
              id="when_started"
              placeholder="Ej: Ayer por la tarde, desde la actualización..."
              value={form.when_started}
              onChange={(e) => handleChange("when_started", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs">¿Se repite siempre o es intermitente?</Label>
            <div className="flex gap-3">
              {[
                { value: true, label: "Siempre" },
                { value: false, label: "Intermitente" },
              ].map((opt) => (
                <button
                  key={String(opt.value)}
                  type="button"
                  onClick={() => handleChange("is_recurring", opt.value)}
                  className={`px-3 py-1.5 rounded-md border text-sm transition-colors ${
                    form.is_recurring === opt.value
                      ? "bg-red-600 text-white border-red-600"
                      : "bg-white text-slate-700 border-slate-300 hover:bg-red-50"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Usage section field */}
      {form.type === "usage" && (
        <div className="space-y-2">
          <Label htmlFor="section">¿En qué sección de la web estás?</Label>
          <Input
            id="section"
            placeholder="Ej: Catálogos, Proveedores, Exportar..."
            value={form.section}
            onChange={(e) => handleChange("section", e.target.value)}
          />
        </div>
      )}

      {/* Priority */}
      <div className="space-y-2">
        <Label>Prioridad</Label>
        <div className="flex flex-wrap gap-2">
          {PRIORITIES.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => handleChange("priority", p.value)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${
                form.priority === p.value
                  ? p.color + " border-current font-medium"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${p.dot}`} />
              <span>{p.label}</span>
              <span className="text-xs opacity-70">— {p.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between pt-2 border-t border-slate-100">
        <Button variant="ghost" onClick={onCancel}>Cancelar</Button>
        <Button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={submitting || !form.subject.trim() || !form.description.trim()}
        >
          {submitting ? (
            <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
          ) : (
            <Send className="w-4 h-4 mr-2" />
          )}
          Enviar consulta
        </Button>
      </div>
    </div>
  );
};

// ==================== TICKET LIST ====================

const TicketList = ({ tickets, onSelect, loading }) => {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  if (!tickets.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <TicketCheck className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-slate-700 font-medium">Sin tickets todavía</h3>
        <p className="text-slate-400 text-sm mt-1">
          Crea un nuevo ticket si necesitas ayuda
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tickets.map((ticket) => (
        <button
          key={ticket.id}
          onClick={() => onSelect(ticket)}
          className="w-full text-left p-4 bg-white border border-slate-200 rounded-lg hover:border-indigo-300 hover:shadow-sm transition-all group"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-slate-400">#{ticket.ticket_number}</span>
                <StatusBadge status={ticket.status} />
                {ticket.rating && (
                  <span className="flex items-center gap-0.5 text-xs text-amber-500">
                    <Star className="w-3 h-3 fill-current" />
                    {ticket.rating}
                  </span>
                )}
              </div>
              <p className="font-medium text-slate-800 truncate group-hover:text-indigo-700 transition-colors">
                {ticket.subject}
              </p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-slate-400">
                  {TYPE_LABELS[ticket.type] || ticket.type}
                </span>
                <PriorityDot priority={ticket.priority} />
                <span className="text-xs text-slate-400">
                  {new Date(ticket.created_at).toLocaleDateString("es-ES", {
                    day: "2-digit", month: "short", year: "numeric",
                  })}
                </span>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-colors flex-shrink-0 mt-1" />
          </div>
          {ticket.messages?.length > 1 && (
            <div className="flex items-center gap-1 mt-2 text-xs text-slate-400">
              <MessageSquare className="w-3 h-3" />
              {ticket.messages.length} mensajes
            </div>
          )}
        </button>
      ))}
    </div>
  );
};

// ==================== MAIN PAGE ====================

const Support = () => {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("open");

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const res = await api.get("/support/tickets");
      setTickets(res.data);
    } catch (err) {
      toast.error("Error al cargar los tickets");
    } finally {
      setLoading(false);
    }
  };

  const handleTicketCreated = (ticket) => {
    setTickets((prev) => [ticket, ...prev]);
    setShowCreate(false);
    setSelectedTicket(ticket);
  };

  const handleRefreshTicket = async () => {
    try {
      const res = await api.get(`/support/tickets/${selectedTicket.id}`);
      setSelectedTicket(res.data);
      setTickets((prev) => prev.map((t) => (t.id === res.data.id ? res.data : t)));
    } catch (_) {
      toast.error("Error al actualizar el ticket");
    }
  };

  // Filter tickets by tab
  const openStatuses = ["received", "reviewing", "replied"];
  const closedStatuses = ["resolved", "closed"];

  const openTickets = tickets.filter((t) => openStatuses.includes(t.status));
  const closedTickets = tickets.filter((t) => closedStatuses.includes(t.status));

  // ---- Selected ticket detail ----
  if (selectedTicket) {
    const fresh = tickets.find((t) => t.id === selectedTicket.id) || selectedTicket;
    return (
      <div className="max-w-3xl mx-auto space-y-6" data-testid="support-ticket-detail">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
              Soporte
            </h1>
            <p className="text-slate-500 mt-1 text-sm">Detalle del ticket</p>
          </div>
          <Button variant="outline" size="sm" onClick={handleRefreshTicket}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>
        <TicketDetail
          ticket={fresh}
          onBack={() => setSelectedTicket(null)}
          onRefresh={handleRefreshTicket}
        />
      </div>
    );
  }

  // ---- Create ticket ----
  if (showCreate) {
    return (
      <div className="max-w-2xl mx-auto space-y-6" data-testid="support-create-ticket">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
            Nuevo ticket de soporte
          </h1>
          <p className="text-slate-500 mt-1 text-sm">
            Te responderemos lo antes posible
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <CreateTicketForm
              onCreated={handleTicketCreated}
              onCancel={() => setShowCreate(false)}
              userData={user}
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  // ---- Tickets list ----
  return (
    <div className="space-y-6" data-testid="support-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Manrope, sans-serif" }}>
            Soporte
          </h1>
          <p className="text-slate-500 mt-1">Gestiona tus consultas y tickets de ayuda</p>
        </div>
        <Button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Nuevo ticket
        </Button>
      </div>

      {/* Status info cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-blue-100 bg-blue-50">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Inbox className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-700">{openTickets.length}</p>
              <p className="text-xs text-blue-600">Tickets abiertos</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-green-100 bg-green-50">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-700">{closedTickets.length}</p>
              <p className="text-xs text-green-600">Tickets resueltos</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-100">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-slate-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-700">Tiempo de respuesta</p>
              <p className="text-xs text-slate-500">Habitualmente en menos de 24h</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ticket tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full md:w-auto">
          <TabsTrigger value="open" className="flex-1 md:flex-none">
            Abiertos
            {openTickets.length > 0 && (
              <span className="ml-2 bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5 rounded-full">
                {openTickets.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="closed" className="flex-1 md:flex-none">
            Resueltos
            {closedTickets.length > 0 && (
              <span className="ml-2 bg-slate-100 text-slate-600 text-xs px-1.5 py-0.5 rounded-full">
                {closedTickets.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="open" className="mt-4">
          <TicketList
            tickets={openTickets}
            onSelect={setSelectedTicket}
            loading={loading}
          />
          {!loading && openTickets.length === 0 && tickets.length > 0 && (
            <div className="text-center py-8 text-slate-400 text-sm">
              No tienes tickets abiertos
            </div>
          )}
        </TabsContent>

        <TabsContent value="closed" className="mt-4">
          <TicketList
            tickets={closedTickets}
            onSelect={setSelectedTicket}
            loading={loading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Support;
