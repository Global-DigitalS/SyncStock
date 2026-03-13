import { useEffect, useRef } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
        const res = await axios.get(`${BACKEND_URL}/api/google-services/public`);
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
    const gtmId = config.tag_manager_container_id;
    const gtmScript = document.createElement("script");
    gtmScript.textContent = `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
      new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
      j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
      'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','${gtmId}');`;
    document.head.appendChild(gtmScript);
    const gtmNoscript = document.createElement("noscript");
    gtmNoscript.innerHTML = `<iframe src="https://www.googletagmanager.com/ns.html?id=${gtmId}" height="0" width="0" style="display:none;visibility:hidden"></iframe>`;
    document.body.insertBefore(gtmNoscript, document.body.firstChild);
  }

  // Google Analytics (GA4) — solo si GTM no está activo
  if (config.analytics_enabled && config.analytics_measurement_id && !config.tag_manager_enabled) {
    const gaId = config.analytics_measurement_id;
    const gaScript = document.createElement("script");
    gaScript.async = true;
    gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`;
    document.head.appendChild(gaScript);
    const gaInline = document.createElement("script");
    gaInline.textContent = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${gaId}');`;
    document.head.appendChild(gaInline);
  }

  // Google Ads — solo si GTM no está activo
  if (config.google_ads_enabled && config.google_ads_conversion_id && !config.tag_manager_enabled) {
    const awId = config.google_ads_conversion_id;
    if (!config.analytics_enabled || !config.analytics_measurement_id) {
      const adsScript = document.createElement("script");
      adsScript.async = true;
      adsScript.src = `https://www.googletagmanager.com/gtag/js?id=${awId}`;
      document.head.appendChild(adsScript);
      const adsInline = document.createElement("script");
      adsInline.textContent = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${awId}');`;
      document.head.appendChild(adsInline);
    } else {
      const adsConfig = document.createElement("script");
      adsConfig.textContent = `gtag('config','${awId}');`;
      document.head.appendChild(adsConfig);
    }
  }

  // Google Search Console — meta tag de verificación
  if (config.search_console_enabled && config.search_console_verification_code) {
    const code = config.search_console_verification_code;
    const content = code.includes("content=") ? code.match(/content="?([^">\s]+)"?/)?.[1] || code : code;
    const meta = document.createElement("meta");
    meta.name = "google-site-verification";
    meta.content = content;
    document.head.appendChild(meta);
  }
}
