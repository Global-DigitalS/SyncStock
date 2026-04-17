import { useState, useCallback, useRef, useEffect } from "react";
import { toast } from "sonner";
import * as pageService from "../services/pageService";

/**
 * Custom hook para gestionar páginas del CMS.
 *
 * Proporciona:
 * - Estado: pages (array), currentPage (objeto), loading, error
 * - Métodos: loadPages, loadPage, createPage, updatePage, deletePage
 * - Manejo automático de estados de carga y error
 * - Actualización local del estado después de operaciones
 *
 * @returns {Object} Objeto con estado y métodos para gestión de páginas
 *
 * Uso:
 *   const pageManager = usePageManager();
 *   // Cargar todas las páginas
 *   pageManager.loadPages();
 *   // Crear una página
 *   await pageManager.createPage({ slug: "nueva", title: "Nueva Página", ... });
 */
export function usePageManager() {
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  // Limpieza al desmontar para evitar memory leaks
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const setStateIfMounted = useCallback((setter, value) => {
    if (mountedRef.current) {
      setter(value);
    }
  }, []);

  /**
   * Carga todas las páginas (requiere autenticación como Admin o SuperAdmin).
   * @param {Object} options - Opciones de carga
   * @param {number} options.skip - Número de registros a saltar
   * @param {number} options.limit - Número máximo de registros
   * @param {string|null} options.pageType - Filtrar por tipo de página
   * @param {string|null} options.search - Buscar en título o slug
   */
  const loadPages = useCallback(async (options = {}) => {
    const { skip = 0, limit = 100, pageType = null, search = null } = options;
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const data = await pageService.listPages(skip, limit, pageType, search);
      setStateIfMounted(setPages, data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al cargar las páginas";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [setStateIfMounted]);

  /**
   * Carga una página específica por ID (requiere autenticación como Admin o SuperAdmin).
   * @param {string} pageId - ID de la página
   */
  const loadPage = useCallback(async (pageId) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const data = await pageService.getPage(pageId);
      setStateIfMounted(setCurrentPage, data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al cargar la página";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [setStateIfMounted]);

  /**
   * Crea una nueva página (requiere autenticación como SuperAdmin).
   * @param {Object} pageData - Datos de la página
   * @returns {Promise<Object>} Página creada
   */
  const createPage = useCallback(async (pageData) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const newPage = await pageService.createPage(pageData);
      setStateIfMounted(setPages, (prev) => [...prev, newPage]);
      toast.success("Página creada exitosamente");
      return newPage;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al crear la página";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
      throw err;
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [setStateIfMounted]);

  /**
   * Actualiza una página existente (requiere autenticación como Admin o SuperAdmin).
   * @param {string} pageId - ID de la página
   * @param {Object} pageData - Datos a actualizar
   * @returns {Promise<Object>} Página actualizada
   */
  const updatePage = useCallback(async (pageId, pageData) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const updatedPage = await pageService.updatePage(pageId, pageData);
      // Actualizar en el array pages si existe
      setStateIfMounted(setPages, (prev) =>
        prev.map((p) => (p.id === pageId ? updatedPage : p))
      );
      // Actualizar currentPage si es la página actual
      if (currentPage?.id === pageId) {
        setStateIfMounted(setCurrentPage, updatedPage);
      }
      toast.success("Página actualizada exitosamente");
      return updatedPage;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al actualizar la página";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
      throw err;
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [currentPage?.id, setStateIfMounted]);

  /**
   * Elimina una página (requiere autenticación como SuperAdmin).
   * @param {string} pageId - ID de la página a eliminar
   */
  const deletePage = useCallback(async (pageId) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      await pageService.deletePage(pageId);
      // Eliminar del array pages
      setStateIfMounted(setPages, (prev) => prev.filter((p) => p.id !== pageId));
      // Limpiar currentPage si es la eliminada
      if (currentPage?.id === pageId) {
        setStateIfMounted(setCurrentPage, null);
      }
      toast.success("Página eliminada exitosamente");
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al eliminar la página";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
      throw err;
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [currentPage?.id, setStateIfMounted]);

  /**
   * Publica o despublica una página (requiere autenticación como Admin o SuperAdmin).
   * @param {string} pageId - ID de la página
   * @param {boolean} published - True para publicar, False para despublicar
   * @returns {Promise<Object>} Página actualizada
   */
  const publishPage = useCallback(async (pageId, published = true) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const updatedPage = await pageService.publishPage(pageId, published);
      // Actualizar en el array pages si existe
      setStateIfMounted(setPages, (prev) =>
        prev.map((p) => (p.id === pageId ? updatedPage : p))
      );
      // Actualizar currentPage si es la página actual
      if (currentPage?.id === pageId) {
        setStateIfMounted(setCurrentPage, updatedPage);
      }
      const action = published ? "publicada" : "despublicada";
      toast.success(`Página ${action} exitosamente`);
      return updatedPage;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al cambiar estado de publicación";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
      throw err;
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [currentPage?.id, setStateIfMounted]);

  /**
   * Publica o despublica múltiples páginas (requiere autenticación como Admin o SuperAdmin).
   * @param {Array<string>} pageIds - IDs de páginas a actualizar
   * @param {boolean} published - True para publicar, False para despublicar
   * @returns {Promise<Object>} Respuesta con número de páginas modificadas
   */
  const bulkPublish = useCallback(async (pageIds, published = true) => {
    setStateIfMounted(setLoading, true);
    setStateIfMounted(setError, null);
    try {
      const result = await pageService.bulkPublishPages(pageIds, published);
      // Recargar todas las páginas para sincronizar estado
      await loadPages();
      const action = published ? "publicadas" : "despublicadas";
      toast.success(`${result.modified_count} página(s) ${action}`);
      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error en la actualización masiva";
      setStateIfMounted(setError, err);
      toast.error(errorMsg);
      throw err;
    } finally {
      setStateIfMounted(setLoading, false);
    }
  }, [setStateIfMounted, loadPages]);

  /**
   * Limpia el error actual.
   */
  const clearError = useCallback(() => {
    setStateIfMounted(setError, null);
  }, [setStateIfMounted]);

  /**
   * Limpia la página actual seleccionada.
   */
  const clearCurrentPage = useCallback(() => {
    setStateIfMounted(setCurrentPage, null);
  }, [setStateIfMounted]);

  return {
    // Estado
    pages,
    currentPage,
    loading,
    error,
    // Métodos
    loadPages,
    loadPage,
    createPage,
    updatePage,
    deletePage,
    publishPage,
    bulkPublish,
    clearError,
    clearCurrentPage,
  };
}
