import { toast } from "sonner";

/**
 * Extrae el mensaje de error de una respuesta de Axios y muestra un toast.
 *
 * @param {Error}  err             - El error capturado en el catch.
 * @param {string} fallbackMessage - Mensaje por defecto si la API no devuelve detalle.
 * @returns {string} El mensaje de error extraído.
 *
 * Uso:
 *   try {
 *     await api.post("/products", data);
 *   } catch (err) {
 *     handleApiError(err, "Error al guardar el producto");
 *   }
 *
 * También puedes suprimir el toast si solo quieres el mensaje:
 *   const msg = handleApiError(err, "Error", { silent: true });
 */
export function handleApiError(err, fallbackMessage = "Ha ocurrido un error", { silent = false } = {}) {
  const message =
    err?.response?.data?.detail ||
    err?.response?.data?.message ||
    err?.message ||
    fallbackMessage;

  if (!silent) {
    toast.error(message);
  }

  return message;
}
