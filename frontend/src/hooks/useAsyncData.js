import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Hook genérico para cargar datos asíncronos con estado de loading y error.
 *
 * @param {Function} fetcher   - Función async que devuelve los datos.
 * @param {Array}    deps      - Dependencias de useEffect (como en useEffect).
 * @param {Object}   options
 * @param {*}        options.initialData  - Valor inicial de `data` (por defecto null).
 * @param {boolean}  options.immediate    - Si debe ejecutarse al montar (por defecto true).
 *
 * @returns {{ data, loading, error, reload }}
 *
 * Uso:
 *   const { data: products, loading, error, reload } = useAsyncData(
 *     () => api.get("/products").then(r => r.data),
 *     [currentPage, searchTerm]
 *   );
 */
export function useAsyncData(fetcher, deps = [], { initialData = null, immediate = true } = {}) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  // Evita actualizaciones de estado en componentes desmontados
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) setData(result);
    } catch (err) {
      if (mountedRef.current) setError(err);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    if (immediate) execute();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute]);

  return { data, loading, error, reload: execute };
}
