import { useState, useEffect } from "react";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../components/ui/dialog";
import { Checkbox } from "../components/ui/checkbox";
import {
  Folder, File, FolderUp, RefreshCw, ChevronRight, FileArchive,
  FileSpreadsheet, Plus, Trash2, Save
} from "lucide-react";

// Get file icon based on extension
const getFileIcon = (filename, isDir) => {
  if (isDir) return <Folder className="w-4 h-4 text-amber-500" />;
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "zip") return <FileArchive className="w-4 h-4 text-purple-500" />;
  if (["csv", "xlsx", "xls"].includes(ext)) return <FileSpreadsheet className="w-4 h-4 text-emerald-500" />;
  return <File className="w-4 h-4 text-slate-400" />;
};

// Format file size
const formatSize = (bytes) => {
  if (!bytes) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const FTP_FILE_ROLES = [
  { value: "products", label: "Productos (principal)" },
  { value: "stock", label: "Stock" },
  { value: "prices", label: "Precios" },
  { value: "prices_qb", label: "Precios QB" },
  { value: "kit", label: "Kits" },
  { value: "min_qty", label: "Cantidad mínima" },
];

const FtpFileBrowser = ({
  open,
  onOpenChange,
  supplier,
  onSave
}) => {
  const [ftpFiles, setFtpFiles] = useState([]);
  const [ftpCurrentPath, setFtpCurrentPath] = useState("/");
  const [ftpLoading, setFtpLoading] = useState(false);
  const [selectedPaths, setSelectedPaths] = useState([]);
  const [ftpPathHistory, setFtpPathHistory] = useState(["/"]);

  useEffect(() => {
    if (open && supplier?.ftp_host) {
      browseFtp("/");
      // Load existing paths
      if (supplier.ftp_paths && supplier.ftp_paths.length > 0) {
        setSelectedPaths(supplier.ftp_paths);
      } else if (supplier.ftp_path) {
        setSelectedPaths([{
          path: supplier.ftp_path,
          role: "products",
          auto_latest: false,
          separator: ";",
          header_row: 1,
          label: supplier.ftp_path.split("/").pop()
        }]);
      } else {
        setSelectedPaths([]);
      }
    }
  }, [open, supplier]);

  const browseFtp = async (path) => {
    if (!supplier?.ftp_host) return;
    setFtpLoading(true);
    try {
      const res = await api.post("/suppliers/browse-ftp", {
        host: supplier.ftp_host,
        port: supplier.ftp_port || 21,
        username: supplier.ftp_username || "",
        password: supplier.ftp_password || "",
        mode: supplier.ftp_mode || "passive",
        path: path
      });
      setFtpFiles(res.data.files || []);
      setFtpCurrentPath(path);
      if (!ftpPathHistory.includes(path)) {
        setFtpPathHistory([...ftpPathHistory, path]);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al explorar FTP");
    } finally {
      setFtpLoading(false);
    }
  };

  const navigateUp = () => {
    if (ftpCurrentPath === "/") return;
    const parts = ftpCurrentPath.split("/").filter(Boolean);
    parts.pop();
    const parentPath = parts.length === 0 ? "/" : "/" + parts.join("/");
    browseFtp(parentPath);
  };

  const handleFileClick = (file) => {
    if (file.is_dir) {
      browseFtp(file.path);
    } else {
      // Add to selected paths if not already there
      const alreadySelected = selectedPaths.some(p => p.path === file.path);
      if (!alreadySelected) {
        // Auto-detect role from filename
        const fname = file.name.toLowerCase();
        let autoRole = "products";
        if (fname.includes("stock")) autoRole = "stock";
        else if (fname.includes("price") && fname.includes("qb")) autoRole = "prices_qb";
        else if (fname.includes("price")) autoRole = "prices";
        else if (fname.includes("kit")) autoRole = "kit";
        else if (fname.includes("minqty") || fname.includes("min_qty")) autoRole = "min_qty";
        
        setSelectedPaths([...selectedPaths, {
          path: file.path,
          role: autoRole,
          auto_latest: false,
          separator: ";",
          header_row: 1,
          label: file.name
        }]);
        toast.success(`Archivo añadido: ${file.name}`);
      }
    }
  };

  const removeSelectedPath = (index) => {
    setSelectedPaths(selectedPaths.filter((_, i) => i !== index));
  };

  const updateSelectedPath = (index, field, value) => {
    setSelectedPaths(selectedPaths.map((p, i) => 
      i === index ? { ...p, [field]: value } : p
    ));
  };

  const handleSave = async () => {
    try {
      await api.put(`/suppliers/${supplier.id}`, {
        ftp_paths: selectedPaths,
        ftp_path: selectedPaths[0]?.path || supplier.ftp_path
      });
      toast.success("Configuración de archivos FTP guardada");
      onSave?.();
      onOpenChange(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
            Explorador de Archivos FTP
          </DialogTitle>
          <DialogDescription>
            Selecciona y configura los archivos de catálogo para {supplier?.name}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-1 overflow-hidden">
          {/* File Browser Panel */}
          <div className="flex-1 border-r flex flex-col">
            {/* Breadcrumb */}
            <div className="p-3 border-b bg-slate-50 flex items-center gap-2">
              <Button
                variant="ghost" size="sm"
                onClick={navigateUp}
                disabled={ftpCurrentPath === "/" || ftpLoading}
              >
                <FolderUp className="w-4 h-4" />
              </Button>
              <div className="flex items-center gap-1 text-sm text-slate-600 flex-1 overflow-hidden">
                <span className="text-slate-400">/</span>
                {ftpCurrentPath.split("/").filter(Boolean).map((part, i, arr) => (
                  <span key={i} className="flex items-center">
                    <span className="truncate max-w-[100px]">{part}</span>
                    {i < arr.length - 1 && <ChevronRight className="w-3 h-3 text-slate-400 mx-1" />}
                  </span>
                ))}
              </div>
              <Button
                variant="ghost" size="sm"
                onClick={() => browseFtp(ftpCurrentPath)}
                disabled={ftpLoading}
                data-testid="refresh-ftp"
              >
                <RefreshCw className={`w-4 h-4 ${ftpLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-y-auto">
              {ftpLoading ? (
                <div className="flex items-center justify-center h-full">
                  <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
                </div>
              ) : ftpFiles.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-500">
                  <Folder className="w-10 h-10 text-slate-300 mb-2" />
                  <p>Carpeta vacía</p>
                </div>
              ) : (
                <div className="divide-y">
                  {ftpFiles.map((file, idx) => {
                    const isSelected = selectedPaths.some(p => p.path === file.path);
                    return (
                      <div
                        key={idx}
                        onClick={() => handleFileClick(file)}
                        className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                          isSelected ? "bg-indigo-50" : "hover:bg-slate-50"
                        }`}
                        data-testid={`ftp-file-${file.name}`}
                      >
                        {getFileIcon(file.name, file.is_dir)}
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm truncate ${isSelected ? "font-medium text-indigo-700" : "text-slate-700"}`}>
                            {file.name}
                          </p>
                        </div>
                        <span className="text-xs text-slate-400">{formatSize(file.size)}</span>
                        {isSelected && !file.is_dir && (
                          <Badge className="bg-indigo-100 text-indigo-700 border-0 text-xs">Seleccionado</Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Selected Files Panel */}
          <div className="w-96 flex flex-col bg-slate-50">
            <div className="p-3 border-b">
              <h3 className="font-semibold text-slate-900 text-sm">
                Archivos seleccionados ({selectedPaths.length})
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {selectedPaths.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  <Plus className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p>Haz clic en un archivo para seleccionarlo</p>
                </div>
              ) : (
                selectedPaths.map((pathConfig, idx) => (
                  <div key={idx} className="bg-white rounded-lg border border-slate-200 p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-600 truncate flex-1">
                        {pathConfig.label || pathConfig.path}
                      </span>
                      <Button
                        variant="ghost" size="sm" className="h-6 w-6 p-0 text-rose-500"
                        onClick={() => removeSelectedPath(idx)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                    <Select
                      value={pathConfig.role}
                      onValueChange={(v) => updateSelectedPath(idx, "role", v)}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FTP_FILE_ROLES.map(r => (
                          <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label className="text-[10px] text-slate-500">Separador</Label>
                        <Input
                          value={pathConfig.separator || ";"}
                          onChange={(e) => updateSelectedPath(idx, "separator", e.target.value)}
                          className="h-7 text-xs"
                        />
                      </div>
                      <div>
                        <Label className="text-[10px] text-slate-500">Fila encabezado</Label>
                        <Input
                          type="number"
                          value={pathConfig.header_row || 1}
                          onChange={(e) => updateSelectedPath(idx, "header_row", parseInt(e.target.value) || 1)}
                          className="h-7 text-xs"
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id={`auto-latest-${idx}`}
                        checked={pathConfig.auto_latest || false}
                        onCheckedChange={(v) => updateSelectedPath(idx, "auto_latest", v)}
                      />
                      <Label htmlFor={`auto-latest-${idx}`} className="text-xs text-slate-600 cursor-pointer">
                        Auto-seleccionar archivo más reciente
                      </Label>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="px-6 py-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSave} className="btn-primary" data-testid="save-ftp-config">
            <Save className="w-4 h-4 mr-2" />
            Guardar configuración
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default FtpFileBrowser;
