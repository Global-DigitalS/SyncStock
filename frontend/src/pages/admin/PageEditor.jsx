import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { usePageManager } from "../../hooks/usePageManager";
import PageForm from "../../components/admin/PageForm";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { ArrowLeft, FileText, Loader } from "lucide-react";

const PageEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const pageManager = usePageManager();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load page if editing
  useEffect(() => {
    if (id) {
      pageManager.loadPage(id);
    }
  }, [id]);

  const isEditing = !!id;
  const isLoading = isEditing && pageManager.loading && !pageManager.currentPage;

  const handleSubmit = async (formData) => {
    setIsSubmitting(true);
    try {
      if (isEditing) {
        await pageManager.updatePage(id, formData);
        toast.success("Página actualizada exitosamente");
      } else {
        const newPage = await pageManager.createPage(formData);
        toast.success("Página creada exitosamente");
        navigate(`/admin/pages/${newPage.id}`);
      }
      // Navigate back after a brief delay to show success message
      setTimeout(() => {
        navigate("/admin/pages-list");
      }, 500);
    } catch (error) {
      console.error("Error submitting form:", error);
      // Error toast is already shown by the hook
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
          <p className="text-slate-600 mt-4">Cargando página...</p>
        </div>
      </div>
    );
  }

  if (isEditing && pageManager.error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/admin/pages-list")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </Button>
        </div>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-700">
              No se pudo cargar la página. {pageManager.error.message}
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => navigate("/admin/pages-list")}
            >
              Ir al listado
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/admin/pages-list")}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al listado
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg">
          <FileText className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">
            {isEditing ? "Editar página" : "Crear nueva página"}
          </h1>
          <p className="text-slate-600">
            {isEditing
              ? "Modifica los detalles de la página"
              : "Rellena el formulario para crear una nueva página"}
          </p>
        </div>
      </div>

      <PageForm
        page={pageManager.currentPage}
        onSubmit={handleSubmit}
        loading={isSubmitting}
      />
    </div>
  );
};

export default PageEditor;
