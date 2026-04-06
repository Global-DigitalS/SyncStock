import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Download,
  ShoppingCart,
  CheckCircle2,
  FileDown,
  ExternalLink
} from "lucide-react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

const platforms = [
  {
    id: "prestashop",
    name: "PrestaShop",
    description: "Exporta tu catálogo en formato compatible con PrestaShop 1.6+",
    color: "bg-pink-500",
    icon: "🛒"
  },
  {
    id: "woocommerce",
    name: "WooCommerce",
    description: "Archivo CSV listo para importar en WooCommerce (WordPress)",
    color: "bg-purple-600",
    icon: "🏪"
  },
  {
    id: "shopify",
    name: "Shopify",
    description: "Formato CSV optimizado para la importación en Shopify",
    color: "bg-green-600",
    icon: "🛍️"
  }
];

const Export = () => {
  const [catalogCount, setCatalogCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);

  useEffect(() => {
    const fetchCatalogCount = async () => {
      try {
        const res = await api.get("/catalog?active_only=true");
        setCatalogCount(res.data.length);
      } catch (error) {
        // handled silently
      } finally {
        setLoading(false);
      }
    };
    fetchCatalogCount();
  }, []);

  const handleExport = async (platformId) => {
    if (catalogCount === 0) {
      toast.error("No hay productos activos en tu catálogo");
      return;
    }

    setExporting(platformId);
    try {
      const response = await api.post("/export", { platform: platformId }, {
        responseType: "blob"
      });

      // Create download link
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Get filename from headers or generate one
      const contentDisposition = response.headers["content-disposition"];
      let filename = `catalog_${platformId}_${new Date().toISOString().split("T")[0]}.csv`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, "");
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(`Archivo ${filename} descargado correctamente`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al exportar el catálogo");
    } finally {
      setExporting(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Exportar Catálogo
        </h1>
        <p className="text-slate-500">
          Descarga tu catálogo en formato CSV para tu tienda online
        </p>
      </div>

      {/* Status Card */}
      <Card className="border-slate-200 mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-indigo-100 rounded-sm flex items-center justify-center">
                <ShoppingCart className="w-6 h-6 text-indigo-600" strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Productos activos en tu catálogo</p>
                <p className="text-3xl font-bold font-mono text-slate-900">{catalogCount.toLocaleString()}</p>
              </div>
            </div>
            {catalogCount > 0 && (
              <Badge className="badge-success flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" strokeWidth={1.5} />
                Listo para exportar
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Platforms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {platforms.map((platform) => (
          <Card
            key={platform.id}
            className="border-slate-200 hover:shadow-lg transition-all duration-200"
            data-testid={`export-${platform.id}`}
          >
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className={`w-12 h-12 ${platform.color} rounded-sm flex items-center justify-center text-2xl`}>
                  {platform.icon}
                </div>
              </div>
              <CardTitle className="text-xl mt-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {platform.name}
              </CardTitle>
              <CardDescription className="text-slate-500">
                {platform.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => handleExport(platform.id)}
                disabled={exporting !== null || catalogCount === 0}
                className="w-full btn-primary"
                data-testid={`export-btn-${platform.id}`}
              >
                {exporting === platform.id ? (
                  <>
                    <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                    Exportando...
                  </>
                ) : (
                  <>
                    <FileDown className="w-4 h-4 mr-2" strokeWidth={1.5} />
                    Descargar CSV
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Help Section */}
      <Card className="border-slate-200 mt-8">
        <CardHeader>
          <CardTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Guía de importación
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <span className="w-6 h-6 bg-pink-100 text-pink-600 rounded-full flex items-center justify-center text-sm font-bold">P</span>
                PrestaShop
              </h4>
              <ol className="text-sm text-slate-600 space-y-1 ml-8">
                <li>1. Ve a Catálogo → Productos</li>
                <li>2. Haz clic en "Importar"</li>
                <li>3. Selecciona el archivo CSV</li>
                <li>4. Verifica el mapeo de campos</li>
              </ol>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <span className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-sm font-bold">W</span>
                WooCommerce
              </h4>
              <ol className="text-sm text-slate-600 space-y-1 ml-8">
                <li>1. Ve a Productos → Todos los productos</li>
                <li>2. Haz clic en "Importar"</li>
                <li>3. Sube el archivo CSV</li>
                <li>4. Ejecuta el importador</li>
              </ol>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <span className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-bold">S</span>
                Shopify
              </h4>
              <ol className="text-sm text-slate-600 space-y-1 ml-8">
                <li>1. Ve a Productos</li>
                <li>2. Haz clic en "Importar"</li>
                <li>3. Añade tu archivo CSV</li>
                <li>4. Revisa y confirma</li>
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Export;
