import { useState, useEffect, createContext, useContext, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Pages
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Suppliers from "./pages/Suppliers";
import SupplierDetail from "./pages/SupplierDetail";
import Products from "./pages/Products";
import Catalogs from "./pages/Catalogs";
import CatalogDetail from "./pages/CatalogDetail";
import MarginRules from "./pages/MarginRules";
import Export from "./pages/Export";
import WooCommerceExport from "./pages/WooCommerceExport";
import PriceHistory from "./pages/PriceHistory";
import Notifications from "./pages/Notifications";
import SyncHistory from "./pages/SyncHistory";
import UserManagement from "./pages/UserManagement";
import SuperAdminDashboard from "./pages/SuperAdminDashboard";
import Subscriptions from "./pages/Subscriptions";
import Webhooks from "./pages/Webhooks";

// Components
import Sidebar from "./components/Sidebar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://");

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// WebSocket Context for real-time notifications
const WebSocketContext = createContext(null);

export const useWebSocket = () => useContext(WebSocketContext);

// API instance with auth
export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

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

// Main Layout with Sidebar
const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="app-container">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <main className="main-content">
        {children}
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

  // WebSocket connection
  const connectWebSocket = useCallback((userId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const ws = new WebSocket(`${WS_URL}/ws/notifications/${userId}`);
      
      ws.onopen = () => {
        console.log("WebSocket connected");
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
            // Show toast for real-time notification
            const notif = data.data;
            if (notif.type === "sync_complete") {
              toast.success(notif.message, { duration: 5000 });
            } else if (notif.type === "sync_error") {
              toast.error(notif.message, { duration: 8000 });
            } else if (notif.type === "price_change") {
              toast.info(notif.message, { duration: 5000 });
            } else if (notif.type === "stock_out" || notif.type === "stock_low") {
              toast.warning(notif.message, { duration: 5000 });
            }
          }
        } catch (e) {
          console.log("WS message:", event.data);
        }
      };
      
      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setWsConnected(false);
        if (ws.pingInterval) clearInterval(ws.pingInterval);
        // Reconnect after 5 seconds
        if (user) {
          reconnectTimeoutRef.current = setTimeout(() => connectWebSocket(userId), 5000);
        }
      };
      
      ws.onerror = (error) => {
        console.log("WebSocket error:", error);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.log("WebSocket connection failed:", error);
    }
  }, [user]);

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
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    
    if (token && savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      // Verify token is still valid
      api.get("/auth/me")
        .then((res) => {
          setUser(res.data);
          localStorage.setItem("user", JSON.stringify(res.data));
          connectWebSocket(res.data.id);
        })
        .catch(() => {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
    
    return () => disconnectWebSocket();
  }, []);

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    const { token, user: userData } = res.data;
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    connectWebSocket(userData.id);
    return userData;
  };

  const register = async (data) => {
    const res = await api.post("/auth/register", data);
    const { token, user: userData } = res.data;
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    connectWebSocket(userData.id);
    return userData;
  };

  const logout = () => {
    disconnectWebSocket();
    localStorage.removeItem("token");
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
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster 
          position="top-right" 
          richColors 
          toastOptions={{
            style: { fontFamily: 'Inter, sans-serif' }
          }}
        />
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
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
            element={
              <ProtectedRoute>
                <MainLayout>
                  <MarginRules />
                </MainLayout>
              </ProtectedRoute>
            }
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

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
