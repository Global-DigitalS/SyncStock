import { useState, useEffect, useContext } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from "../components/ui/alert-dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  FileText, Plus, Pencil, Trash2, RefreshCw, Eye, Code, 
  Mail, Save, RotateCcw, Send, CheckCircle, AlertCircle
} from "lucide-react";

const AdminEmailTemplates = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewSubject, setPreviewSubject] = useState("");
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    key: "",
    subject: "",
    html_content: "",
    text_content: "",
    variables: [],
    is_active: true
  });
  const [editTab, setEditTab] = useState("html");

  const TEMPLATE_ICONS = {
    welcome: "👋",
    password_reset: "🔑",
    subscription_change: "💳"
  };

  useEffect(() => {
    if (user?.role !== "superadmin") {
      navigate("/");
      return;
    }
    fetchTemplates();
  }, [user, navigate]);

  const fetchTemplates = async () => {
    try {
      const res = await api.get("/admin/email-templates");
      setTemplates(res.data);
    } catch (error) {
      toast.error("Error al cargar plantillas");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      key: "",
      subject: "",
      html_content: "",
      text_content: "",
      variables: [],
      is_active: true
    });
    setSelectedTemplate(null);
  };

  const openEdit = (template) => {
    setSelectedTemplate(template);
    setFormData({
      name: template.name,
      key: template.key,
      subject: template.subject,
      html_content: template.html_content || "",
      text_content: template.text_content || "",
      variables: template.variables || [],
      is_active: template.is_active !== false
    });
    setEditTab("html");
    setShowDialog(true);
  };

  const openCreate = () => {
    resetForm();
    setShowDialog(true);
  };

  const openDelete = (template) => {
    setSelectedTemplate(template);
    setShowDeleteDialog(true);
  };

  const handlePreview = async (template) => {
    try {
      const res = await api.post(`/admin/email-templates/${template.id}/preview`);
      setPreviewHtml(res.data.html);
      setPreviewSubject(res.data.subject);
      setShowPreviewDialog(true);
    } catch (error) {
      toast.error("Error al generar vista previa");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.subject.trim()) {
      toast.error("Nombre y asunto son obligatorios");
      return;
    }

    setSaving(true);
    try {
      if (selectedTemplate) {
        await api.put(`/admin/email-templates/${selectedTemplate.id}`, formData);
        toast.success("Plantilla actualizada");
      } else {
        if (!formData.key.trim()) {
          toast.error("La clave es obligatoria para nuevas plantillas");
          setSaving(false);
          return;
        }
        await api.post("/admin/email-templates", formData);
        toast.success("Plantilla creada");
      }
      setShowDialog(false);
      resetForm();
      fetchTemplates();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/admin/email-templates/${selectedTemplate.id}`);
      toast.success("Plantilla eliminada");
      setShowDeleteDialog(false);
      fetchTemplates();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const handleResetDefaults = async () => {
    setResetting(true);
    try {
      await api.post("/admin/email-templates/reset-defaults");
      toast.success("Plantillas restablecidas");
      fetchTemplates();
    } catch (error) {
      toast.error("Error al restablecer");
    } finally {
      setResetting(false);
    }
  };

  const isDefaultTemplate = (key) => ["welcome", "password_reset", "subscription_change"].includes(key);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Plantillas de Email
          </h1>
          <p className="text-slate-500">Personaliza los correos electrónicos del sistema</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleResetDefaults} disabled={resetting}>
            {resetting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <RotateCcw className="w-4 h-4 mr-2" />}
            Restablecer
          </Button>
          <Button onClick={openCreate} className="btn-primary" data-testid="add-template-btn">
            <Plus className="w-4 h-4 mr-2" />
            Nueva Plantilla
          </Button>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {templates.map((template) => (
          <Card key={template.id} className={!template.is_active ? "opacity-60" : ""}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{TEMPLATE_ICONS[template.key] || "📧"}</div>
                  <div>
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <p className="text-sm text-slate-500 font-mono">{template.key}</p>
                  </div>
                </div>
                {!template.is_active && (
                  <Badge variant="secondary">Inactivo</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-xs text-slate-500">Asunto</Label>
                <p className="text-sm font-medium truncate">{template.subject}</p>
              </div>

              {template.variables && template.variables.length > 0 && (
                <div>
                  <Label className="text-xs text-slate-500">Variables disponibles</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {template.variables.map((v, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs font-mono">
                        {`{${v}}`}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => handlePreview(template)}>
                  <Eye className="w-4 h-4 mr-1" />
                  Vista previa
                </Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => openEdit(template)}>
                  <Pencil className="w-4 h-4 mr-1" />
                  Editar
                </Button>
                {!isDefaultTemplate(template.key) && (
                  <Button variant="outline" size="sm" onClick={() => openDelete(template)} className="text-rose-600 hover:text-rose-700">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}

        {templates.length === 0 && (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No hay plantillas</h3>
              <p className="text-slate-500 mb-4">Las plantillas predeterminadas se crearán automáticamente</p>
              <Button onClick={fetchTemplates} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Cargar plantillas
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <FileText className="w-5 h-5 text-purple-600" />
              {selectedTemplate ? "Editar Plantilla" : "Nueva Plantilla"}
            </DialogTitle>
            <DialogDescription>
              Usa variables como {`{name}`}, {`{email}`}, {`{app_name}`} en tu contenido
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Info */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Bienvenida"
                  className="input-base"
                  data-testid="template-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="key">Clave (identificador)</Label>
                <Input
                  id="key"
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                  placeholder="welcome_new_user"
                  className="input-base font-mono"
                  disabled={selectedTemplate && isDefaultTemplate(selectedTemplate.key)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Asunto del Email *</Label>
              <Input
                id="subject"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                placeholder="¡Bienvenido a {app_name}!"
                className="input-base"
              />
            </div>

            {/* Content Tabs */}
            <Tabs value={editTab} onValueChange={setEditTab} className="space-y-4">
              <TabsList className="bg-slate-100">
                <TabsTrigger value="html" className="data-[state=active]:bg-white">
                  <Code className="w-4 h-4 mr-2" />
                  HTML
                </TabsTrigger>
                <TabsTrigger value="text" className="data-[state=active]:bg-white">
                  <FileText className="w-4 h-4 mr-2" />
                  Texto plano
                </TabsTrigger>
                <TabsTrigger value="variables" className="data-[state=active]:bg-white">
                  Variables
                </TabsTrigger>
              </TabsList>

              <TabsContent value="html" className="space-y-2">
                <Label>Contenido HTML</Label>
                <Textarea
                  value={formData.html_content}
                  onChange={(e) => setFormData({ ...formData, html_content: e.target.value })}
                  placeholder="<html>...</html>"
                  className="font-mono text-sm min-h-[300px]"
                />
              </TabsContent>

              <TabsContent value="text" className="space-y-2">
                <Label>Contenido de texto plano (fallback)</Label>
                <Textarea
                  value={formData.text_content}
                  onChange={(e) => setFormData({ ...formData, text_content: e.target.value })}
                  placeholder="Versión de texto plano del email..."
                  className="min-h-[300px]"
                />
              </TabsContent>

              <TabsContent value="variables" className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Variables disponibles</h4>
                  <p className="text-sm text-slate-500 mb-4">
                    Estas variables se reemplazarán automáticamente al enviar el email:
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      { var: "name", desc: "Nombre del usuario" },
                      { var: "email", desc: "Email del usuario" },
                      { var: "app_name", desc: "Nombre de la app" },
                      { var: "app_url", desc: "URL de la app" },
                      { var: "primary_color", desc: "Color primario" },
                      { var: "footer_text", desc: "Texto del footer" },
                      { var: "reset_link", desc: "Link de reset (password)" },
                      { var: "old_plan", desc: "Plan anterior" },
                      { var: "new_plan", desc: "Nuevo plan" }
                    ].map((item) => (
                      <div key={item.var} className="flex items-center gap-2 p-2 bg-white rounded border">
                        <code className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          {`{${item.var}}`}
                        </code>
                        <span className="text-xs text-slate-500">{item.desc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving} className="btn-primary" data-testid="template-submit-btn">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                {selectedTemplate ? "Guardar" : "Crear"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-purple-600" />
              Vista Previa del Email
            </DialogTitle>
            <DialogDescription>
              Asunto: {previewSubject}
            </DialogDescription>
          </DialogHeader>
          <div className="border rounded-lg overflow-hidden max-h-[60vh] overflow-y-auto">
            <iframe
              srcDoc={previewHtml}
              className="w-full h-[500px] border-0"
              title="Email Preview"
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar plantilla?</AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminará la plantilla "{selectedTemplate?.name}". Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-rose-600 hover:bg-rose-700">
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminEmailTemplates;
