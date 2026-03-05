/**
 * Input sanitization utilities for frontend security.
 * Prevents XSS and other client-side attacks.
 */

/**
 * Sanitize a string input by escaping HTML entities
 * @param {string} str - The string to sanitize
 * @param {number} maxLength - Maximum allowed length
 * @returns {string} Sanitized string
 */
export const sanitizeString = (str, maxLength = 10000) => {
  if (typeof str !== 'string') return str;
  
  // Trim to max length
  let result = str.slice(0, maxLength);
  
  // Remove null bytes
  result = result.replace(/\0/g, '');
  
  // Escape HTML entities
  const htmlEntities = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };
  
  result = result.replace(/[&<>"'/]/g, char => htmlEntities[char]);
  
  return result.trim();
};

/**
 * Sanitize HTML content while preserving safe tags
 * @param {string} html - The HTML string to sanitize
 * @returns {string} Sanitized HTML
 */
export const sanitizeHtml = (html) => {
  if (typeof html !== 'string') return html;
  
  // Remove script tags and content
  html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  
  // Remove on* event handlers
  html = html.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');
  html = html.replace(/\s*on\w+\s*=\s*[^\s>]+/gi, '');
  
  // Remove javascript: URLs
  html = html.replace(/javascript:/gi, '');
  html = html.replace(/vbscript:/gi, '');
  html = html.replace(/data:text\/html/gi, '');
  
  return html;
};

/**
 * Sanitize email input
 * @param {string} email - The email to sanitize
 * @returns {string} Sanitized email
 */
export const sanitizeEmail = (email) => {
  if (typeof email !== 'string') return email;
  
  return email.trim().toLowerCase().slice(0, 254);
};

/**
 * Sanitize URL input
 * @param {string} url - The URL to sanitize
 * @returns {string} Sanitized URL
 */
export const sanitizeUrl = (url) => {
  if (typeof url !== 'string') return url;
  
  // Remove dangerous protocols
  if (/^(javascript|data|vbscript):/i.test(url.trim())) {
    return '';
  }
  
  return url.trim().slice(0, 2048);
};

/**
 * Sanitize a number input
 * @param {any} value - The value to sanitize
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @param {number} defaultValue - Default value if invalid
 * @returns {number} Sanitized number
 */
export const sanitizeNumber = (value, min = 0, max = Number.MAX_SAFE_INTEGER, defaultValue = 0) => {
  const num = parseInt(value, 10);
  
  if (isNaN(num)) return defaultValue;
  if (num < min) return min;
  if (num > max) return max;
  
  return num;
};

/**
 * Sanitize an object by sanitizing all string values
 * @param {object} obj - The object to sanitize
 * @param {string[]} htmlFields - Fields that should allow HTML
 * @returns {object} Sanitized object
 */
export const sanitizeObject = (obj, htmlFields = []) => {
  if (!obj || typeof obj !== 'object') return obj;
  
  const result = {};
  
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      result[key] = htmlFields.includes(key) 
        ? sanitizeHtml(value) 
        : sanitizeString(value);
    } else if (Array.isArray(value)) {
      result[key] = value.map(item => 
        typeof item === 'object' ? sanitizeObject(item, htmlFields) : 
        typeof item === 'string' ? sanitizeString(item) : item
      );
    } else if (typeof value === 'object' && value !== null) {
      result[key] = sanitizeObject(value, htmlFields);
    } else {
      result[key] = value;
    }
  }
  
  return result;
};

/**
 * Sanitize form data before submission
 * @param {object} formData - The form data to sanitize
 * @returns {object} Sanitized form data
 */
export const sanitizeFormData = (formData) => {
  // Fields that may contain HTML (like email templates)
  const htmlFields = ['html_content', 'template_content', 'body_html'];
  
  return sanitizeObject(formData, htmlFields);
};

/**
 * Check if a string contains potential XSS patterns
 * @param {string} str - The string to check
 * @returns {boolean} True if suspicious patterns found
 */
export const hasSuspiciousContent = (str) => {
  if (typeof str !== 'string') return false;
  
  const patterns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i,
    /data:text\/html/i,
    /vbscript:/i
  ];
  
  return patterns.some(pattern => pattern.test(str));
};

export default {
  sanitizeString,
  sanitizeHtml,
  sanitizeEmail,
  sanitizeUrl,
  sanitizeNumber,
  sanitizeObject,
  sanitizeFormData,
  hasSuspiciousContent
};
