import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Switch } from "../ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import RichTextEditor from "./RichTextEditor";
import { AlertCircle, Save, Loader } from "lucide-react";

const PageForm = ({ page = null, onSubmit, loading = false }) => {
  const [formData, setFormData] = useState({
    slug: "",
    title: "",
    page_type: "page",
    hero_title: "",
    hero_subtitle: "",
    hero_image_url: "",
    content: JSON.stringify([
      {
        type: "paragraph",
        children: [{ text: "" }],
      },
    ]),
    meta_description: "",
    meta_keywords: "",
    is_published: false,
    is_public: true,
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (page) {
      setFormData({
        slug: page.slug || "",
        title: page.title || "",
        page_type: page.page_type || "page",
        hero_title: page.hero_section?.title || "",
        hero_subtitle: page.hero_section?.subtitle || "",
        hero_image_url: page.hero_section?.image_url || "",
        content:
          typeof page.content === "string"
            ? page.content
            : JSON.stringify(page.content || []),
        meta_description: page.meta_description || "",
        meta_keywords:
          typeof page.meta_keywords === "string"
            ? page.meta_keywords
            : page.meta_keywords?.join(", ") || "",
        is_published: page.is_published || false,
        is_public: page.is_public !== false,
      });
    }
  }, [page]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.slug.trim()) {
      newErrors.slug = "El slug es requerido";
    }

    if (!formData.title.trim()) {
      newErrors.title = "El título es requerido";
    }

    try {
      const contentData = JSON.parse(formData.content);
      if (!contentData || contentData.length === 0) {
        newErrors.content = "El contenido es requerido";
      }
    } catch {
      newErrors.content = "El contenido debe ser JSON válido";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
  };

  const handleSwitchChange = (name) => {
    setFormData((prev) => ({
      ...prev,
      [name]: !prev[name],
    }));
  };

  const handleContentChange = (newContent) => {
    setFormData((prev) => ({
      ...prev,
      content: newContent,
    }));
    if (errors.content) {
      setErrors((prev) => ({
        ...prev,
        content: "",
      }));
    }
  };

  const handleSlugChange = (e) => {
    const { value } = e.target;
    const slugifiedValue = value
      .toLowerCase()
      .replace(/[^\w\-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/--+/g, "-");
    setFormData((prev) => ({
      ...prev,
      slug: slugifiedValue,
    }));
    if (errors.slug) {
      setErrors((prev) => ({
        ...prev,
        slug: "",
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData = {
      slug: formData.slug,
      title: formData.title,
      page_type: formData.page_type,
      hero_section: {
        title: formData.hero_title,
        subtitle: formData.hero_subtitle,
        image_url: formData.hero_image_url,
      },
      content: JSON.parse(formData.content),
      meta_description: formData.meta_description,
      meta_keywords: formData.meta_keywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k),
      is_published: formData.is_published,
      is_public: formData.is_public,
    };

    await onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {Object.keys(errors).length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800 mb-2">
                  Hay errores en el formulario
                </h3>
                <ul className="text-sm text-red-700 space-y-1">
                  {Object.entries(errors).map(([field, error]) => (
                    <li key={field}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="hero">Sección Hero</TabsTrigger>
          <TabsTrigger value="seo">SEO</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>Información General</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="slug">Slug (URL)*</Label>
                <Input
                  id="slug"
                  name="slug"
                  value={formData.slug}
                  onChange={handleSlugChange}
                  placeholder="mi-pagina"
                  disabled={!!page}
                  className={errors.slug ? "border-red-500" : ""}
                />
                {errors.slug && (
                  <p className="text-sm text-red-600">{errors.slug}</p>
                )}
                <p className="text-xs text-slate-500">
                  Se puede cambiar automáticamente a formato URL
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="title">Título*</Label>
                <Input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Título de la página"
                  className={errors.title ? "border-red-500" : ""}
                />
                {errors.title && (
                  <p className="text-sm text-red-600">{errors.title}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="page_type">Tipo de página</Label>
                <select
                  id="page_type"
                  name="page_type"
                  value={formData.page_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="page">Página estándar</option>
                  <option value="landing">Página de destino</option>
                  <option value="blog">Blog</option>
                  <option value="showcase">Vitrina</option>
                </select>
              </div>

              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="published" className="cursor-pointer">
                      Publicada
                    </Label>
                    <p className="text-xs text-slate-500">
                      La página será visible en el sitio
                    </p>
                  </div>
                  <Switch
                    id="published"
                    checked={formData.is_published}
                    onCheckedChange={() => handleSwitchChange("is_published")}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="public" className="cursor-pointer">
                      Pública
                    </Label>
                    <p className="text-xs text-slate-500">
                      Acceso sin autenticación
                    </p>
                  </div>
                  <Switch
                    id="public"
                    checked={formData.is_public}
                    onCheckedChange={() => handleSwitchChange("is_public")}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hero">
          <Card>
            <CardHeader>
              <CardTitle>Sección Hero (Encabezado)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hero_title">Título del hero</Label>
                <Input
                  id="hero_title"
                  name="hero_title"
                  value={formData.hero_title}
                  onChange={handleInputChange}
                  placeholder="Título principal"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="hero_subtitle">Subtítulo del hero</Label>
                <Textarea
                  id="hero_subtitle"
                  name="hero_subtitle"
                  value={formData.hero_subtitle}
                  onChange={handleInputChange}
                  placeholder="Descripción corta"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="hero_image_url">URL de imagen</Label>
                <Input
                  id="hero_image_url"
                  name="hero_image_url"
                  value={formData.hero_image_url}
                  onChange={handleInputChange}
                  placeholder="https://ejemplo.com/imagen.jpg"
                  type="url"
                />
                {formData.hero_image_url && (
                  <div className="mt-2 relative w-full h-48 bg-slate-100 rounded overflow-hidden">
                    <img
                      src={formData.hero_image_url}
                      alt="Preview"
                      className="w-full h-full object-cover"
                      onError={() => {
                        console.error("Image load error");
                      }}
                    />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="seo">
          <Card>
            <CardHeader>
              <CardTitle>SEO y Metadatos</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="meta_description">Meta descripción</Label>
                <Textarea
                  id="meta_description"
                  name="meta_description"
                  value={formData.meta_description}
                  onChange={handleInputChange}
                  placeholder="Descripción para buscadores (máx 160 caracteres)"
                  rows={2}
                  maxLength={160}
                />
                <p className="text-xs text-slate-500">
                  {formData.meta_description.length}/160 caracteres
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="meta_keywords">Palabras clave (separadas por coma)</Label>
                <Textarea
                  id="meta_keywords"
                  name="meta_keywords"
                  value={formData.meta_keywords}
                  onChange={handleInputChange}
                  placeholder="palabra1, palabra2, palabra3"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Contenido Principal*</CardTitle>
        </CardHeader>
        <CardContent>
          <RichTextEditor
            value={formData.content}
            onChange={handleContentChange}
            label="Editor de contenido"
          />
          {errors.content && (
            <p className="text-sm text-red-600 mt-2">{errors.content}</p>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-4 sticky bottom-0 bg-white pt-4 border-t">
        <Button
          type="submit"
          disabled={loading}
          className="gap-2"
        >
          {loading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              {page ? "Actualizar" : "Crear"} página
            </>
          )}
        </Button>
      </div>
    </form>
  );
};

export default PageForm;
