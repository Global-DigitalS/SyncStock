import { useRef, useEffect, useState } from "react";

/**
 * Hook que usa IntersectionObserver para detectar cuando un elemento
 * entra en el viewport. Devuelve [ref, inView].
 * Una vez visible, no vuelve a false (oneShot = true por defecto).
 *
 * @param {IntersectionObserverInit} [options]
 * @param {boolean} [oneShot=true] - Si true, deja de observar al hacerse visible
 * @returns {[React.RefObject, boolean]}
 */
export function useInView(options = {}, oneShot = true) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      // Fallback: mostrar directamente si el browser no soporta IO
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          if (oneShot) observer.disconnect();
        }
      },
      {
        threshold: 0.12,
        rootMargin: "0px 0px -60px 0px",
        ...options,
      }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [oneShot]); // eslint-disable-line react-hooks/exhaustive-deps

  return [ref, inView];
}

/**
 * Hook para animar números contando desde 0 hasta `target`
 * cuando el elemento está en el viewport.
 *
 * @param {number} target
 * @param {number} [duration=1500] - duración en ms
 * @returns {[React.RefObject, string]} ref y valor actual como string
 */
export function useCountUp(target, duration = 1500) {
  const [ref, inView] = useInView();
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const start = performance.now();
    const numericTarget = parseFloat(String(target).replace(/[^0-9.]/g, "")) || 0;

    const tick = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * numericTarget));
      if (progress < 1) requestAnimationFrame(tick);
      else setCount(numericTarget);
    };

    requestAnimationFrame(tick);
  }, [inView, target, duration]);

  // Preservar sufijo original (%, +, etc.)
  const suffix = String(target).replace(/^[\d.,]+/, "");
  const formatted = count.toLocaleString("es-ES");

  return [ref, `${formatted}${suffix}`];
}
