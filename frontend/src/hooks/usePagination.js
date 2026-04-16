import { useState, useCallback } from "react";

/**
 * Hook para gestionar el estado de paginación server-side.
 *
 * @param {Object} options
 * @param {number} options.pageSize   - Ítems por página (por defecto 25).
 * @param {number} options.total      - Total de ítems (gestionado externamente).
 *
 * @returns {{ currentPage, pageSize, skip, totalPages, handlePageChange, resetPage, setTotal, total }}
 *
 * Uso:
 *   const { currentPage, skip, totalPages, handlePageChange, resetPage, setTotal } =
 *     usePagination({ pageSize: 25 });
 *
 *   // Al cargar la respuesta:
 *   setTotal(response.data.total);
 *
 *   // Al cambiar filtros, resetear a página 1:
 *   resetPage();
 *
 *   // Para construir los params:
 *   params.append("skip", skip);
 *   params.append("limit", pageSize);
 */
export function usePagination({ pageSize = 25 } = {}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);

  const totalPages = Math.ceil(total / pageSize);
  const skip = (currentPage - 1) * pageSize;

  const handlePageChange = useCallback((newPage) => {
    setCurrentPage((prev) => {
      const pages = Math.ceil(total / pageSize) || 1;
      if (newPage >= 1 && newPage <= pages) return newPage;
      return prev;
    });
  // total y pageSize son estables por referencia en la mayoría de los casos
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [total, pageSize]);

  const resetPage = useCallback(() => setCurrentPage(1), []);

  return {
    currentPage,
    pageSize,
    skip,
    total,
    totalPages,
    setTotal,
    handlePageChange,
    resetPage,
  };
}
