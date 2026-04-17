import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_BASE_URL}/api`;

// Instancia Axios específica para pageService
const apiClient = axios.create({
  baseURL: API,
  withCredentials: true,
  timeout: 30000,
});

/**
 * Obtiene todas las páginas públicas (sin autenticación).
 * @param {number} skip - Número de registros a saltar (paginación)
 * @param {number} limit - Número máximo de registros
 * @returns {Promise<Array>} Lista de páginas públicas
 */
export const listPublicPages = async (skip = 0, limit = 100) => {
  try {
    const response = await apiClient.get("/pages/public", {
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Obtiene una página pública por slug (sin autenticación).
 * @param {string} slug - Slug de la página
 * @returns {Promise<Object>} Objeto de página
 */
export const getPublicPage = async (slug) => {
  try {
    const response = await apiClient.get(`/pages/public/${slug}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Obtiene todas las páginas (requiere autenticación como Admin o SuperAdmin).
 * @param {number} skip - Número de registros a saltar
 * @param {number} limit - Número máximo de registros
 * @param {string|null} pageType - Filtrar por tipo de página
 * @param {string|null} search - Buscar en título o slug
 * @returns {Promise<Array>} Lista de páginas
 */
export const listPages = async (skip = 0, limit = 100, pageType = null, search = null) => {
  try {
    const params = { skip, limit };
    if (pageType) params.page_type = pageType;
    if (search) params.search = search;

    const response = await apiClient.get("/pages", { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Obtiene una página por ID (requiere autenticación como Admin o SuperAdmin).
 * @param {string} pageId - ID de la página
 * @returns {Promise<Object>} Objeto de página
 */
export const getPage = async (pageId) => {
  try {
    const response = await apiClient.get(`/pages/${pageId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Crea una nueva página (requiere autenticación como SuperAdmin).
 * @param {Object} pageData - Datos de la página
 * @param {string} pageData.slug - Slug único
 * @param {string} pageData.title - Título de la página
 * @param {string} pageData.page_type - Tipo de página
 * @param {Object} pageData.hero_section - Sección hero (opcional)
 * @param {Array} pageData.content - Contenido de la página
 * @param {string} pageData.meta_description - Descripción meta (SEO)
 * @param {Array} pageData.meta_keywords - Palabras clave meta (SEO)
 * @param {boolean} pageData.is_published - Si está publicada
 * @param {boolean} pageData.is_public - Si es pública
 * @returns {Promise<Object>} Página creada
 */
export const createPage = async (pageData) => {
  try {
    const response = await apiClient.post("/pages", pageData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza una página por ID (requiere autenticación como Admin o SuperAdmin).
 * @param {string} pageId - ID de la página
 * @param {Object} pageData - Datos a actualizar (solo campos a cambiar)
 * @returns {Promise<Object>} Página actualizada
 */
export const updatePage = async (pageId, pageData) => {
  try {
    const response = await apiClient.put(`/pages/${pageId}`, pageData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Elimina una página por ID (requiere autenticación como SuperAdmin).
 * @param {string} pageId - ID de la página a eliminar
 * @returns {Promise<void>}
 */
export const deletePage = async (pageId) => {
  try {
    await apiClient.delete(`/pages/${pageId}`);
  } catch (error) {
    throw error;
  }
};

/**
 * Publica o despublica una página (requiere autenticación como Admin o SuperAdmin).
 * @param {string} pageId - ID de la página
 * @param {boolean} published - True para publicar, False para despublicar
 * @returns {Promise<Object>} Página actualizada
 */
export const publishPage = async (pageId, published = true) => {
  try {
    const response = await apiClient.put(`/pages/${pageId}/publish`, null, {
      params: { published },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Publica o despublica múltiples páginas (requiere autenticación como Admin o SuperAdmin).
 * @param {Array<string>} pageIds - IDs de páginas a actualizar
 * @param {boolean} published - True para publicar, False para despublicar
 * @returns {Promise<Object>} Respuesta con número de modificadas
 */
export const bulkPublishPages = async (pageIds, published = true) => {
  try {
    const response = await apiClient.post("/pages/bulk/publish", pageIds, {
      params: { published },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};
