import { useState, useEffect } from "react";
import {
  getBranding,
  getPublicPages,
  getPageBySlug,
} from "../services/landingApiService";
import {
  DEFAULT_BRANDING,
  DEFAULT_PAGES,
  DEFAULT_PLANS,
} from "../constants/defaultBranding";

/**
 * Hook personalizado para cargar datos de la landing page desde la API.
 * Gestiona branding, listado de páginas públicas y página específica (opcional).
 *
 * @param {Object} options - Opciones del hook
 * @param {string} [options.slug] - Slug de página específica a cargar. Si se proporciona, carga esa página además de branding y listado.
 * @returns {Object} Objeto con estado:
 *   - branding: Configuración de branding (objeto)
 *   - pages: Array de páginas públicas
 *   - currentPage: Página específica si slug fue proporcionado, null si no
 *   - plans: Array de planes de suscripción
 *   - loading: Boolean indicando si hay carga en progreso
 *   - error: Objeto con posibles errores { brandingError, pagesError, currentPageError }
 *   - isLoading: Alias de loading para compatibilidad
 *
 * @example
 * const { branding, pages, currentPage, loading, error } = useLandingData({ slug: "acerca-de" });
 *
 * @example
 * const { branding, pages, plans, loading } = useLandingData();
 */
export function useLandingData({ slug = null } = {}) {
  // Estado principal
  const [branding, setBranding] = useState(DEFAULT_BRANDING);
  const [pages, setPages] = useState(DEFAULT_PAGES);
  const [currentPage, setCurrentPage] = useState(null);
  const [plans, setPlans] = useState(DEFAULT_PLANS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState({
    brandingError: null,
    pagesError: null,
    currentPageError: null,
  });

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      try {
        setLoading(true);
        setError({ brandingError: null, pagesError: null, currentPageError: null });

        // Cargar branding y páginas públicas en paralelo
        const [brandingRes, pagesRes] = await Promise.allSettled([
          getBranding(),
          getPublicPages(),
        ]);

        // Procesar respuesta de branding
        if (isMounted) {
          if (brandingRes.status === "fulfilled" && brandingRes.value) {
            setBranding((prev) => ({
              ...prev,
              ...brandingRes.value,
            }));
          } else if (brandingRes.status === "rejected") {
            console.warn("Error cargando branding, usando defaults:", brandingRes.reason);
            setError((prev) => ({
              ...prev,
              brandingError: brandingRes.reason,
            }));
            // Mantener DEFAULT_BRANDING
          }
        }

        // Procesar respuesta de páginas
        if (isMounted) {
          if (pagesRes.status === "fulfilled" && Array.isArray(pagesRes.value)) {
            setPages(pagesRes.value);
          } else if (pagesRes.status === "rejected") {
            console.warn("Error cargando páginas, usando defaults:", pagesRes.reason);
            setError((prev) => ({
              ...prev,
              pagesError: pagesRes.reason,
            }));
            // Mantener DEFAULT_PAGES
          }
        }

        // Cargar página específica si slug es proporcionado
        if (slug && isMounted) {
          try {
            const pageData = await getPageBySlug(slug);
            if (isMounted) {
              setCurrentPage(pageData);
            }
          } catch (pageError) {
            console.warn(`Error cargando página "${slug}":`, pageError);
            setError((prev) => ({
              ...prev,
              currentPageError: pageError,
            }));
            setCurrentPage(null);
          }
        } else if (!slug && isMounted) {
          // Si no hay slug, limpiar currentPage
          setCurrentPage(null);
        }
      } catch (err) {
        console.error("Error inesperado en useLandingData:", err);
        if (isMounted) {
          setError((prev) => ({
            ...prev,
            brandingError: err,
            pagesError: err,
            currentPageError: err,
          }));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();

    // Cleanup function: evita actualizar estado si el componente se desmonta
    return () => {
      isMounted = false;
    };
  }, [slug]);

  return {
    branding,
    pages,
    currentPage,
    plans,
    loading,
    error,
    isLoading: loading, // Alias para compatibilidad
  };
}

export default useLandingData;
