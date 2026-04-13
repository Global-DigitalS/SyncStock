// landing/src/hooks/useReveal.js
import { useEffect, useRef } from 'react';

/**
 * Devuelve un ref. Cuando el elemento entra en el viewport,
 * añade la clase "revealed" (activa .animate-reveal.revealed en CSS).
 * Se dispara solo una vez por elemento.
 */
export function useReveal(threshold = 0.15) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('revealed');
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return ref;
}
