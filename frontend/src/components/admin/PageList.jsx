import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Edit2, Trash2, Plus, Eye, EyeOff, Globe, Lock } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import EmptyState from "../shared/EmptyState";

const PageList = ({ pages, loading, onDelete, onPublish }) => {
  const navigate = useNavigate();
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const handleEdit = (pageId) => {
    navigate(`/admin/pages/${pageId}`);
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await onDelete(deleteId);
      setDeleteId(null);
    } catch (error) {
      console.error("Error deleting page:", error);
    } finally {
      setDeleting(false);
    }
  };

  const handlePublishToggle = async (pageId, currentPublished) => {
    try {
      await onPublish(pageId, !currentPublished);
    } catch (error) {
      console.error("Error updating publication status:", error);
    }
  };

  if (loading && pages.length === 0) {
    return (
      <Card>
        <CardContent className="pt-8">
          <div className="text-center py-8">
            <div className="inline-block">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
            <p className="text-slate-600 mt-2">Cargando páginas...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (pages.length === 0) {
    return (
      <EmptyState
        icon={Globe}
        title="No hay páginas"
        description="Comienza creando tu primera página para el sitio web."
        action={
          <Button onClick={() => navigate("/admin/pages")}>
            <Plus className="w-4 h-4 mr-2" />
            Crear primera página
          </Button>
        }
      />
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Páginas</CardTitle>
            <p className="text-sm text-slate-600 mt-1">
              Total: {pages.length} página(s)
            </p>
          </div>
          <Button onClick={() => navigate("/admin/pages")}>
            <Plus className="w-4 h-4 mr-2" />
            Nueva página
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Título</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-center">Publicada</TableHead>
                  <TableHead className="text-center">Pública</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pages.map((page) => (
                  <TableRow key={page.id}>
                    <TableCell className="font-medium">
                      {page.title}
                    </TableCell>
                    <TableCell className="text-slate-600 text-sm">
                      <code className="bg-slate-100 px-2 py-1 rounded">
                        {page.slug}
                      </code>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {page.page_type || "Página"}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <button
                        onClick={() =>
                          handlePublishToggle(page.id, page.is_published)
                        }
                        className="inline-flex items-center justify-center p-2 hover:bg-slate-100 rounded"
                        title={
                          page.is_published
                            ? "Despublicar"
                            : "Publicar"
                        }
                      >
                        {page.is_published ? (
                          <Eye className="w-4 h-4 text-green-600" />
                        ) : (
                          <EyeOff className="w-4 h-4 text-slate-400" />
                        )}
                      </button>
                    </TableCell>
                    <TableCell className="text-center">
                      {page.is_public ? (
                        <Globe className="w-4 h-4 text-blue-600 inline" />
                      ) : (
                        <Lock className="w-4 h-4 text-slate-400 inline" />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(page.id)}
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteId(page.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar página</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. La página será eliminada permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex gap-3 justify-end">
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleting ? "Eliminando..." : "Eliminar"}
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default PageList;
