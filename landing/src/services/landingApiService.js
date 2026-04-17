import axios from "axios";

/**
 * Cliente de API público para la landing page.
 * Proporciona acceso a endpoints de branding y páginas públicas.
 * No requiere autenticación (endpoints públicos).
 */

const API_BASE_URL = (process.env.REACT_APP_API_URL || "").replace(/\/$/, "");

// Crear instancia de Axios sin credenciales (endpoints públicos)
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor para manejo de errores
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.message);
    return Promise.reject(error);
  }
);

/**
 * Obtiene la configuración de branding de la landing page.
 * GET /api/branding
 *
 * @returns {Promise<Object>} Objeto con configuración de branding
 * @throws {Error} Si la solicitud falla
 */
export async function getBranding() {
  try {
    const response = await apiClient.get("/api/branding");
    return response.data;
  } catch (error) {
    console.error("Error obteniendo branding:", error);
    throw error;
  }
}

/**
 * Obtiene la lista de todas las páginas públicas.
 * GET /api/pages/public
 *
 * @returns {Promise<Array>} Array de páginas públicas
 * @throws {Error} Si la solicitud falla
 */
export async function getPublicPages() {
  try {
    const response = await apiClient.get("/api/pages/public");
    // Asegurar que la respuesta es un array
    return Array.isArray(response.data) ? response.data : response.data.pages || [];
  } catch (error) {
    console.error("Error obteniendo páginas públicas:", error);
    throw error;
  }
}

/**
 * Obtiene una página pública específica por slug.
 * GET /api/pages/public/{slug}
 *
 * @param {string} slug - Identificador único de la página (ej. "acerca-de", "blog")
 * @returns {Promise<Object>} Objeto con datos de la página
 * @throws {Error} Si la solicitud falla o la página no existe (404)
 */
export async function getPageBySlug(slug) {
  try {
    if (!slug || typeof slug !== "string") {
      throw new Error("El slug debe ser un string válido");
    }
    const response = await apiClient.get(`/api/pages/public/${slug}`);
    return response.data;
  } catch (error) {
    console.error(`Error obteniendo página con slug "${slug}":`, error);
    throw error;
  }
}

/**
 * Obtiene el contenido de branding y páginas de forma simultánea.
 * Útil para inicializaciones que requieren ambos datos.
 *
 * @returns {Promise<Object>} Objeto con estructura { branding, pages, errors }
 */
export async function getLandingData() {
  try {
    const [brandingRes, pagesRes] = await Promise.allSettled([
      getBranding(),
      getPublicPages(),
    ]);

    const branding =
      brandingRes.status === "fulfilled"
        ? brandingRes.value
        : null;
    const pages =
      pagesRes.status === "fulfilled"
        ? pagesRes.value
        : [];

    return {
      branding,
      pages,
      errors: {
        brandingError:
          brandingRes.status === "rejected"
            ? brandingRes.reason
            : null,
        pagesError:
          pagesRes.status === "rejected"
            ? pagesRes.reason
            : null,
      },
    };
  } catch (error) {
    console.error("Error obteniendo datos de landing:", error);
    throw error;
  }
}

export default {
  getBranding,
  getPublicPages,
  getPageBySlug,
  getLandingData,
};
