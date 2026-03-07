import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Save, Plus, Trash2, GripVertical, Eye, Layout, 
  MessageSquare, HelpCircle, Megaphone, Star
} from "lucide-react";
import { api } from "../App";

const AdminLanding = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [content, setContent] = useState({
    hero: {
      title: "",
      subtitle: "",
      cta_primary: "",
      cta_secondary: ""
    },
    features: [],
    benefits: { title: "", items: [] },
    testimonials: [],
    faq: [],
    cta_final: { title: "", subtitle: "", button_text: "" },
    footer: { company_description: "", links: [] }
  });

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      const res = await api.get("/landing/content");
      if (res.data) {
        setContent(prev => ({ ...prev, ...res.data }));
      }
    } catch (error) {
      console.error("Error loading content:", error);
    } finally {
      setLoading(false);
    }
  };

  const saveContent = async () => {
    setSaving(true);
    try {
      await api.put("/admin/landing/content", content);
      toast.success("Contenido guardado correctamente");
    } catch (error) {
      toast.error("Error al guardar el contenido");
    } finally {
      setSaving(false);
    }
  };

  const updateHero = (field, value) => {
    setContent(prev => ({
      ...prev,
      hero: { ...prev.hero, [field]: value }
    }));
  };

  const updateFeature = (index, field, value) => {
    const newFeatures = [...content.features];
    newFeatures[index] = { ...newFeatures[index], [field]: value };
    setContent(prev => ({ ...prev, features: newFeatures }));
  };

  const addFeature = () => {
    setContent(prev => ({
      ...prev,
      features: [...prev.features, { icon: "Zap", title: "", description: "" }]
    }));
  };

  const removeFeature = (index) => {
    setContent(prev => ({
      ...prev,
      features: prev.features.filter((_, i) => i !== index)
    }));
  };

  const updateTestimonial = (index, field, value) => {
    const newTestimonials = [...content.testimonials];
    newTestimonials[index] = { ...newTestimonials[index], [field]: value };
    setContent(prev => ({ ...prev, testimonials: newTestimonials }));
  };

  const addTestimonial = () => {
    setContent(prev => ({
      ...prev,
      testimonials: [...prev.testimonials, { quote: "", author: "", role: "" }]
    }));
  };

  const removeTestimonial = (index) => {
    setContent(prev => ({
      ...prev,
      testimonials: prev.testimonials.filter((_, i) => i !== index)
    }));
  };

  const updateFaq = (index, field, value) => {
    const newFaq = [...content.faq];
    newFaq[index] = { ...newFaq[index], [field]: value };
    setContent(prev => ({ ...prev, faq: newFaq }));
  };

  const addFaq = () => {
    setContent(prev => ({
      ...prev,
      faq: [...prev.faq, { question: "", answer: "" }]
    }));
  };

  const removeFaq = (index) => {
    setContent(prev => ({
      ...prev,
      faq: prev.faq.filter((_, i) => i !== index)
    }));
  };

  const updateBenefitItem = (index, field, value) => {
    const newItems = [...(content.benefits?.items || [])];
    newItems[index] = { ...newItems[index], [field]: value };
    setContent(prev => ({
      ...prev,
      benefits: { ...prev.benefits, items: newItems }
    }));
  };

  const addBenefitItem = () => {
    setContent(prev => ({
      ...prev,
      benefits: {
        ...prev.benefits,
        items: [...(prev.benefits?.items || []), { stat: "", text: "" }]
      }
    }));
  };

  const removeBenefitItem = (index) => {
    setContent(prev => ({
      ...prev,
      benefits: {
        ...prev.benefits,
        items: prev.benefits.items.filter((_, i) => i !== index)
      }
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  const iconOptions = ["Zap", "Database", "Store", "Calculator", "RefreshCw", "Shield", "Layers", "BarChart3", "Clock", "Users", "Star"];

  return (
    <div className="space-y-6" data-testid="admin-landing-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Editor de Landing Page
          </h1>
          <p className="text-slate-500 mt-1">
            Personaliza el contenido de la página de ventas
          </p>
        </div>
        <div className="flex items-center gap-3">
          <a href="/" target="_blank" rel="noopener noreferrer">
            <Button variant="outline">
              <Eye className="w-4 h-4 mr-2" />
              Vista Previa
            </Button>
          </a>
          <Button onClick={saveContent} disabled={saving} className="btn-primary">
            {saving ? (
              <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Guardar Cambios
          </Button>
        </div>
      </div>

      <Tabs defaultValue="hero" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-[600px]">
          <TabsTrigger value="hero">
            <Layout className="w-4 h-4 mr-2" />
            Hero
          </TabsTrigger>
          <TabsTrigger value="features">
            <Star className="w-4 h-4 mr-2" />
            Features
          </TabsTrigger>
          <TabsTrigger value="testimonials">
            <MessageSquare className="w-4 h-4 mr-2" />
            Testimonios
          </TabsTrigger>
          <TabsTrigger value="faq">
            <HelpCircle className="w-4 h-4 mr-2" />
            FAQ
          </TabsTrigger>
          <TabsTrigger value="cta">
            <Megaphone className="w-4 h-4 mr-2" />
            CTA
          </TabsTrigger>
        </TabsList>

        {/* Hero Section */}
        <TabsContent value="hero">
          <Card>
            <CardHeader>
              <CardTitle>Sección Hero</CardTitle>
              <CardDescription>El mensaje principal que verán los visitantes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Título Principal</Label>
                <Input
                  value={content.hero?.title || ""}
                  onChange={(e) => updateHero("title", e.target.value)}
                  placeholder="Sincroniza tu inventario con un clic"
                />
              </div>
              <div className="space-y-2">
                <Label>Subtítulo</Label>
                <Textarea
                  value={content.hero?.subtitle || ""}
                  onChange={(e) => updateHero("subtitle", e.target.value)}
                  placeholder="Conecta proveedores, gestiona catálogos..."
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Botón Principal</Label>
                  <Input
                    value={content.hero?.cta_primary || ""}
                    onChange={(e) => updateHero("cta_primary", e.target.value)}
                    placeholder="Empezar Gratis"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Botón Secundario</Label>
                  <Input
                    value={content.hero?.cta_secondary || ""}
                    onChange={(e) => updateHero("cta_secondary", e.target.value)}
                    placeholder="Ver Demo"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Benefits/Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Estadísticas</CardTitle>
              <CardDescription>Números que impresionan a los visitantes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.benefits?.items || []).map((item, idx) => (
                <div key={idx} className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg">
                  <GripVertical className="w-5 h-5 text-slate-400 cursor-move" />
                  <Input
                    value={item.stat}
                    onChange={(e) => updateBenefitItem(idx, "stat", e.target.value)}
                    placeholder="80%"
                    className="w-24"
                  />
                  <Input
                    value={item.text}
                    onChange={(e) => updateBenefitItem(idx, "text", e.target.value)}
                    placeholder="Menos tiempo en gestión"
                    className="flex-1"
                  />
                  <Button variant="ghost" size="sm" onClick={() => removeBenefitItem(idx)}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              ))}
              <Button variant="outline" onClick={addBenefitItem}>
                <Plus className="w-4 h-4 mr-2" />
                Añadir Estadística
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Features Section */}
        <TabsContent value="features">
          <Card>
            <CardHeader>
              <CardTitle>Características</CardTitle>
              <CardDescription>Las funcionalidades principales de tu producto</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.features || []).map((feature, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">Característica {idx + 1}</span>
                    <Button variant="ghost" size="sm" onClick={() => removeFeature(idx)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Icono</Label>
                      <select
                        value={feature.icon}
                        onChange={(e) => updateFeature(idx, "icon", e.target.value)}
                        className="w-full h-10 px-3 rounded-md border border-slate-200"
                      >
                        {iconOptions.map(icon => (
                          <option key={icon} value={icon}>{icon}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label>Título</Label>
                      <Input
                        value={feature.title}
                        onChange={(e) => updateFeature(idx, "title", e.target.value)}
                        placeholder="Sincronización Automática"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Descripción</Label>
                    <Textarea
                      value={feature.description}
                      onChange={(e) => updateFeature(idx, "description", e.target.value)}
                      placeholder="Actualiza precios, stock y productos..."
                      rows={2}
                    />
                  </div>
                </div>
              ))}
              <Button variant="outline" onClick={addFeature}>
                <Plus className="w-4 h-4 mr-2" />
                Añadir Característica
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Testimonials Section */}
        <TabsContent value="testimonials">
          <Card>
            <CardHeader>
              <CardTitle>Testimonios</CardTitle>
              <CardDescription>Opiniones de clientes satisfechos</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.testimonials || []).map((testimonial, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">Testimonio {idx + 1}</span>
                    <Button variant="ghost" size="sm" onClick={() => removeTestimonial(idx)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Cita</Label>
                    <Textarea
                      value={testimonial.quote}
                      onChange={(e) => updateTestimonial(idx, "quote", e.target.value)}
                      placeholder="SyncStock nos ha ahorrado más de 20 horas semanales..."
                      rows={3}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Nombre</Label>
                      <Input
                        value={testimonial.author}
                        onChange={(e) => updateTestimonial(idx, "author", e.target.value)}
                        placeholder="María García"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cargo / Empresa</Label>
                      <Input
                        value={testimonial.role}
                        onChange={(e) => updateTestimonial(idx, "role", e.target.value)}
                        placeholder="CEO, TechStore"
                      />
                    </div>
                  </div>
                </div>
              ))}
              <Button variant="outline" onClick={addTestimonial}>
                <Plus className="w-4 h-4 mr-2" />
                Añadir Testimonio
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* FAQ Section */}
        <TabsContent value="faq">
          <Card>
            <CardHeader>
              <CardTitle>Preguntas Frecuentes</CardTitle>
              <CardDescription>Resuelve las dudas más comunes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.faq || []).map((item, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-700">Pregunta {idx + 1}</span>
                    <Button variant="ghost" size="sm" onClick={() => removeFaq(idx)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Pregunta</Label>
                    <Input
                      value={item.question}
                      onChange={(e) => updateFaq(idx, "question", e.target.value)}
                      placeholder="¿Cuánto tiempo tarda la configuración inicial?"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Respuesta</Label>
                    <Textarea
                      value={item.answer}
                      onChange={(e) => updateFaq(idx, "answer", e.target.value)}
                      placeholder="La mayoría de usuarios están operativos en menos de 15 minutos..."
                      rows={3}
                    />
                  </div>
                </div>
              ))}
              <Button variant="outline" onClick={addFaq}>
                <Plus className="w-4 h-4 mr-2" />
                Añadir Pregunta
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* CTA Section */}
        <TabsContent value="cta">
          <Card>
            <CardHeader>
              <CardTitle>Call to Action Final</CardTitle>
              <CardDescription>El último empujón para la conversión</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Título</Label>
                <Input
                  value={content.cta_final?.title || ""}
                  onChange={(e) => setContent(prev => ({
                    ...prev,
                    cta_final: { ...prev.cta_final, title: e.target.value }
                  }))}
                  placeholder="¿Listo para automatizar tu negocio?"
                />
              </div>
              <div className="space-y-2">
                <Label>Subtítulo</Label>
                <Textarea
                  value={content.cta_final?.subtitle || ""}
                  onChange={(e) => setContent(prev => ({
                    ...prev,
                    cta_final: { ...prev.cta_final, subtitle: e.target.value }
                  }))}
                  placeholder="Únete a cientos de empresas..."
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Texto del Botón</Label>
                <Input
                  value={content.cta_final?.button_text || ""}
                  onChange={(e) => setContent(prev => ({
                    ...prev,
                    cta_final: { ...prev.cta_final, button_text: e.target.value }
                  }))}
                  placeholder="Comenzar Prueba Gratuita"
                />
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Footer</CardTitle>
              <CardDescription>Información del pie de página</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Descripción de la empresa</Label>
                <Textarea
                  value={content.footer?.company_description || ""}
                  onChange={(e) => setContent(prev => ({
                    ...prev,
                    footer: { ...prev.footer, company_description: e.target.value }
                  }))}
                  placeholder="SyncStock es la plataforma líder..."
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Floating Save Button */}
      <div className="fixed bottom-6 right-6">
        <Button onClick={saveContent} disabled={saving} size="lg" className="btn-primary shadow-xl">
          {saving ? (
            <div className="spinner w-5 h-5 border-2 border-white/30 border-t-white mr-2" />
          ) : (
            <Save className="w-5 h-5 mr-2" />
          )}
          Guardar Todo
        </Button>
      </div>
    </div>
  );
};

export default AdminLanding;
