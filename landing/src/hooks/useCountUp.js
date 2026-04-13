// landing/src/hooks/useCountUp.js
import { useState, useEffect, useRef } from 'react';

/**
 * Anima un número de 0 hasta `target` usando requestAnimationFrame.
 * Solo arranca cuando `trigger` es true (útil con IntersectionObserver).
 * Soporta targets con sufijos: "500+" → anima hasta 500, devuelve "500+".
 */
export function useCountUp(rawTarget, duration = 1800, trigger = true) {
  const [display, setDisplay] = useState('0');
  const rafRef = useRef(null);

  useEffect(() => {
    if (!trigger) return;

    const suffix = rawTarget.toString().replace(/[\d.]/g, '');
    const numTarget = parseFloat(rawTarget.toString().replace(/[^\d.]/g, ''));

    if (isNaN(numTarget)) { setDisplay(rawTarget); return; }

    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = Math.floor(eased * numTarget);

      const formatted = numTarget >= 1000
        ? (current / 1000).toFixed(current >= 1000 ? 0 : 1) + 'M'
        : current.toString();

      setDisplay(formatted + suffix);

      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [rawTarget, duration, trigger]);

  return display;
}
