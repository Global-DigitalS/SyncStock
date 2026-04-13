import { useEffect } from "react";

const BASE_URL = "https://sync-stock.com";
const DEFAULT_OG_IMAGE = `${BASE_URL}/og-image.png`;

/**
 * Hook para gestionar SEO por página sin dependencias externas.
 * Actualiza dinámicamente title, meta tags, Open Graph, Twitter Card,
 * canonical y structured data JSON-LD.
 *
 * @param {Object} config
 * @param {string} config.title           - Título de la página (sin el sufijo de marca)
 * @param {string} config.description     - Meta descripción (máx. 160 chars)
 * @param {string} config.canonical       - Ruta relativa, ej. "/precios"
 * @param {string} [config.ogImage]       - URL absoluta de la imagen OG
 * @param {Object} [config.structuredData]- Objeto JSON-LD
 */
export function useSEO({ title, description, canonical, ogImage, structuredData } = {}) {
  useEffect(() => {
    const fullTitle = title
      ? `${title} | SyncStock`
      : "SyncStock — Sincronización de Inventario B2B Automatizada";

    const canonicalUrl = canonical
      ? `${BASE_URL}${canonical}`
      : BASE_URL;

    const image = ogImage || DEFAULT_OG_IMAGE;

    // ── Título ──────────────────────────────────────────────────────────
    document.title = fullTitle;

    // ── Función helper ───────────────────────────────────────────────────
    const setMeta = (selector, attr, value) => {
      let el = document.querySelector(selector);
      if (!el) {
        el = document.createElement("meta");
        const [attrName, attrVal] = selector.match(/\[([^=]+)=['"]([^'"]+)/)?.[1]
          ? [selector.match(/\[([^=]+)=/)?.[1], selector.match(/=['"]([^'"]+)/)?.[1]]
          : ["name", ""];
        el.setAttribute(attrName || "property", attrVal || "");
        document.head.appendChild(el);
      }
      el.setAttribute(attr, value);
    };

    // ── Meta básicos ─────────────────────────────────────────────────────
    setMeta('meta[name="description"]', "content", description || "");

    // ── Canonical ────────────────────────────────────────────────────────
    let canonicalEl = document.querySelector('link[rel="canonical"]');
    if (!canonicalEl) {
      canonicalEl = document.createElement("link");
      canonicalEl.setAttribute("rel", "canonical");
      document.head.appendChild(canonicalEl);
    }
    canonicalEl.setAttribute("href", canonicalUrl);

    // ── Open Graph ───────────────────────────────────────────────────────
    const ogTags = {
      'meta[property="og:title"]': ["content", fullTitle],
      'meta[property="og:description"]': ["content", description || ""],
      'meta[property="og:url"]': ["content", canonicalUrl],
      'meta[property="og:image"]': ["content", image],
    };
    Object.entries(ogTags).forEach(([selector, [attr, value]]) => {
      let el = document.querySelector(selector);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute("property", selector.match(/property="([^"]+)"/)?.[1] || "");
        document.head.appendChild(el);
      }
      el.setAttribute(attr, value);
    });

    // ── Twitter Card ─────────────────────────────────────────────────────
    const twitterTags = {
      'meta[name="twitter:title"]': ["content", fullTitle],
      'meta[name="twitter:description"]': ["content", description || ""],
      'meta[name="twitter:image"]': ["content", image],
    };
    Object.entries(twitterTags).forEach(([selector, [attr, value]]) => {
      let el = document.querySelector(selector);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute("name", selector.match(/name="([^"]+)"/)?.[1] || "");
        document.head.appendChild(el);
      }
      el.setAttribute(attr, value);
    });

    // ── JSON-LD structured data ──────────────────────────────────────────
    const SCRIPT_ID = "page-structured-data";
    let existing = document.getElementById(SCRIPT_ID);
    if (existing) existing.remove();

    if (structuredData) {
      const script = document.createElement("script");
      script.type = "application/ld+json";
      script.id = SCRIPT_ID;
      script.textContent = JSON.stringify(structuredData);
      document.head.appendChild(script);
    }

    // Cleanup al desmontar
    return () => {
      const sd = document.getElementById(SCRIPT_ID);
      if (sd) sd.remove();
    };
  }, [title, description, canonical, ogImage, structuredData]);
}
