import { useState, useEffect, createContext, useContext, useCallback, useRef, lazy, Suspense } from "react";
import "@/App.css";
import { HashRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Pages — lazy loaded for code splitting
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Setup = lazy(() => import("./pages/Setup"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Suppliers = lazy(() => import("./pages/Suppliers"));
const SupplierDetail = lazy(() => import("./pages/SupplierDetail"));
const Products = lazy(() => import("./pages/Products"));
const Catalogs = lazy(() => import("./pages/Catalogs"));
const CatalogDetail = lazy(() => import("./pages/CatalogDetail"));
const Export = lazy(() => import("./pages/Export"));
const WooCommerceExport = lazy(() => import("./pages/WooCommerceExport"));
const PriceHistory = lazy(() => import("./pages/PriceHistory"));
const Notifications = lazy(() => import("./pages/Notifications"));
const SyncHistory = lazy(() => import("./pages/SyncHistory"));
const UserManagement = lazy(() => import("./pages/UserManagement"));
const SuperAdminDashboard = lazy(() => import("./pages/SuperAdminDashboard"));
const Subscriptions = lazy(() => import("./pages/Subscriptions"));
const Webhooks = lazy(() => import("./pages/Webhooks"));
const EmailConfig = lazy(() => import("./pages/EmailConfig"));
const CRMPage = lazy(() => import("./pages/CRM"));
const Marketplaces = lazy(() => import("./pages/Marketplaces"));
const SyncSettings = lazy(() => import("./pages/SyncSettings"));
const Profile = lazy(() => import("./pages/Profile"));
const Support = lazy(() => import("./pages/Support"));
const Landing = lazy(() => import("./pages/Landing"));

// Admin Pages — lazy loaded
const AdminBranding = lazy(() => import("./pages/AdminBranding"));
const AdminPlans = lazy(() => import("./pages/AdminPlans"));
const AdminEmailTemplates = lazy(() => import("./pages/AdminEmailTemplates"));
const AdminStripe = lazy(() => import("./pages/AdminStripe"));
const AdminEmailAccounts = lazy(() => import("./pages/AdminEmailAccounts"));
const AdminLanding = lazy(() => import("./pages/AdminLanding"));
const AdminGoogleServices = lazy(() => import("./pages/AdminGoogleServices"));
const AdminSupport = lazy(() => import("./pages/AdminSupport"));

// Components
import Sidebar from "./components/Sidebar";
import ErrorBoundary from "./components/ErrorBoundary";

// Hooks
import useGoogleScripts from "./hooks/useGoogleScripts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://");

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// WebSocket Context for real-time notifications
const WebSocketContext = createContext(null);

export const useWebSocket = () => useContext(WebSocketContext);

// Helper to read a cookie value by name
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

// API instance with auth — usa httpOnly cookie automáticamente (withCredentials)
export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  timeout: 10000  // 10s max per request - fail fast if backend is slow
});

// Attach CSRF token header to every mutating request (double-submit cookie pattern)
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

// Response interceptor: auto-refresh on 401, redirect on final failure
let isRefreshing = false;
let refreshQueue = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const currentPath = window.location.hash || window.location.pathname;
    const isAuthPage = currentPath.includes('/login') || currentPath.includes('/register') || currentPath.includes('/forgot-password');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthPage) {
      // Don't retry refresh endpoint itself
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem("user");
        window.location.href = "/#/login";
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then(() => api(originalRequest));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await api.post("/auth/refresh");
        // Refresh successful — retry queued requests
        refreshQueue.forEach(({ resolve }) => resolve());
        refreshQueue = [];
        return api(originalRequest);
      } catch (refreshError) {
        refreshQueue.forEach(({ reject }) => reject(refreshError));
        refreshQueue = [];
        localStorage.removeItem("user");
        window.location.href = "/#/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 401 && !isAuthPage) {
      localStorage.removeItem("user");
      window.location.href = "/#/login";
    }

    return Promise.reject(error);
  }
);

// Home redirect: superadmin → /admin/dashboard, others → Dashboard
const HomeRedirect = () => {
  const { user } = useAuth();
  if (user?.role === "superadmin") {
    return <Navigate to="/admin/dashboard" replace />;
  }
  return <Dashboard />;
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Main Layout with Sidebar + Error Boundary per page
const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="app-container">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <main className="main-content">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    </div>
  );
};

// Auth Provider with WebSocket support
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const userIdRef = useRef(null);

  // WebSocket connection
  const connectWebSocket = useCallback((userId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    userIdRef.current = userId;

    try {
      const ws = new WebSocket(`${WS_URL}/ws/notifications/${userId}`);

      ws.onopen = () => {
        setWsConnected(true);
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000);
        ws.pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        if (event.data === "pong") return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === "notification") {
            const notif = data.data;
            if (notif.type === "sync_progress") {
              toast.loading(notif.message, { id: "sync-progress", duration: 30000 });
            } else if (notif.type === "sync_complete") {
              toast.dismiss("sync-progress");
              toast.success(notif.message, { duration: 5000 });
            } else if (notif.type === "sync_error") {
              toast.dismiss("sync-progress");
              toast.error(notif.message, { duration: 8000 });
            } else if (notif.type === "price_change") {
              toast.info(notif.message, { duration: 5000 });
            } else if (notif.type === "stock_out" || notif.type === "stock_low") {
              toast.warning(notif.message, { duration: 5000 });
            }
          }
        } catch (e) {
          // ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (ws.pingInterval) clearInterval(ws.pingInterval);
        // Reconnect after 5 seconds using ref to avoid stale closure
        if (userIdRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => connectWebSocket(userIdRef.current), 5000);
        }
      };

      ws.onerror = () => {};

      wsRef.current = ws;
    } catch (error) {
      // WebSocket connection failed silently
    }
  }, []);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      if (wsRef.current.pingInterval) clearInterval(wsRef.current.pingInterval);
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsConnected(false);
  }, []);

  useEffect(() => {
    // Inicializa usuario desde caché local y luego valida con el servidor (via cookie httpOnly)
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)); } catch (_) {}
    }
    // NO BLOQUEAR: setear loading=false inmediatamente, validar JWT en background
    setLoading(false);

    // Validar JWT de forma asincrónica sin bloquear la UI
    api.get("/auth/me")
      .then((res) => {
        setUser(res.data);
        localStorage.setItem("user", JSON.stringify(res.data));
        connectWebSocket(res.data.id);
      })
      .catch(() => {
        localStorage.removeItem("user");
        setUser(null);
        // Si JWT inválido/expirado, ProtectedRoute redirige a /login automáticamente
      });

    return () => disconnectWebSocket();
  }, [connectWebSocket, disconnectWebSocket]);

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    const { user: userData } = res.data;
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    connectWebSocket(userData.id);
    return userData;
  };

  const register = async (data) => {
    const res = await api.post("/auth/register", data);
    const { user: userData } = res.data;
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    connectWebSocket(userData.id);
    return userData;
  };

  const logout = async () => {
    userIdRef.current = null;
    disconnectWebSocket();
    try { await api.post("/auth/logout"); } catch (_) {}
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      <WebSocketContext.Provider value={{ connected: wsConnected }}>
        {children}
      </WebSocketContext.Provider>
    </AuthContext.Provider>
  );
};

function App() {
  useGoogleScripts();

  return (
    <ErrorBoundary>
    <HashRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          richColors
          toastOptions={{
            style: { fontFamily: 'Inter, sans-serif' }
          }}
        />
        <Suspense fallback={
          <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <div className="spinner"></div>
          </div>
        }>
        <Routes>
          {/* Setup Route */}
          <Route path="/setup" element={<Setup />} />
          
          {/* Landing Page (Public) */}
          <Route path="/landing" element={<Landing />} />
          
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ForgotPassword />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <HomeRedirect />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/suppliers"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Suppliers />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/suppliers/:supplierId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SupplierDetail />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/products"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Products />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalogs"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Catalogs />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalogs/:catalogId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <CatalogDetail />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalog"
            element={<Navigate to="/catalogs" replace />}
          />
          <Route
            path="/margin-rules"
            element={<Navigate to="/catalogs" replace />}
          />
          <Route
            path="/export"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Export />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/stores"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <WooCommerceExport />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/marketplaces"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Marketplaces />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/price-history"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <PriceHistory />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Notifications />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/sync-history"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SyncHistory />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/webhooks"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Webhooks />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <UserManagement />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SuperAdminDashboard />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/subscriptions"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Subscriptions />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Profile />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/email-config"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <EmailConfig />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/support"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Support />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SuperAdminDashboard />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <UserManagement />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/plans"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminPlans />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/subscriptions"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminPlans />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/stripe"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminStripe />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/branding"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminBranding />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/email-config"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminEmailAccounts />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/email-templates"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminEmailTemplates />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/landing"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminLanding />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/google-services"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminGoogleServices />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/support"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AdminSupport />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* CRM Route */}
          <Route
            path="/crm"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <CRMPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* Sync Settings Route */}
          <Route
            path="/sync-settings"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SyncSettings />
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </Suspense>
      </AuthProvider>
    </HashRouter>
    </ErrorBoundary>
  );
}

export default App;
