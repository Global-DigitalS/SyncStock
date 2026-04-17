import { useState } from "react";
import { Code, Eye, EyeOff } from "lucide-react";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

const RichTextEditor = ({ value, onChange, label }) => {
  const [jsonView, setJsonView] = useState(false);
  const [editorValue, setEditorValue] = useState(() => {
    try {
      if (typeof value === "string" && value) {
        return value;
      }
      return JSON.stringify(
        [
          {
            type: "paragraph",
            children: [{ text: "" }],
          },
        ],
        null,
        2
      );
    } catch {
      return JSON.stringify(
        [
          {
            type: "paragraph",
            children: [{ text: "" }],
          },
        ],
        null,
        2
      );
    }
  });

  const handleChange = (newValue) => {
    setEditorValue(newValue);
    onChange(newValue);
  };

  const insertElement = (type) => {
    try {
      const currentData = JSON.parse(editorValue);
      const newElement = {
        type,
        children: [{ text: type === "paragraph" ? "Nuevo párrafo" : "Nuevo contenido" }],
      };
      const updatedData = [...currentData, newElement];
      const newValue = JSON.stringify(updatedData, null, 2);
      setEditorValue(newValue);
      onChange(newValue);
    } catch (error) {
      console.error("Error inserting element:", error);
    }
  };

  const validateJSON = () => {
    try {
      JSON.parse(editorValue);
      return true;
    } catch {
      return false;
    }
  };

  const isValid = validateJSON();

  return (
    <div className="space-y-2">
      {label && <Label>{label}</Label>}
      <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
        <Tabs defaultValue="editor" className="w-full">
          <TabsList className="border-b border-slate-200 rounded-none bg-slate-50 px-3">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="preview">Vista previa</TabsTrigger>
            <TabsTrigger value="code">JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="space-y-3 p-4">
            <div className="space-y-2">
              <p className="text-sm text-slate-600">
                Haz clic en un botón para insertar elementos de contenido
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => insertElement("paragraph")}
                >
                  + Párrafo
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => insertElement("heading-one")}
                >
                  + H1
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => insertElement("heading-two")}
                >
                  + H2
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => insertElement("block-quote")}
                >
                  + Cita
                </Button>
              </div>
            </div>
            <Textarea
              value={editorValue}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Edita el contenido en formato JSON..."
              className={`font-mono text-sm min-h-96 ${
                !isValid ? "border-red-500" : ""
              }`}
            />
            {!isValid && (
              <p className="text-sm text-red-600">
                JSON no válido. Verifica el formato.
              </p>
            )}
          </TabsContent>

          <TabsContent value="preview" className="p-4">
            <div className="space-y-4">
              <p className="text-sm text-slate-600">
                Vista previa del contenido renderizado
              </p>
              {isValid ? (
                <ContentPreview content={JSON.parse(editorValue)} />
              ) : (
                <div className="bg-amber-50 border border-amber-200 rounded p-4 text-amber-800 text-sm">
                  El JSON no es válido. Corrige los errores para ver la vista previa.
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="code" className="space-y-3 p-4">
            <div className="space-y-2">
              <p className="text-sm text-slate-600">Estructura JSON del contenido</p>
              <Textarea
                value={editorValue}
                onChange={(e) => handleChange(e.target.value)}
                placeholder="{"type": "paragraph", "children": [{"text": ""}]}"
                className={`font-mono text-xs min-h-96 ${
                  !isValid ? "border-red-500" : ""
                }`}
              />
            </div>
            {!isValid && (
              <p className="text-sm text-red-600">
                JSON no válido. Verifica la sintaxis.
              </p>
            )}
          </TabsContent>
        </Tabs>
      </div>
      <p className="text-xs text-slate-500">
        El contenido se almacena en formato JSON. Cada elemento debe tener un campo "type" y "children".
      </p>
    </div>
  );
};

const ContentPreview = ({ content }) => {
  if (!Array.isArray(content)) return null;

  return (
    <div className="prose prose-sm max-w-none">
      {content.map((element, idx) => {
        const text = element.children
          ?.map((child) => child.text || "")
          .join("") || "";

        switch (element.type) {
          case "heading-one":
            return (
              <h1 key={idx} className="text-3xl font-bold my-4">
                {text}
              </h1>
            );
          case "heading-two":
            return (
              <h2 key={idx} className="text-2xl font-bold my-3">
                {text}
              </h2>
            );
          case "block-quote":
            return (
              <blockquote
                key={idx}
                className="border-l-4 border-slate-300 pl-4 italic text-slate-600 my-2"
              >
                {text}
              </blockquote>
            );
          case "paragraph":
          default:
            return (
              <p key={idx} className="my-2">
                {text}
              </p>
            );
        }
      })}
    </div>
  );
};

export default RichTextEditor;
