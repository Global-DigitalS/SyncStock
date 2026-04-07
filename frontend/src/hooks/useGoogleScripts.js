import { useEffect, useRef } from "react";
import axios from "axios";
import DOMPurify from "dompurify";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const axiosInstance = axios.create({
  baseURL: BACKEND_URL,
  timeout: 5000  // Shorter timeout for optional tracking
});

/**
 * Valida que un ID de Google Tag Manager tenga el formato correcto: GTM-XXXXXX
 * @param {string} id - El ID a validar
 * @returns {string|null} - El ID validado o null si es inválido
 */
function validateGTMId(id) {
  if (typeof id !== 'string') return null;
  const gtmRegex = /^GTM-[A-Z0-9]{6,}$/;
  return gtmRegex.test(id) ? id : null;
}

/**
 * Valida que un ID de Google Analytics (GA4) tenga el formato correcto: G-XXXXXXXXXX
 * @param {string} id - El ID a validar
 * @returns {string|null} - El ID validado o null si es inválido
 */
function validateGAId(id) {
  if (typeof id !== 'string') return null;
  const gaRegex = /^G-[A-Z0-9]{10,}$/;
  return gaRegex.test(id) ? id : null;
}

/**
 * Valida que un ID de Google Ads tenga el formato correcto: AW-XXXXXXXXXX
 * @param {string} id - El ID a validar
 * @returns {string|null} - El ID validado o null si es inválido
 */
function validateGoogleAdsId(id) {
  if (typeof id !== 'string') return null;
  const adsRegex = /^AW-\d{9,}$/;
  return adsRegex.test(id) ? id : null;
}

/**
 * Valida y sanitiza el código de verificación de Google Search Console
 * @param {string} code - El código a validar (puede ser un string o un meta tag HTML)
 * @returns {string|null} - El código validado o null si es inválido
 */
function validateSearchConsoleCode(code) {
  if (typeof code !== 'string' || code.trim().length === 0) return null;

  // Si es un contenido HTML (ej: meta tag), extraer el atributo content
  if (code.includes('<') && code.includes('>')) {
    try {
      // Intentar extraer el content attribute de un meta tag
      // Soporta: content="value", content='value', o content=value
      const contentMatch = code.match(/content\s*=\s*["']?([a-zA-Z0-9_-]+)["']?/i);
      if (contentMatch && contentMatch[1]) {
        const extractedCode = contentMatch[1];
        const codeRegex = /^[a-zA-Z0-9_-]+$/;
        return codeRegex.test(extractedCode) ? extractedCode : null;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  // Si es solo un código (string de verificación), validar que sea alfanumérico
  const codeRegex = /^[a-zA-Z0-9_-]+$/;
  return codeRegex.test(code) ? code : null;
}

/**
 * Escapa caracteres especiales en atributos HTML para prevenir inyección
 * @param {string} str - String a escapar
 * @returns {string} - String escapado
 */
function escapeHtmlAttribute(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Hook que carga la configuración de Google Services desde el backend
 * e inyecta dinámicamente los scripts de tracking (Analytics, GTM, Ads, Search Console).
 * Se ejecuta una sola vez al montar el componente.
 */
export default function useGoogleScripts() {
  const injected = useRef(false);

  useEffect(() => {
    if (injected.current) return;
    injected.current = true;

    const load = async () => {
      try {
        const res = await axiosInstance.get("/api/google-services/public");
        const config = res.data;
        if (!config) return;
        injectScripts(config);
      } catch (_) {
        // Silently fail — tracking is optional
      }
    };
    load();
  }, []);
}

function injectScripts(config) {
  // Google Tag Manager (se recomienda cargar primero)
  if (config.tag_manager_enabled && config.tag_manager_container_id) {
    const validGtmId = validateGTMId(config.tag_manager_container_id);

    if (!validGtmId) {
      console.warn('[Security] Google Tag Manager ID validation failed');
      return;
    }

    const gtmScript = document.createElement("script");
    gtmScript.textContent = `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
      new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
      j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
      'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','${validGtmId}');`;
    document.head.appendChild(gtmScript);

    // Sanitizar iframe HTML para prevenir XSS
    const gtmNoscript = document.createElement("noscript");
    const iframeHtml = `<iframe src="https://www.googletagmanager.com/ns.html?id=${validGtmId}" height="0" width="0" style="display:none;visibility:hidden"></iframe>`;
    const sanitizedHtml = DOMPurify.sanitize(iframeHtml, {
      ALLOWED_TAGS: ['iframe'],
      ALLOWED_ATTR: ['src', 'height', 'width', 'style']
    });
    gtmNoscript.innerHTML = sanitizedHtml;
    document.body.insertBefore(gtmNoscript, document.body.firstChild);
  }

  // Google Analytics (GA4) — solo si GTM no está activo
  if (config.analytics_enabled && config.analytics_measurement_id && !config.tag_manager_enabled) {
    const validGaId = validateGAId(config.analytics_measurement_id);

    if (!validGaId) {
      console.warn('[Security] Google Analytics ID validation failed');
      return;
    }

    const gaScript = document.createElement("script");
    gaScript.async = true;
    gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${validGaId}`;
    document.head.appendChild(gaScript);

    const gaInline = document.createElement("script");
    gaInline.textContent = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${validGaId}');`;
    document.head.appendChild(gaInline);
  }

  // Google Ads — solo si GTM no está activo
  if (config.google_ads_enabled && config.google_ads_conversion_id && !config.tag_manager_enabled) {
    const validAwId = validateGoogleAdsId(config.google_ads_conversion_id);

    if (!validAwId) {
      console.warn('[Security] Google Ads ID validation failed');
      return;
    }

    if (!config.analytics_enabled || !config.analytics_measurement_id) {
      const adsScript = document.createElement("script");
      adsScript.async = true;
      adsScript.src = `https://www.googletagmanager.com/gtag/js?id=${validAwId}`;
      document.head.appendChild(adsScript);

      const adsInline = document.createElement("script");
      adsInline.textContent = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${validAwId}');`;
      document.head.appendChild(adsInline);
    } else {
      const adsConfig = document.createElement("script");
      adsConfig.textContent = `gtag('config','${validAwId}');`;
      document.head.appendChild(adsConfig);
    }
  }

  // Google Search Console — meta tag de verificación
  if (config.search_console_enabled && config.search_console_verification_code) {
    const validCode = validateSearchConsoleCode(config.search_console_verification_code);

    if (!validCode) {
      console.warn('[Security] Search Console verification code validation failed');
      return;
    }

    // Si el código contiene HTML (meta tag), parsearlo
    if (validCode.includes('<')) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = DOMPurify.sanitize(validCode, { ALLOWED_TAGS: ['meta'], ALLOWED_ATTR: ['name', 'content'] });
      const metaTag = tempDiv.querySelector('meta[name="google-site-verification"]');
      if (metaTag && metaTag.content) {
        const meta = document.createElement("meta");
        meta.name = "google-site-verification";
        meta.content = metaTag.content;
        document.head.appendChild(meta);
      }
    } else {
      // Si es solo el contenido, crear el meta tag
      const meta = document.createElement("meta");
      meta.name = "google-site-verification";
      meta.content = validCode;
      document.head.appendChild(meta);
    }
  }
}
