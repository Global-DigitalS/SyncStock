import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Save, Plus, Trash2, GripVertical, Eye, Layout,
  MessageSquare, HelpCircle, Megaphone, Star,
  Search, Copy, Check, ExternalLink, Globe, Share2, Twitter
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { api } from "../App";

const DEFAULT_SEO = {
  site_url: "https://sync-stock.com",
  page_title: "SyncStock — Sincronización de Inventario B2B Automatizada",
  meta_description: "SyncStock — Sincroniza catálogos de proveedores, gestiona márgenes y publica en WooCommerce, Shopify y PrestaShop automáticamente. Prueba gratuita 14 días.",
  meta_keywords: "sincronización inventario, gestión catálogos, woocommerce, shopify, prestashop, dolibarr, odoo, proveedores ftp, stock automatico, b2b saas",
  robots: "index, follow",
  og_title: "SyncStock — Sincronización de Inventario B2B Automatizada",
  og_description: "Conecta proveedores FTP/SFTP/URL, gestiona catálogos con márgenes personalizados y publica en tus tiendas online automáticamente.",
  og_image: "",
  og_locale: "es_ES",
  og_site_name: "SyncStock",
  twitter_card: "summary_large_image",
  twitter_title: "SyncStock — Sincronización de Inventario B2B",
  twitter_description: "Automatiza la gestión de stock entre proveedores y tiendas online. WooCommerce, Shopify, Dolibarr y más.",
  twitter_image: ""
};

const AdminLanding = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingSeo, setSavingSeo] = useState(false);
  const [copiedSitemap, setCopiedSitemap] = useState(false);
  const [seo, setSeo] = useState(DEFAULT_SEO);
  const [content, setContent] = useState({
    hero: {
      title: "",
      subtitle: "",
      cta_primary: "",
      cta_secondary: "",
      badge: "",
      social_proof_text: ""
    },
    features: [],
    benefits: { title: "", items: [] },
    testimonials: [],
    faq: [],
    cta_final: { title: "", subtitle: "", button_text: "" },
    footer: { company_description: "", links: [] },
    how_it_works: []
  });

  useEffect(() => {
    loadContent();
    loadSeo();
  }, []);

  const loadContent = async () => {
    try {
      const res = await api.get("/landing/content");
      if (res.data) {
        setContent(prev => ({ ...prev, ...res.data }));
      }
    } catch (error) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  const loadSeo = async () => {
    try {
      const res = await api.get("/admin/seo");
      if (res.data) {
        setSeo(prev => ({ ...DEFAULT_SEO, ...res.data }));
      }
    } catch (error) {
      // handled silently
    }
  };

  const saveSeo = async () => {
    setSavingSeo(true);
    try {
      await api.put("/admin/seo", seo);
      toast.success("Configuración SEO guardada correctamente");
    } catch (error) {
      toast.error("Error al guardar la configuración SEO");
    } finally {
      setSavingSeo(false);
    }
  };

  const updateSeo = (field, value) => {
    setSeo(prev => ({ ...prev, [field]: value }));
  };

  const sitemapUrl = `${process.env.REACT_APP_BACKEND_URL}/api/seo/sitemap.xml`;

  const copySitemapUrl = async () => {
    try {
      await navigator.clipboard.writeText(sitemapUrl);
      setCopiedSitemap(true);
      toast.success("URL del sitemap copiada");
      setTimeout(() => setCopiedSitemap(false), 2000);
    } catch {
      toast.error("No se pudo copiar la URL");
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

  const updateHowItWorksStep = (index, field, value) => {
    const newSteps = [...(content.how_it_works || [])];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setContent(prev => ({ ...prev, how_it_works: newSteps }));
  };

  const addHowItWorksStep = () => {
    setContent(prev => ({
      ...prev,
      how_it_works: [
        ...(prev.how_it_works || []),
        { title: "", description: "" }
      ]
    }));
  };

  const removeHowItWorksStep = (index) => {
    setContent(prev => ({
      ...prev,
      how_it_works: (prev.how_it_works || []).filter((_, i) => i !== index)
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
        <TabsList className="grid w-full grid-cols-7 lg:w-[840px]">
          <TabsTrigger value="hero">
            <Layout className="w-4 h-4 mr-2" />
            Hero
          </TabsTrigger>
          <TabsTrigger value="features">
            <Star className="w-4 h-4 mr-2" />
            Features
          </TabsTrigger>
          <TabsTrigger value="how_it_works">
            Cómo funciona
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
          <TabsTrigger value="seo">
            <Search className="w-4 h-4 mr-2" />
            SEO
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
              <div className="space-y-2">
                <Label>Texto del badge</Label>
                <Input
                  value={content.hero?.badge || ""}
                  onChange={(e) => updateHero("badge", e.target.value)}
                  placeholder="Sincronización en tiempo real"
                />
                <p className="text-xs text-slate-400">Aparece encima del título principal como pill destacado</p>
              </div>
              <div className="space-y-2">
                <Label>Texto de social proof</Label>
                <Input
                  value={content.hero?.social_proof_text || ""}
                  onChange={(e) => updateHero("social_proof_text", e.target.value)}
                  placeholder="Usado por 500+ empresas en España y LATAM"
                />
                <p className="text-xs text-slate-400">Aparece debajo de los botones junto a los avatares</p>
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

        {/* How It Works Section */}
        <TabsContent value="how_it_works">
          <Card>
            <CardHeader>
              <CardTitle>Cómo funciona</CardTitle>
              <CardDescription>Los pasos que explican cómo usar SyncStock (máximo 3)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {(content.how_it_works || []).map((step, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700 flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                      Paso {idx + 1}
                    </span>
                    <Button variant="ghost" size="sm" onClick={() => removeHowItWorksStep(idx)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Título del paso</Label>
                    <Input
                      value={step.title}
                      onChange={(e) => updateHowItWorksStep(idx, "title", e.target.value)}
                      placeholder="Conecta un proveedor"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Descripción</Label>
                    <Textarea
                      value={step.description}
                      onChange={(e) => updateHowItWorksStep(idx, "description", e.target.value)}
                      placeholder="Añade la URL, FTP o sube el archivo CSV..."
                      rows={2}
                    />
                  </div>
                </div>
              ))}
              {(content.how_it_works || []).length < 3 && (
                <Button variant="outline" onClick={addHowItWorksStep}>
                  <Plus className="w-4 h-4 mr-2" />
                  Añadir Paso
                </Button>
              )}
              {(content.how_it_works || []).length >= 3 && (
                <p className="text-xs text-slate-400">Máximo 3 pasos recomendado para buena UX</p>
              )}
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
        {/* SEO Section */}
        <TabsContent value="seo" className="space-y-6">
          {/* Sitemap URL */}
          <Card className="border-emerald-200 bg-emerald-50">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-emerald-600" />
                <CardTitle className="text-emerald-800">Sitemap XML</CardTitle>
                <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">Público</Badge>
              </div>
              <CardDescription className="text-emerald-700">
                URL pública del sitemap generado automáticamente. Úsala en Google Search Console y otros motores de búsqueda.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Input
                  value={sitemapUrl}
                  readOnly
                  className="bg-white font-mono text-sm text-slate-700"
                />
                <Button variant="outline" size="icon" onClick={copySitemapUrl} className="shrink-0">
                  {copiedSitemap ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                </Button>
                <a href={sitemapUrl} target="_blank" rel="noopener noreferrer">
                  <Button variant="outline" size="icon" className="shrink-0">
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </a>
              </div>
              <p className="text-xs text-emerald-600 mt-2">
                El sitemap incluye automáticamente todas las páginas públicas de la landing page.
              </p>
            </CardContent>
          </Card>

          {/* Meta básico */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Search className="w-5 h-5 text-slate-600" />
                <CardTitle>Meta Básico</CardTitle>
              </div>
              <CardDescription>Información principal para motores de búsqueda</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>URL Canónica del sitio</Label>
                <Input
                  value={seo.site_url}
                  onChange={(e) => updateSeo("site_url", e.target.value)}
                  placeholder="https://sync-stock.com"
                />
                <p className="text-xs text-slate-500">Se usa en la etiqueta canonical y en el sitemap</p>
              </div>
              <div className="space-y-2">
                <Label>Título de la página</Label>
                <Input
                  value={seo.page_title}
                  onChange={(e) => updateSeo("page_title", e.target.value)}
                  placeholder="SyncStock — Sincronización de Inventario B2B Automatizada"
                />
                <p className="text-xs text-slate-500">{seo.page_title.length}/60 caracteres recomendados</p>
              </div>
              <div className="space-y-2">
                <Label>Meta Description</Label>
                <Textarea
                  value={seo.meta_description}
                  onChange={(e) => updateSeo("meta_description", e.target.value)}
                  placeholder="Descripción breve de la página para buscadores..."
                  rows={3}
                />
                <p className="text-xs text-slate-500">{seo.meta_description.length}/160 caracteres recomendados</p>
              </div>
              <div className="space-y-2">
                <Label>Palabras clave (keywords)</Label>
                <Textarea
                  value={seo.meta_keywords}
                  onChange={(e) => updateSeo("meta_keywords", e.target.value)}
                  placeholder="palabra1, palabra2, palabra3..."
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Robots</Label>
                <select
                  value={seo.robots}
                  onChange={(e) => updateSeo("robots", e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-slate-200 text-sm"
                >
                  <option value="index, follow">index, follow (recomendado)</option>
                  <option value="noindex, follow">noindex, follow</option>
                  <option value="index, nofollow">index, nofollow</option>
                  <option value="noindex, nofollow">noindex, nofollow</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Open Graph */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Share2 className="w-5 h-5 text-slate-600" />
                <CardTitle>Open Graph (Facebook / LinkedIn)</CardTitle>
              </div>
              <CardDescription>Cómo aparece el sitio al compartirse en redes sociales</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>OG Título</Label>
                <Input
                  value={seo.og_title}
                  onChange={(e) => updateSeo("og_title", e.target.value)}
                  placeholder="SyncStock — Sincronización de Inventario B2B"
                />
              </div>
              <div className="space-y-2">
                <Label>OG Descripción</Label>
                <Textarea
                  value={seo.og_description}
                  onChange={(e) => updateSeo("og_description", e.target.value)}
                  placeholder="Descripción para compartir en redes sociales..."
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>OG Imagen (URL)</Label>
                <Input
                  value={seo.og_image}
                  onChange={(e) => updateSeo("og_image", e.target.value)}
                  placeholder="https://sync-stock.com/og-image.png"
                />
                <p className="text-xs text-slate-500">Tamaño recomendado: 1200×630 px</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>OG Locale</Label>
                  <Input
                    value={seo.og_locale}
                    onChange={(e) => updateSeo("og_locale", e.target.value)}
                    placeholder="es_ES"
                  />
                </div>
                <div className="space-y-2">
                  <Label>OG Site Name</Label>
                  <Input
                    value={seo.og_site_name}
                    onChange={(e) => updateSeo("og_site_name", e.target.value)}
                    placeholder="SyncStock"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Twitter Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Twitter className="w-5 h-5 text-slate-600" />
                <CardTitle>Twitter Card</CardTitle>
              </div>
              <CardDescription>Vista previa al compartir en X (Twitter)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Tipo de Card</Label>
                <select
                  value={seo.twitter_card}
                  onChange={(e) => updateSeo("twitter_card", e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-slate-200 text-sm"
                >
                  <option value="summary_large_image">summary_large_image (imagen grande)</option>
                  <option value="summary">summary (imagen pequeña)</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label>Twitter Título</Label>
                <Input
                  value={seo.twitter_title}
                  onChange={(e) => updateSeo("twitter_title", e.target.value)}
                  placeholder="SyncStock — Sincronización de Inventario B2B"
                />
              </div>
              <div className="space-y-2">
                <Label>Twitter Descripción</Label>
                <Textarea
                  value={seo.twitter_description}
                  onChange={(e) => updateSeo("twitter_description", e.target.value)}
                  placeholder="Descripción para Twitter..."
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Twitter Imagen (URL)</Label>
                <Input
                  value={seo.twitter_image}
                  onChange={(e) => updateSeo("twitter_image", e.target.value)}
                  placeholder="https://sync-stock.com/og-image.png"
                />
              </div>
            </CardContent>
          </Card>

          {/* Save button for SEO tab */}
          <div className="flex justify-end">
            <Button onClick={saveSeo} disabled={savingSeo} className="btn-primary">
              {savingSeo ? (
                <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Guardar SEO
            </Button>
          </div>
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
