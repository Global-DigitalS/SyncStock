import { useState } from "react";
import {
  FolderOpen,
  FileArchive,
  FileText,
  FileSpreadsheet,
  RefreshCw,
  CheckCircle,
  ChevronRight,
  FolderTree,
  CheckSquare,
  Square,
  PlusCircle
} from "lucide-react";
import { Button } from "../ui/button";
import SelectedFilesList from "./SelectedFilesList";

const FtpFileBrowser = ({
  files,
  currentPath,
  selectedFiles,
  stats,
  browsing,
  listingAll,
  canListAll,
  onBrowse,
  onListAll,
  onAddFile,
  onAddMultipleFiles,
  onRemoveFile,
  onUpdateFileRole,
  formatFileSize
}) => {
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const [checkedFiles, setCheckedFiles] = useState([]);
  
  const navigateUp = () => {
    const parent = currentPath.split("/").slice(0, -1).join("/") || "/";
    onBrowse(parent);
  };
  
  const toggleFileCheck = (file) => {
    if (checkedFiles.some(f => f.path === file.path)) {
      setCheckedFiles(checkedFiles.filter(f => f.path !== file.path));
    } else {
      setCheckedFiles([...checkedFiles, file]);
    }
  };
  
  const selectAllSupported = () => {
    const supportedFiles = files.filter(f => !f.is_dir && f.is_supported && !selectedFiles.some(s => s.path === f.path));
    setCheckedFiles(supportedFiles);
  };
  
  const clearChecked = () => {
    setCheckedFiles([]);
  };
  
  const addCheckedFiles = () => {
    if (checkedFiles.length > 0) {
      if (onAddMultipleFiles) {
        onAddMultipleFiles(checkedFiles);
      } else {
        checkedFiles.forEach(file => onAddFile(file));
      }
      setCheckedFiles([]);
      setMultiSelectMode(false);
    }
  };
  
  const supportedCount = files.filter(f => !f.is_dir && f.is_supported && !selectedFiles.some(s => s.path === f.path)).length;

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden" data-testid="ftp-browser">
      {/* Header */}
      <div className="bg-slate-50 px-4 py-3 flex items-center justify-between border-b border-slate-200">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-indigo-600" />
          <span className="text-sm font-semibold text-slate-800">Explorador FTP</span>
          {selectedFiles.length > 0 && (
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              {selectedFiles.length} archivos
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Multi-select toggle */}
          {files.length > 0 && supportedCount > 0 && (
            <Button
              type="button"
              size="sm"
              variant={multiSelectMode ? "default" : "outline"}
              onClick={() => {
                setMultiSelectMode(!multiSelectMode);
                if (multiSelectMode) setCheckedFiles([]);
              }}
              className={`text-xs h-7 ${multiSelectMode ? "bg-indigo-600 hover:bg-indigo-700" : ""}`}
              data-testid="ftp-multi-select-btn"
            >
              <CheckSquare className="w-3 h-3 mr-1" />
              Múltiple
            </Button>
          )}
          {canListAll && (
            <Button
              type="button" 
              size="sm" 
              variant="outline"
              onClick={onListAll}
              disabled={listingAll || browsing}
              className="text-xs h-7"
              title="Buscar todos los archivos en subcarpetas"
              data-testid="ftp-list-all-btn"
            >
              {listingAll ? (
                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              ) : (
                <FolderTree className="w-3 h-3 mr-1" />
              )}
              Buscar en carpetas
            </Button>
          )}
          <Button
            type="button" 
            size="sm" 
            variant="outline"
            onClick={() => onBrowse(currentPath)}
            disabled={browsing}
            className="text-xs h-7"
            data-testid="ftp-browse-btn"
          >
            {browsing ? (
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <FolderOpen className="w-3 h-3 mr-1" />
            )}
            Explorar
          </Button>
        </div>
      </div>

      {/* Multi-select actions bar */}
      {multiSelectMode && files.length > 0 && (
        <div className="px-4 py-2 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs text-indigo-700 font-medium">
              {checkedFiles.length} de {supportedCount} archivos seleccionados
            </span>
            <button 
              type="button"
              onClick={selectAllSupported}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Seleccionar todos
            </button>
            {checkedFiles.length > 0 && (
              <button 
                type="button"
                onClick={clearChecked}
                className="text-xs text-slate-500 hover:text-slate-700"
              >
                Limpiar
              </button>
            )}
          </div>
          <Button
            type="button"
            size="sm"
            onClick={addCheckedFiles}
            disabled={checkedFiles.length === 0}
            className="h-7 text-xs bg-indigo-600 hover:bg-indigo-700 text-white"
            data-testid="ftp-add-selected-btn"
          >
            <PlusCircle className="w-3 h-3 mr-1" />
            Añadir {checkedFiles.length > 0 ? `(${checkedFiles.length})` : ""}
          </Button>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="px-4 py-2 bg-slate-50/50 border-b border-slate-100 flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <FolderOpen className="w-3.5 h-3.5 text-amber-500" />
            <span>{stats.total_dirs} carpetas</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            <span>{stats.total_files} archivos</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-600">
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>{stats.supported_files} soportados</span>
          </div>
        </div>
      )}

      {/* Selected Files */}
      <SelectedFilesList 
        files={selectedFiles}
        onRemove={onRemoveFile}
        onUpdateRole={onUpdateFileRole}
      />

      {/* File List */}
      {files.length > 0 && (
        <div className="max-h-64 overflow-y-auto">
          {/* Current path */}
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex items-center gap-1">
            <span className="text-xs text-slate-500">Ruta:</span>
            <span className="text-xs font-mono text-slate-700">{currentPath}</span>
            {currentPath !== "/" && (
              <button 
                type="button" 
                onClick={navigateUp}
                className="text-xs text-indigo-600 hover:text-indigo-700 ml-2 font-medium"
              >
                ↑ Subir
              </button>
            )}
          </div>
          
          {files.map((file) => {
            const isSelected = selectedFiles.some(f => f.path === file.path);
            const isChecked = checkedFiles.some(f => f.path === file.path);
            const isSupported = file.is_supported;
            const canCheck = multiSelectMode && !file.is_dir && isSupported && !isSelected;
            
            return (
              <div 
                key={file.path}
                className={`flex items-center gap-3 px-3 py-2 border-b border-slate-100 hover:bg-slate-50 transition-colors ${
                  file.is_dir ? "cursor-pointer" : ""
                } ${isSelected ? "bg-indigo-50" : ""} ${isChecked ? "bg-indigo-100" : ""} ${!file.is_dir && !isSupported ? "opacity-50" : ""}`}
                onClick={() => {
                  if (file.is_dir) {
                    onBrowse(file.path);
                  } else if (canCheck) {
                    toggleFileCheck(file);
                  }
                }}
                data-testid={`ftp-file-${file.name}`}
              >
                {/* Checkbox for multi-select mode */}
                {multiSelectMode && !file.is_dir && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (isSupported && !isSelected) toggleFileCheck(file);
                    }}
                    className={`flex-shrink-0 ${!isSupported || isSelected ? "opacity-30 cursor-not-allowed" : "cursor-pointer"}`}
                    disabled={!isSupported || isSelected}
                  >
                    {isChecked ? (
                      <CheckSquare className="w-4 h-4 text-indigo-600" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                )}
                
                {/* Icon */}
                {file.is_dir ? (
                  <FolderOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
                ) : file.name.endsWith('.zip') ? (
                  <FileArchive className="w-4 h-4 text-purple-500 flex-shrink-0" />
                ) : file.extension === 'csv' || file.extension === 'xlsx' || file.extension === 'xls' ? (
                  <FileSpreadsheet className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                ) : (
                  <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                )}
                
                {/* Name */}
                <span className={`text-sm flex-1 truncate ${
                  file.is_dir ? "font-medium text-slate-800" : "text-slate-700 font-mono text-xs"
                }`}>
                  {file.name}
                </span>
                
                {/* File details */}
                {!file.is_dir && (
                  <>
                    {file.extension && (
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        isSupported ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                      }`}>
                        {file.extension.toUpperCase()}
                      </span>
                    )}
                    <span className="text-xs text-slate-400 min-w-[60px] text-right">
                      {file.size_formatted || formatFileSize?.(file.size) || ""}
                    </span>
                    {!multiSelectMode && (
                      isSelected ? (
                        <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 min-w-[70px]">
                          <CheckCircle className="w-3 h-3" /> Añadido
                        </span>
                      ) : isSupported ? (
                        <button 
                          type="button" 
                          onClick={(e) => { e.stopPropagation(); onAddFile(file); }}
                          className="text-xs bg-indigo-600 text-white px-2.5 py-1 rounded-md hover:bg-indigo-700 transition-colors font-medium min-w-[70px]"
                          data-testid={`add-file-${file.name}`}
                        >
                          Añadir
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400 min-w-[70px]">No soportado</span>
                      )
                    )}
                    {multiSelectMode && isSelected && (
                      <span className="text-xs text-emerald-600 font-medium flex items-center gap-1 min-w-[70px]">
                        <CheckCircle className="w-3 h-3" /> Añadido
                      </span>
                    )}
                  </>
                )}
                
                {file.is_dir && (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Empty states */}
      {files.length === 0 && !browsing && (
        <div className="py-8 text-center text-sm text-slate-400">
          Pulsa "Explorar" para ver los archivos del servidor FTP
        </div>
      )}
      {browsing && (
        <div className="py-8 text-center">
          <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-400">Conectando al FTP...</p>
        </div>
      )}
    </div>
  );
};

export default FtpFileBrowser;
