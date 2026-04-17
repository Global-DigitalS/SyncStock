import { useEffect, useState } from "react";
import { usePageManager } from "../../hooks/usePageManager";
import PageList from "../../components/admin/PageList";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { FileText, BarChart3 } from "lucide-react";

const PageManager = () => {
  const pageManager = usePageManager();
  const [selectedType, setSelectedType] = useState(null);

  useEffect(() => {
    pageManager.loadPages();
  }, []);

  const filteredPages = selectedType
    ? pageManager.pages.filter((page) => page.page_type === selectedType)
    : pageManager.pages;

  const pageTypes = [
    { value: null, label: "Todas las páginas", count: pageManager.pages.length },
    { value: "page", label: "Páginas", count: pageManager.pages.filter((p) => p.page_type === "page").length },
    { value: "landing", label: "Landings", count: pageManager.pages.filter((p) => p.page_type === "landing").length },
    { value: "blog", label: "Blog", count: pageManager.pages.filter((p) => p.page_type === "blog").length },
    { value: "showcase", label: "Vitrinas", count: pageManager.pages.filter((p) => p.page_type === "showcase").length },
  ];

  const publishedCount = pageManager.pages.filter((p) => p.is_published).length;
  const publicCount = pageManager.pages.filter((p) => p.is_public).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg">
          <FileText className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Gestor de Páginas</h1>
          <p className="text-slate-600">Gestiona todas las páginas del sitio web</p>
        </div>
      </div>

      {pageManager.pages.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Total de páginas</p>
                  <p className="text-3xl font-bold">{pageManager.pages.length}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Publicadas</p>
                  <p className="text-3xl font-bold">{publishedCount}</p>
                </div>
                <div className="w-8 h-8 bg-green-100 rounded text-center">
                  <span className="text-green-600 text-lg">✓</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Públicas</p>
                  <p className="text-3xl font-bold">{publicCount}</p>
                </div>
                <div className="w-8 h-8 bg-purple-100 rounded text-center">
                  <span className="text-purple-600 text-lg">🌐</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {pageManager.pages.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Filtrar por tipo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {pageTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSelectedType(type.value)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition ${
                    selectedType === type.value
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {type.label}
                  <span className="ml-2 inline-flex items-center justify-center w-6 h-6 text-xs rounded-full bg-white/20">
                    {type.count}
                  </span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <PageList
        pages={filteredPages}
        loading={pageManager.loading}
        onDelete={pageManager.deletePage}
        onPublish={pageManager.publishPage}
      />

      {pageManager.error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-700 text-sm">
              Error: {pageManager.error.message}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PageManager;
