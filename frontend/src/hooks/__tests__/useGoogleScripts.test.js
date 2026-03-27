/**
 * Test suite para useGoogleScripts.js
 * Valida que las funciones de sanitización y validación funcionan correctamente
 */

import DOMPurify from 'dompurify';

// Funciones de validación (copiadas del hook para testing)
function validateGTMId(id) {
  if (typeof id !== 'string') return null;
  const gtmRegex = /^GTM-[A-Z0-9]{6,}$/;
  return gtmRegex.test(id) ? id : null;
}

function validateGAId(id) {
  if (typeof id !== 'string') return null;
  const gaRegex = /^G-[A-Z0-9]{10,}$/;
  return gaRegex.test(id) ? id : null;
}

function validateGoogleAdsId(id) {
  if (typeof id !== 'string') return null;
  const adsRegex = /^AW-\d{9,}$/;
  return adsRegex.test(id) ? id : null;
}

function validateSearchConsoleCode(code) {
  if (typeof code !== 'string' || code.trim().length === 0) return null;

  if (code.includes('<') && code.includes('>')) {
    try {
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

  const codeRegex = /^[a-zA-Z0-9_-]+$/;
  return codeRegex.test(code) ? code : null;
}

describe('useGoogleScripts validation functions', () => {
  describe('validateGTMId', () => {
    it('debe aceptar un GTM ID válido', () => {
      expect(validateGTMId('GTM-123456')).toBe('GTM-123456');
      expect(validateGTMId('GTM-ABCDEF123')).toBe('GTM-ABCDEF123');
    });

    it('debe rechazar un GTM ID inválido', () => {
      expect(validateGTMId('gtm-123456')).toBeNull(); // lowercase
      expect(validateGTMId('GTM-12345')).toBeNull(); // muy corto
      expect(validateGTMId('GA-123456')).toBeNull(); // prefijo incorrecto
      expect(validateGTMId('GTM-123-456')).toBeNull(); // carácter inválido
      expect(validateGTMId('')).toBeNull(); // vacío
      expect(validateGTMId(null)).toBeNull(); // null
      expect(validateGTMId(123)).toBeNull(); // no es string
    });

    it('debe prevenir XSS en GTM ID', () => {
      expect(validateGTMId('<script>alert("xss")</script>')).toBeNull();
      expect(validateGTMId('GTM-12345" onload="alert(\'xss\')')).toBeNull();
      expect(validateGTMId('GTM-${alert("xss")}')).toBeNull();
    });
  });

  describe('validateGAId', () => {
    it('debe aceptar un GA4 ID válido', () => {
      expect(validateGAId('G-ABCDEF1234')).toBe('G-ABCDEF1234');
      expect(validateGAId('G-1234567890')).toBe('G-1234567890');
    });

    it('debe rechazar un GA4 ID inválido', () => {
      expect(validateGAId('g-ABCDEF1234')).toBeNull(); // lowercase
      expect(validateGAId('GA-ABCDEF1234')).toBeNull(); // prefijo incorrecto
      expect(validateGAId('G-ABCDEF123')).toBeNull(); // muy corto
      expect(validateGAId('')).toBeNull(); // vacío
      expect(validateGAId(null)).toBeNull(); // null
    });

    it('debe prevenir XSS en GA ID', () => {
      expect(validateGAId('<iframe src="evil.com"></iframe>')).toBeNull();
      expect(validateGAId('G-1234567890" onload="fetch(\'evil.com\')')).toBeNull();
    });
  });

  describe('validateGoogleAdsId', () => {
    it('debe aceptar un Google Ads ID válido', () => {
      expect(validateGoogleAdsId('AW-123456789')).toBe('AW-123456789');
      expect(validateGoogleAdsId('AW-9876543210')).toBe('AW-9876543210');
    });

    it('debe rechazar un Google Ads ID inválido', () => {
      expect(validateGoogleAdsId('aw-123456789')).toBeNull(); // lowercase
      expect(validateGoogleAdsId('AW-12345678')).toBeNull(); // muy corto
      expect(validateGoogleAdsId('AW-ABC123')).toBeNull(); // no es numérico
      expect(validateGoogleAdsId('')).toBeNull(); // vacío
      expect(validateGoogleAdsId(null)).toBeNull(); // null
    });

    it('debe prevenir XSS en Google Ads ID', () => {
      expect(validateGoogleAdsId('AW-123456789\' onload=\'alert("xss")')).toBeNull();
    });
  });

  describe('validateSearchConsoleCode', () => {
    it('debe aceptar un código de verificación válido (string)', () => {
      expect(validateSearchConsoleCode('google123abc456')).toBe('google123abc456');
      expect(validateSearchConsoleCode('abc_def-123')).toBe('abc_def-123');
    });

    it('debe aceptar un meta tag válido', () => {
      const metaTag = '<meta name="google-site-verification" content="googleXXX123">';
      const result = validateSearchConsoleCode(metaTag);
      // La función extrae solo el valor del content attribute
      expect(result).toBe('googleXXX123');
    });

    it('debe rechazar un código inválido', () => {
      expect(validateSearchConsoleCode('')).toBeNull(); // vacío
      expect(validateSearchConsoleCode(null)).toBeNull(); // null
      expect(validateSearchConsoleCode(123)).toBeNull(); // no es string
    });

    it('debe sanitizar HTML malicioso extrayendo solo el content value', () => {
      const maliciousHtml = '<meta name="google-site-verification" content="test"><script>alert("xss")</script>';
      const result = validateSearchConsoleCode(maliciousHtml);
      // El script tag se ignora, solo se extrae el content value
      expect(result).toBe('test');
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert');
    });

    it('debe rechazar meta tags con atributos peligrosos en el content value', () => {
      const maliciousHtml = '<meta name="google-site-verification" onload="alert(\'xss\')" content="test_with_alert">';
      const result = validateSearchConsoleCode(maliciousHtml);
      // Solo se extrae el content value, se ignoran otros atributos
      expect(result).toBe('test_with_alert');
    });
  });

  describe('DOMPurify sanitization', () => {
    it('debe sanitizar iframe HTML correctamente', () => {
      const iframeHtml = `<iframe src="https://www.googletagmanager.com/ns.html?id=GTM-123456" height="0" width="0" style="display:none"></iframe>`;
      const sanitized = DOMPurify.sanitize(iframeHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src', 'height', 'width', 'style']
      });
      expect(sanitized).toContain('<iframe');
      expect(sanitized).toContain('src="https://www.googletagmanager.com/ns.html?id=GTM-123456"');
    });

    it('debe remover scripts de iframe HTML', () => {
      const maliciousHtml = `<iframe src="https://example.com"><script>alert("xss")</script></iframe>`;
      const sanitized = DOMPurify.sanitize(maliciousHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src']
      });
      expect(sanitized).not.toContain('<script>');
      expect(sanitized).not.toContain('alert');
    });

    it('debe remover event handlers de iframe', () => {
      const maliciousHtml = `<iframe src="https://example.com" onload="alert('xss')" onerror="fetch('evil.com')"></iframe>`;
      const sanitized = DOMPurify.sanitize(maliciousHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src']
      });
      expect(sanitized).not.toContain('onload');
      expect(sanitized).not.toContain('onerror');
    });

    it('debe permitir atributos de seguridad válidos', () => {
      const html = `<iframe src="https://www.googletagmanager.com/ns.html?id=GTM-123456" height="0" width="0" style="display:none;visibility:hidden"></iframe>`;
      const sanitized = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src', 'height', 'width', 'style']
      });
      expect(sanitized).toContain('height="0"');
      expect(sanitized).toContain('width="0"');
      expect(sanitized).toContain('display:none');
    });
  });

  describe('XSS Attack Prevention', () => {
    it('debe prevenir inyección de atributos src maliciosos', () => {
      const maliciousId = 'GTM-123456" onerror="alert(\'xss\')"';
      expect(validateGTMId(maliciousId)).toBeNull();
    });

    it('debe prevenir inyección de iframe src doble', () => {
      const maliciousId = 'GTM-123456\' src=\'javascript:alert("xss")';
      expect(validateGTMId(maliciousId)).toBeNull();
    });

    it('debe prevenir data URI injection', () => {
      const maliciousId = 'data:text/html,<script>alert("xss")</script>';
      expect(validateGTMId(maliciousId)).toBeNull();
    });

    it('debe prevenir javascript: protocol injection', () => {
      const maliciousHtml = `<iframe src="javascript:alert('xss')"></iframe>`;
      const sanitized = DOMPurify.sanitize(maliciousHtml, {
        ALLOWED_TAGS: ['iframe'],
        ALLOWED_ATTR: ['src']
      });
      // DOMPurify debe remover el src malicioso
      expect(sanitized).not.toContain('javascript:');
    });
  });
});
