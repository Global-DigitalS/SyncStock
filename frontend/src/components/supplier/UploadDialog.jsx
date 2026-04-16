import { useState, useRef } from "react";
import { FileUp } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog";

export function UploadDialog({ open, onOpenChange, supplierName, uploading, onUpload }) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) onUpload(e.dataTransfer.files[0]);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "Manrope, sans-serif" }}>Importar Productos</DialogTitle>
          <DialogDescription>Sube un archivo con los productos de {supplierName}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div
            className={`upload-zone ${dragActive ? "dragging" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls,.xml"
              onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])}
              className="hidden"
              data-testid="file-input"
            />
            {uploading ? (
              <div className="flex flex-col items-center">
                <div className="spinner mb-3"></div>
                <p className="text-slate-600">Importando productos...</p>
              </div>
            ) : (
              <>
                <FileUp className="w-12 h-12 text-slate-400 mx-auto mb-3" strokeWidth={1.5} />
                <p className="text-slate-600 font-medium mb-1">
                  Arrastra tu archivo aquí o haz clic para seleccionar
                </p>
                <p className="text-sm text-slate-400">Formatos soportados: CSV, XLSX, XLS, XML</p>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
