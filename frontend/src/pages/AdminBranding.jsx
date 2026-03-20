import { useState, useEffect, useContext, useRef } from "react";
import { api, AuthContext } from "../App";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Palette, Upload, Eye, Save, RefreshCw, Image, Type,
  Paintbrush, CheckCircle, Sparkles, LayoutTemplate, FileText,
  Globe, Server, ShoppingCart, ShoppingBag, Boxes, Building2,
  Package, Trash2, ImageIcon, Info
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ==================== ICON SLOT DEFINITIONS ====================
const ICON_GROUPS = [
  {
    key: "proveedores",
    label: "Proveedores",
    description: "Iconos para los distintos tipos de conexión de proveedores",
    items: [
      { key: "supplier_url", label: "Conexión URL", defaultIcon: Globe, defaultBg: "bg-blue-100", defaultColor: "text-blue-600" },
      { key: "supplier_ftp", label: "Conexión FTP / SFTP", defaultIcon: Server, defaultBg: "bg-indigo-100", defaultColor: "text-indigo-600" },
    ]
  },
  {
    key: "tiendas",
    label: "Tiendas",
    description: "Iconos para las plataformas de tiendas online",
    items: [
      { key: "store_woocommerce", label: "WooCommerce", defaultIcon: ShoppingCart, defaultBg: "bg-purple-100", defaultColor: "text-purple-600" },
      { key: "store_prestashop", label: "PrestaShop", defaultIcon: ShoppingBag, defaultBg: "bg-pink-100", defaultColor: "text-pink-600" },
      { key: "store_shopify", label: "Shopify", defaultIcon: Boxes, defaultBg: "bg-green-100", defaultColor: "text-green-600" },
      { key: "store_wix", label: "Wix eCommerce", defaultIcon: Sparkles, defaultBg: "bg-blue-100", defaultColor: "text-blue-600" },
      { key: "store_magento", label: "Magento", defaultIcon: Globe, defaultBg: "bg-orange-100", defaultColor: "text-orange-600" },
    ]
  },
  {
    key: "marketplaces",
    label: "Marketplaces",
    description: "Iconos para los canales de venta marketplace",
    items: [
      { key: "marketplace_google_merchant", label: "Google Merchant", initials: "GM", defaultBg: "bg-blue-500" },
      { key: "marketplace_facebook_shops", label: "Facebook Shops", initials: "FB", defaultBg: "bg-indigo-600" },
      { key: "marketplace_amazon", label: "Amazon", initials: "AMZ", defaultBg: "bg-orange-500" },
      { key: "marketplace_el_corte_ingles", label: "El Corte Inglés", initials: "ECI", defaultBg: "bg-green-600" },
      { key: "marketplace_miravia", label: "Miravia", initials: "MIR", defaultBg: "bg-pink-500" },
      { key: "marketplace_idealo", label: "Idealo", initials: "IDL", defaultBg: "bg-yellow-500" },
      { key: "marketplace_kelkoo", label: "Kelkoo", initials: "KEL", defaultBg: "bg-red-500" },
      { key: "marketplace_trovaprezzi", label: "Trovaprezzi", initials: "TRV", defaultBg: "bg-purple-500" },
      { key: "marketplace_ebay", label: "eBay", initials: "eBay", defaultBg: "bg-sky-500" },
      { key: "marketplace_zalando", label: "Zalando", initials: "ZAL", defaultBg: "bg-orange-700" },
      { key: "marketplace_pricerunner", label: "PriceRunner", initials: "PR", defaultBg: "bg-teal-500" },
      { key: "marketplace_bing_shopping", label: "Bing Shopping", initials: "BING", defaultBg: "bg-cyan-600" },
    ]
  },
  {
    key: "crm",
    label: "CRM / ERP",
    description: "Iconos para las integraciones CRM y ERP",
    items: [
      { key: "crm_dolibarr", label: "Dolibarr", defaultIcon: Building2, defaultBg: "bg-cyan-100", defaultColor: "text-cyan-700" },
      { key: "crm_odoo", label: "Odoo", defaultIcon: Building2, defaultBg: "bg-purple-100", defaultColor: "text-purple-700" },
      { key: "crm_hubspot", label: "HubSpot", defaultIcon: Building2, defaultBg: "bg-orange-100", defaultColor: "text-orange-600" },
      { key: "crm_salesforce", label: "Salesforce", defaultIcon: Building2, defaultBg: "bg-blue-100", defaultColor: "text-blue-600" },
      { key: "crm_zoho", label: "Zoho CRM", defaultIcon: Building2, defaultBg: "bg-red-100", defaultColor: "text-red-600" },
      { key: "crm_pipedrive", label: "Pipedrive", defaultIcon: Building2, defaultBg: "bg-green-100", defaultColor: "text-green-700" },
      { key: "crm_monday", label: "Monday CRM", defaultIcon: Building2, defaultBg: "bg-indigo-100", defaultColor: "text-indigo-600" },
      { key: "crm_freshsales", label: "Freshsales", defaultIcon: Building2, defaultBg: "bg-orange-100", defaultColor: "text-orange-700" },
    ]
  },
];

const COLOR_SWATCHES = [
  "#4f46e5", "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
  "#ec4899", "#f43f5e", "#ef4444", "#f97316", "#f59e0b",
  "#eab308", "#84cc16", "#22c55e", "#10b981", "#14b8a6",
  "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1", "#475569"
];

const AdminBranding = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const logoInputRef = useRef(null);
  const faviconInputRef = useRef(null);
  const heroInputRef = useRef(null);

  const [branding, setBranding] = useState({
    app_name: "StockHub",
    app_slogan: "Gestión de Catálogos",
    logo_url: null,
    favicon_url: null,
    primary_color: "#4f46e5",
    secondary_color: "#0f172a",
    accent_color: "#10b981",
    footer_text: "",
    theme_preset: "default",
    // Hero section
    hero_image_url: null,
    hero_title: "Gestiona tu inventario de forma inteligente",
    hero_subtitle: "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos.",
    // Page title
    page_title: "StockHub - Gestión de Catálogos"
  });
  const [themePresets, setThemePresets] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState("general");
  const [icons, setIcons] = useState({});
  const [uploadingIcon, setUploadingIcon] = useState(null);

  useEffect(() => {
    if (user?.role !== "superadmin") {
      navigate("/");
      return;
    }
    fetchBranding();
    fetchThemePresets();
    fetchIcons();
  }, [user, navigate]);

  const fetchBranding = async () => {
    try {
      const res = await api.get("/admin/branding");
      setBranding(res.data);
    } catch (error) {
      toast.error("Error al cargar configuración");
    } finally {
      setLoading(false);
    }
  };

  const fetchThemePresets = async () => {
    try {
      const res = await api.get("/admin/theme-presets");
      setThemePresets(res.data);
    } catch (error) {
      // handled silently
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/admin/branding", branding);
      toast.success("Configuración guardada");
    } catch (error) {
      toast.error("Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("El archivo debe ser una imagen");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/admin/branding/upload-logo", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setBranding(prev => ({ ...prev, logo_url: res.data.logo_url }));
      toast.success("Logo subido");
    } catch (error) {
      toast.error("Error al subir logo");
    } finally {
      setUploading(false);
    }
  };

  const handleFaviconUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("El archivo debe ser una imagen");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/admin/branding/upload-favicon", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setBranding(prev => ({ ...prev, favicon_url: res.data.favicon_url }));
      toast.success("Favicon subido");
    } catch (error) {
      toast.error("Error al subir favicon");
    } finally {
      setUploading(false);
    }
  };

  const handleHeroUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("El archivo debe ser una imagen");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/admin/branding/upload-hero", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setBranding(prev => ({ ...prev, hero_image_url: res.data.hero_image_url }));
      toast.success("Imagen Hero subida");
    } catch (error) {
      toast.error("Error al subir imagen Hero");
    } finally {
      setUploading(false);
    }
  };

  const fetchIcons = async () => {
    try {
      const res = await api.get("/admin/icons");
      setIcons(res.data.icons || {});
    } catch (error) {
      // handled silently
    }
  };

  const handleIconUpload = async (iconKey, file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("El archivo debe ser una imagen");
      return;
    }
    if (file.size > 500 * 1024) {
      toast.error("El archivo no puede superar 500KB");
      return;
    }
    setUploadingIcon(iconKey);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post(`/admin/icons/upload/${iconKey}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setIcons(prev => ({ ...prev, [iconKey]: res.data.icon_url }));
      toast.success("Icono actualizado");
    } catch (error) {
      toast.error("Error al subir el icono");
    } finally {
      setUploadingIcon(null);
    }
  };

  const handleIconDelete = async (iconKey) => {
    try {
      await api.delete(`/admin/icons/${iconKey}`);
      setIcons(prev => {
        const next = { ...prev };
        delete next[iconKey];
        return next;
      });
      toast.success("Icono eliminado, se usará el predeterminado");
    } catch (error) {
      toast.error("Error al eliminar el icono");
    }
  };

  const applyPreset = async (presetKey) => {
    try {
      const res = await api.post(`/admin/branding/apply-preset/${presetKey}`);
      setBranding(prev => ({
        ...prev,
        ...res.data.branding
      }));
      toast.success(`Tema "${themePresets[presetKey]?.name}" aplicado`);
    } catch (error) {
      toast.error("Error al aplicar tema");
    }
  };

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
            Personalización
          </h1>
          <p className="text-slate-500">Configura la apariencia de tu aplicación</p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="btn-primary" data-testid="save-branding-btn">
          {saving ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
          Guardar Cambios
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-slate-100 p-1 flex-wrap gap-1">
          <TabsTrigger value="general" className="data-[state=active]:bg-white">
            <Type className="w-4 h-4 mr-2" />
            General
          </TabsTrigger>
          <TabsTrigger value="images" className="data-[state=active]:bg-white">
            <Image className="w-4 h-4 mr-2" />
            Imágenes
          </TabsTrigger>
          <TabsTrigger value="hero" className="data-[state=active]:bg-white">
            <LayoutTemplate className="w-4 h-4 mr-2" />
            Hero
          </TabsTrigger>
          <TabsTrigger value="colors" className="data-[state=active]:bg-white">
            <Palette className="w-4 h-4 mr-2" />
            Colores
          </TabsTrigger>
          <TabsTrigger value="icons" className="data-[state=active]:bg-white">
            <ImageIcon className="w-4 h-4 mr-2" />
            Iconos
          </TabsTrigger>
          <TabsTrigger value="preview" className="data-[state=active]:bg-white">
            <Eye className="w-4 h-4 mr-2" />
            Vista Previa
          </TabsTrigger>
        </TabsList>

        {/* General Tab */}
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Type className="w-5 h-5 text-purple-600" />
                Información General
              </CardTitle>
              <CardDescription>Nombre y textos de la aplicación</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="app_name">Nombre de la Aplicación</Label>
                  <Input
                    id="app_name"
                    value={branding.app_name}
                    onChange={(e) => setBranding({ ...branding, app_name: e.target.value })}
                    placeholder="Mi App"
                    className="input-base"
                    data-testid="app-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="app_slogan">Slogan / Descripción corta</Label>
                  <Input
                    id="app_slogan"
                    value={branding.app_slogan}
                    onChange={(e) => setBranding({ ...branding, app_slogan: e.target.value })}
                    placeholder="Gestión de productos"
                    className="input-base"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="page_title">Título de Página (Pestaña del navegador)</Label>
                <Input
                  id="page_title"
                  value={branding.page_title}
                  onChange={(e) => setBranding({ ...branding, page_title: e.target.value })}
                  placeholder="Mi App - Descripción"
                  className="input-base"
                  data-testid="page-title-input"
                />
                <p className="text-xs text-slate-500">Este texto aparece en la pestaña del navegador</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="footer_text">Texto del Footer</Label>
                <Input
                  id="footer_text"
                  value={branding.footer_text}
                  onChange={(e) => setBranding({ ...branding, footer_text: e.target.value })}
                  placeholder="© 2025 Mi Empresa. Todos los derechos reservados."
                  className="input-base"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Images Tab */}
        <TabsContent value="images" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Image className="w-5 h-5 text-purple-600" />
                  Logo
                </CardTitle>
                <CardDescription>Logo principal de la aplicación (recomendado: 200x50px)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
                  {branding.logo_url ? (
                    <div className="space-y-4">
                      <div className="bg-slate-100 p-4 rounded-lg inline-block">
                        <img
                          src={branding.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${branding.logo_url}` : branding.logo_url}
                          alt="Logo"
                          className="max-h-16 max-w-full object-contain"
                        />
                      </div>
                      <div className="flex justify-center gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => logoInputRef.current?.click()}
                          disabled={uploading}
                        >
                          <Upload className="w-4 h-4 mr-2" />
                          Cambiar
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => setBranding({ ...branding, logo_url: null })}
                        >
                          Eliminar
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="w-16 h-16 bg-slate-100 rounded-lg flex items-center justify-center mx-auto">
                        <Image className="w-8 h-8 text-slate-400" />
                      </div>
                      <Button 
                        variant="outline" 
                        onClick={() => logoInputRef.current?.click()}
                        disabled={uploading}
                      >
                        {uploading ? (
                          <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Upload className="w-4 h-4 mr-2" />
                        )}
                        Subir Logo
                      </Button>
                    </div>
                  )}
                  <input 
                    ref={logoInputRef}
                    type="file" 
                    accept="image/*" 
                    className="hidden" 
                    onChange={handleLogoUpload}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  Favicon
                </CardTitle>
                <CardDescription>Icono del navegador (recomendado: 32x32px o .ico)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
                  {branding.favicon_url ? (
                    <div className="space-y-4">
                      <div className="bg-slate-100 p-4 rounded-lg inline-block">
                        <img
                          src={branding.favicon_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${branding.favicon_url}` : branding.favicon_url}
                          alt="Favicon"
                          className="w-8 h-8 object-contain"
                        />
                      </div>
                      <div className="flex justify-center gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => faviconInputRef.current?.click()}
                          disabled={uploading}
                        >
                          <Upload className="w-4 h-4 mr-2" />
                          Cambiar
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => setBranding({ ...branding, favicon_url: null })}
                        >
                          Eliminar
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto">
                        <Sparkles className="w-6 h-6 text-slate-400" />
                      </div>
                      <Button 
                        variant="outline" 
                        onClick={() => faviconInputRef.current?.click()}
                        disabled={uploading}
                      >
                        {uploading ? (
                          <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Upload className="w-4 h-4 mr-2" />
                        )}
                        Subir Favicon
                      </Button>
                    </div>
                  )}
                  <input 
                    ref={faviconInputRef}
                    type="file" 
                    accept="image/*,.ico" 
                    className="hidden" 
                    onChange={handleFaviconUpload}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Hero Tab */}
        <TabsContent value="hero" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LayoutTemplate className="w-5 h-5 text-purple-600" />
                Página de Inicio de Sesión / Registro
              </CardTitle>
              <CardDescription>
                Personaliza la imagen de fondo y el texto que aparece en las páginas de login y registro
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Hero Image Upload */}
              <div className="space-y-3">
                <Label>Imagen de Fondo (Hero)</Label>
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-6">
                  {branding.hero_image_url ? (
                    <div className="space-y-4">
                      <div className="relative rounded-lg overflow-hidden" style={{ height: "200px" }}>
                        <img 
                          src={branding.hero_image_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${branding.hero_image_url}` : branding.hero_image_url}
                          alt="Hero" 
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                          <div className="text-center text-white p-4">
                            <h3 className="text-xl font-bold mb-2">{branding.hero_title}</h3>
                            <p className="text-sm opacity-80">{branding.hero_subtitle}</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-center gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => heroInputRef.current?.click()}
                          disabled={uploading}
                        >
                          <Upload className="w-4 h-4 mr-2" />
                          Cambiar Imagen
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => setBranding({ ...branding, hero_image_url: null })}
                        >
                          Usar Predeterminada
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center space-y-4">
                      <div className="w-20 h-20 bg-slate-100 rounded-lg flex items-center justify-center mx-auto">
                        <LayoutTemplate className="w-10 h-10 text-slate-400" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-500 mb-3">
                          Se está usando la imagen predeterminada de Unsplash
                        </p>
                        <Button 
                          variant="outline" 
                          onClick={() => heroInputRef.current?.click()}
                          disabled={uploading}
                        >
                          {uploading ? (
                            <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Upload className="w-4 h-4 mr-2" />
                          )}
                          Subir Imagen Personalizada
                        </Button>
                      </div>
                      <p className="text-xs text-slate-400">Recomendado: 1920x1080px o mayor, formato JPG/PNG</p>
                    </div>
                  )}
                  <input 
                    ref={heroInputRef}
                    type="file" 
                    accept="image/*" 
                    className="hidden" 
                    onChange={handleHeroUpload}
                  />
                </div>
              </div>

              {/* Hero Text */}
              <div className="grid gap-4">
                <div className="space-y-2">
                  <Label htmlFor="hero_title">Título del Hero</Label>
                  <Input
                    id="hero_title"
                    value={branding.hero_title}
                    onChange={(e) => setBranding({ ...branding, hero_title: e.target.value })}
                    placeholder="Gestiona tu inventario de forma inteligente"
                    className="input-base"
                    data-testid="hero-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hero_subtitle">Subtítulo del Hero</Label>
                  <Textarea
                    id="hero_subtitle"
                    value={branding.hero_subtitle}
                    onChange={(e) => setBranding({ ...branding, hero_subtitle: e.target.value })}
                    placeholder="Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos."
                    className="input-base resize-none"
                    rows={3}
                    data-testid="hero-subtitle-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Colors Tab */}
        <TabsContent value="colors" className="space-y-6">
          {/* Theme Presets */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Paintbrush className="w-5 h-5 text-purple-600" />
                Temas Predefinidos
              </CardTitle>
              <CardDescription>Selecciona un tema para aplicar colores automáticamente</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {Object.entries(themePresets).map(([key, preset]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className={`p-3 rounded-lg border-2 transition-all hover:scale-105 ${
                      branding.theme_preset === key 
                        ? "border-purple-500 bg-purple-50" 
                        : "border-slate-200 hover:border-slate-300"
                    }`}
                    data-testid={`theme-preset-${key}`}
                  >
                    <div className="flex gap-1 mb-2 justify-center">
                      <div 
                        className="w-5 h-5 rounded-full" 
                        style={{ backgroundColor: preset.primary_color }}
                      />
                      <div 
                        className="w-5 h-5 rounded-full" 
                        style={{ backgroundColor: preset.secondary_color }}
                      />
                      <div 
                        className="w-5 h-5 rounded-full" 
                        style={{ backgroundColor: preset.accent_color }}
                      />
                    </div>
                    <p className="text-xs font-medium text-slate-700 truncate">{preset.name}</p>
                    {branding.theme_preset === key && (
                      <CheckCircle className="w-4 h-4 text-purple-600 mx-auto mt-1" />
                    )}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Custom Colors */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5 text-purple-600" />
                Colores Personalizados
              </CardTitle>
              <CardDescription>Selecciona colores personalizados o usa el selector</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Primary Color */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  Color Primario
                  <div 
                    className="w-6 h-6 rounded border border-slate-300" 
                    style={{ backgroundColor: branding.primary_color }}
                  />
                </Label>
                <div className="flex items-center gap-4">
                  <Input
                    type="color"
                    value={branding.primary_color}
                    onChange={(e) => setBranding({ ...branding, primary_color: e.target.value, theme_preset: "custom" })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={branding.primary_color}
                    onChange={(e) => setBranding({ ...branding, primary_color: e.target.value, theme_preset: "custom" })}
                    placeholder="#4f46e5"
                    className="input-base w-28"
                  />
                  <div className="flex flex-wrap gap-1">
                    {COLOR_SWATCHES.slice(0, 10).map(color => (
                      <button
                        key={color}
                        onClick={() => setBranding({ ...branding, primary_color: color, theme_preset: "custom" })}
                        className={`w-6 h-6 rounded transition-transform hover:scale-110 ${
                          branding.primary_color === color ? "ring-2 ring-offset-2 ring-purple-500" : ""
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Secondary Color */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  Color Secundario
                  <div 
                    className="w-6 h-6 rounded border border-slate-300" 
                    style={{ backgroundColor: branding.secondary_color }}
                  />
                </Label>
                <div className="flex items-center gap-4">
                  <Input
                    type="color"
                    value={branding.secondary_color}
                    onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value, theme_preset: "custom" })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={branding.secondary_color}
                    onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value, theme_preset: "custom" })}
                    placeholder="#0f172a"
                    className="input-base w-28"
                  />
                </div>
              </div>

              {/* Accent Color */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2">
                  Color de Acento
                  <div 
                    className="w-6 h-6 rounded border border-slate-300" 
                    style={{ backgroundColor: branding.accent_color }}
                  />
                </Label>
                <div className="flex items-center gap-4">
                  <Input
                    type="color"
                    value={branding.accent_color}
                    onChange={(e) => setBranding({ ...branding, accent_color: e.target.value, theme_preset: "custom" })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={branding.accent_color}
                    onChange={(e) => setBranding({ ...branding, accent_color: e.target.value, theme_preset: "custom" })}
                    placeholder="#10b981"
                    className="input-base w-28"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Icons Tab */}
        <TabsContent value="icons" className="space-y-6">
          {/* Specification info card */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">Especificaciones de iconos</p>
                  <ul className="space-y-0.5 list-disc list-inside">
                    <li><strong>Tamaño recomendado:</strong> 64×64 px o 128×128 px (cuadrado)</li>
                    <li><strong>Formato:</strong> PNG, SVG o WebP — fondo transparente recomendado</li>
                    <li><strong>Tamaño máximo:</strong> 500 KB por archivo</li>
                    <li>Si no se sube un icono personalizado, se usará el icono predeterminado del sistema</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {ICON_GROUPS.map(group => (
            <Card key={group.key}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-purple-600" />
                  {group.label}
                </CardTitle>
                <CardDescription>{group.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {group.items.map(item => {
                    const customUrl = icons[item.key];
                    const inputRef = { current: null };
                    const DefaultIcon = item.defaultIcon;

                    return (
                      <div key={item.key} className="border border-slate-200 rounded-lg p-4 flex flex-col items-center gap-3 text-center hover:border-purple-200 transition-colors">
                        {/* Icon preview */}
                        <div className={`w-16 h-16 rounded-xl flex items-center justify-center overflow-hidden ${!customUrl ? (item.defaultBg || "bg-slate-100") : "bg-slate-50 border border-slate-200"}`}>
                          {customUrl ? (
                            <img
                              src={customUrl.startsWith("/") ? `${BACKEND_URL}${customUrl}` : customUrl}
                              alt={item.label}
                              className="w-12 h-12 object-contain"
                            />
                          ) : DefaultIcon ? (
                            <DefaultIcon className={`w-8 h-8 ${item.defaultColor || "text-slate-500"}`} />
                          ) : (
                            <span className="text-white font-bold text-xs leading-tight">{item.initials}</span>
                          )}
                        </div>

                        {/* Label */}
                        <div>
                          <p className="text-sm font-medium text-slate-900">{item.label}</p>
                          {customUrl ? (
                            <span className="text-xs text-emerald-600 font-medium">Personalizado</span>
                          ) : (
                            <span className="text-xs text-slate-400">Predeterminado</span>
                          )}
                        </div>

                        {/* Buttons */}
                        <div className="flex gap-2 w-full">
                          <label className="flex-1 cursor-pointer">
                            <div className="flex items-center justify-center gap-1 text-xs px-2 py-1.5 rounded border border-slate-200 hover:border-purple-300 hover:bg-purple-50 transition-colors">
                              {uploadingIcon === item.key ? (
                                <RefreshCw className="w-3 h-3 animate-spin" />
                              ) : (
                                <Upload className="w-3 h-3" />
                              )}
                              {customUrl ? "Cambiar" : "Subir"}
                            </div>
                            <input
                              type="file"
                              accept="image/png,image/svg+xml,image/webp,image/jpeg"
                              className="hidden"
                              disabled={uploadingIcon === item.key}
                              onChange={(e) => handleIconUpload(item.key, e.target.files?.[0])}
                            />
                          </label>
                          {customUrl && (
                            <button
                              onClick={() => handleIconDelete(item.key)}
                              className="flex items-center justify-center px-2 py-1.5 rounded border border-rose-200 text-rose-500 hover:bg-rose-50 transition-colors"
                              title="Restaurar predeterminado"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-purple-600" />
                Vista Previa
              </CardTitle>
              <CardDescription>Así se verá tu aplicación con la configuración actual</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden shadow-lg">
                {/* Preview Header */}
                <div 
                  className="p-4 flex items-center gap-3"
                  style={{ backgroundColor: branding.primary_color }}
                >
                  {branding.logo_url ? (
                    <img src={branding.logo_url.startsWith('/') ? `${process.env.REACT_APP_BACKEND_URL}${branding.logo_url}` : branding.logo_url} alt="Logo" className="h-8" />
                  ) : (
                    <div className="w-10 h-10 bg-white/20 rounded flex items-center justify-center">
                      <span className="text-white font-bold">{branding.app_name?.charAt(0) || "S"}</span>
                    </div>
                  )}
                  <div>
                    <h3 className="text-white font-bold">{branding.app_name || "StockHub"}</h3>
                    <p className="text-white/70 text-sm">{branding.app_slogan || "Gestión de Catálogos"}</p>
                  </div>
                </div>

                {/* Preview Content */}
                <div className="p-6 bg-slate-50">
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="bg-white p-4 rounded-lg shadow-sm">
                        <div className="w-8 h-8 rounded mb-2" style={{ backgroundColor: branding.accent_color }} />
                        <div className="h-3 bg-slate-200 rounded w-3/4 mb-2" />
                        <div className="h-2 bg-slate-100 rounded w-1/2" />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <button 
                      className="px-4 py-2 rounded text-white font-medium"
                      style={{ backgroundColor: branding.primary_color }}
                    >
                      Botón Primario
                    </button>
                    <button 
                      className="px-4 py-2 rounded font-medium border-2"
                      style={{ borderColor: branding.primary_color, color: branding.primary_color }}
                    >
                      Botón Secundario
                    </button>
                  </div>
                </div>

                {/* Preview Footer */}
                <div 
                  className="p-4 text-center text-sm"
                  style={{ backgroundColor: branding.secondary_color, color: "rgba(255,255,255,0.7)" }}
                >
                  {branding.footer_text || "© 2025 Tu Empresa"}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminBranding;
