import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
export const WS_URL = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://");

// Helper para leer el valor de una cookie por nombre
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

// Instancia Axios con auth — usa cookie httpOnly automáticamente (withCredentials)
export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  timeout: 30000  // 30s timeout — permite conexiones lentas a MongoDB
});

// Adjuntar token CSRF a cada petición mutante (patrón double-submit cookie)
api.interceptors.request.use((config) => {
  const method = (config.method || "").toUpperCase();
  if (["POST", "PUT", "DELETE", "PATCH"].includes(method)) {
    const csrf = getCookie("csrf_token");
    if (csrf) {
      config.headers["X-CSRF-Token"] = csrf;
    }
  }
  return config;
});

// Interceptor de respuesta: auto-refresh en 401, redirección en fallo final
// Usa una Promise compartida para evitar race conditions entre peticiones concurrentes
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const currentPath = window.location.hash || window.location.pathname;
    const isAuthPage = currentPath.includes('/login') || currentPath.includes('/register') || currentPath.includes('/forgot-password');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthPage) {
      // No reintentar el propio endpoint de refresh
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem("user");
        window.location.href = "/#/login";
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      // Si ya hay un refresh en curso, esperar a que termine
      if (!refreshPromise) {
        refreshPromise = api.post("/auth/refresh").finally(() => {
          refreshPromise = null;
        });
      }

      try {
        await refreshPromise;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("user");
        window.location.href = "/#/login";
        return Promise.reject(refreshError);
      }
    }

    if (error.response?.status === 401 && !isAuthPage) {
      localStorage.removeItem("user");
      window.location.href = "/#/login";
    }

    return Promise.reject(error);
  }
);
