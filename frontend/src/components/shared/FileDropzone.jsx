import { useState, useRef } from "react";
import { Upload, FileUp } from "lucide-react";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

const FileDropzone = ({
  onFileDrop,
  accept = ".csv,.xlsx,.xls,.xml",
  multiple = false,
  uploading = false,
  className
}) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = multiple ? Array.from(e.dataTransfer.files) : [e.dataTransfer.files[0]];
      onFileDrop(files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const files = multiple ? Array.from(e.target.files) : [e.target.files[0]];
      onFileDrop(files);
    }
  };

  return (
    <div
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
        dragActive 
          ? "border-indigo-500 bg-indigo-50" 
          : "border-slate-200 hover:border-indigo-300",
        className
      )}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      data-testid="file-dropzone"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        className="hidden"
      />
      
      <Upload className={cn(
        "w-12 h-12 mx-auto mb-4",
        dragActive ? "text-indigo-500" : "text-slate-400"
      )} />
      
      <p className="text-slate-600 mb-2">
        Arrastra archivos aquí o{" "}
        <button
          type="button"
          className="text-indigo-600 hover:underline font-medium"
          onClick={() => fileInputRef.current?.click()}
        >
          selecciona
        </button>
      </p>
      
      <p className="text-xs text-slate-500">
        Formatos soportados: CSV, XLSX, XLS, XML
      </p>
      
      {uploading && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <div className="spinner" />
          <span className="text-sm text-indigo-600">Subiendo archivo...</span>
        </div>
      )}
    </div>
  );
};

export default FileDropzone;
