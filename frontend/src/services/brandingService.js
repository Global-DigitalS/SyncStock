import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_BASE_URL}/api`;

// Instancia Axios específica para brandingService
const apiClient = axios.create({
  baseURL: API,
  withCredentials: true,
  timeout: 30000,
});

/**
 * Obtiene la configuración de marca actual (sin autenticación).
 * Este es un endpoint público.
 * @returns {Promise<Object>} Objeto de configuración de marca
 */
export const getBranding = async () => {
  try {
    const response = await apiClient.get("/branding");
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza la configuración de marca (requiere autenticación como SuperAdmin).
 * @param {Object} brandingData - Datos de marca a actualizar
 * @param {string} brandingData.logo_url - URL del logo (opcional)
 * @param {string} brandingData.logo_dark_url - URL del logo en versión oscura (opcional)
 * @param {string} brandingData.favicon_url - URL del favicon (opcional)
 * @param {string} brandingData.primary_color - Color primario en hex (opcional)
 * @param {string} brandingData.secondary_color - Color secundario en hex (opcional)
 * @param {string} brandingData.company_name - Nombre de la empresa (opcional)
 * @param {string} brandingData.company_description - Descripción de la empresa (opcional)
 * @param {string} brandingData.support_email - Email de soporte (opcional)
 * @param {string} brandingData.support_phone - Teléfono de soporte (opcional)
 * @param {Object} brandingData.social_links - Enlaces a redes sociales (opcional)
 * @param {Array} brandingData.subscription_plans - Planes de suscripción (opcional)
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateBranding = async (brandingData) => {
  try {
    const response = await apiClient.put("/branding", brandingData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Inicializa la configuración de marca por primera vez (requiere autenticación como SuperAdmin).
 * Solo puede usarse si no existe configuración previa.
 * @param {Object} brandingData - Datos iniciales de marca
 * @returns {Promise<Object>} Configuración de marca creada
 */
export const initializeBranding = async (brandingData) => {
  try {
    const response = await apiClient.post("/branding", brandingData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza rápidamente los colores primario y secundario (requiere autenticación como SuperAdmin).
 * @param {string} primaryColor - Color primario en formato hex (ej: #FF5733)
 * @param {string} secondaryColor - Color secundario en formato hex (ej: #33FF57)
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateColors = async (primaryColor, secondaryColor) => {
  try {
    const response = await apiClient.put("/branding/colors", null, {
      params: {
        primary_color: primaryColor,
        secondary_color: secondaryColor,
      },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza información de la empresa (requiere autenticación como SuperAdmin).
 * @param {Object} companyInfo - Información de la empresa
 * @param {string} companyInfo.company_name - Nombre de la empresa (opcional)
 * @param {string} companyInfo.company_description - Descripción (opcional)
 * @param {string} companyInfo.support_email - Email de soporte (opcional)
 * @param {string} companyInfo.support_phone - Teléfono (opcional)
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateCompanyInfo = async (companyInfo) => {
  try {
    const params = {};
    if (companyInfo.company_name !== undefined) params.company_name = companyInfo.company_name;
    if (companyInfo.company_description !== undefined) params.company_description = companyInfo.company_description;
    if (companyInfo.support_email !== undefined) params.support_email = companyInfo.support_email;
    if (companyInfo.support_phone !== undefined) params.support_phone = companyInfo.support_phone;

    const response = await apiClient.put("/branding/company-info", null, {
      params,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza logos y favicon (requiere autenticación como SuperAdmin).
 * @param {Object} logoData - Datos de logos
 * @param {string} logoData.logo_url - URL del logo (opcional)
 * @param {string} logoData.logo_dark_url - URL del logo oscuro (opcional)
 * @param {string} logoData.favicon_url - URL del favicon (opcional)
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateLogos = async (logoData) => {
  try {
    const params = {};
    if (logoData.logo_url !== undefined) params.logo_url = logoData.logo_url;
    if (logoData.logo_dark_url !== undefined) params.logo_dark_url = logoData.logo_dark_url;
    if (logoData.favicon_url !== undefined) params.favicon_url = logoData.favicon_url;

    const response = await apiClient.put("/branding/logos", null, {
      params,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza enlaces a redes sociales (requiere autenticación como SuperAdmin).
 * @param {Object} socialLinks - Diccionario con plataforma: URL
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateSocialLinks = async (socialLinks) => {
  try {
    const response = await apiClient.put("/branding/social-links", socialLinks);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Actualiza planes de suscripción (requiere autenticación como SuperAdmin).
 * @param {Array} subscriptionPlans - Lista de configuraciones de planes
 * @returns {Promise<Object>} Configuración de marca actualizada
 */
export const updateSubscriptionPlans = async (subscriptionPlans) => {
  try {
    const response = await apiClient.put("/branding/subscription-plans", subscriptionPlans);
    return response.data;
  } catch (error) {
    throw error;
  }
};
