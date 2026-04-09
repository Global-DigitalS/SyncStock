import { useState, useEffect, createContext, useContext, useCallback, useRef } from "react";
import { toast } from "sonner";
import posthog from "posthog-js";

import { api, WS_URL } from "../lib/api";

// Auth Context
export const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// WebSocket Context para notificaciones en tiempo real
const WebSocketContext = createContext(null);
export const useWebSocket = () => useContext(WebSocketContext);

// Auth Provider: gestiona autenticación + conexión WebSocket
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const userIdRef = useRef(null);
  const wsRetriesRef = useRef(0);

  // Conexión WebSocket con reconexión exponencial + jitter
  const connectWebSocket = useCallback((userId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    userIdRef.current = userId;

    try {
      const ws = new WebSocket(`${WS_URL}/ws/notifications/${userId}`);

      ws.onopen = () => {
        wsRetriesRef.current = 0;
        setWsConnected(true);
        // Ping cada 30 segundos para mantener la conexión viva
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

          if (data.type === "heartbeat") {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "heartbeat_ack", timestamp: Date.now() }));
            }
            return;
          }

          if (data.type === "pong") return;

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
          // Ignorar mensajes no-JSON
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (ws.pingInterval) clearInterval(ws.pingInterval);
        // Reconexión con backoff exponencial + jitter para evitar thundering herd
        if (userIdRef.current) {
          const retries = wsRetriesRef.current;
          const baseDelay = Math.min(1000 * Math.pow(2, retries), 30000); // máx 30s
          const jitter = Math.random() * baseDelay * 0.5;
          const delay = baseDelay + jitter;
          wsRetriesRef.current = retries + 1;
          reconnectTimeoutRef.current = setTimeout(() => connectWebSocket(userIdRef.current), delay);
        }
      };

      ws.onerror = () => {};

      wsRef.current = ws;
    } catch (error) {
      // Fallo silencioso — WebSocket es opcional
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
    // Inicializa usuario desde caché local y luego valida con el servidor
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.debug("Error al parsear usuario en caché", e);
      }
    }
    // Sin bloqueo: setear loading=false inmediatamente, validar JWT en background
    setLoading(false);

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
    posthog.identify(userData.id, { email: userData.email, role: userData.role, name: userData.name });
    return userData;
  };

  const register = async (data) => {
    const res = await api.post("/auth/register", data);
    const { user: userData } = res.data;
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    connectWebSocket(userData.id);
    posthog.identify(userData.id, { email: userData.email, role: userData.role, name: userData.name });
    return userData;
  };

  const logout = async () => {
    userIdRef.current = null;
    disconnectWebSocket();
    try {
      await api.post("/auth/logout");
    } catch (e) {
      console.debug("Error en logout (esperado)", e);
    }
    localStorage.removeItem("user");
    setUser(null);
    posthog.reset();
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      <WebSocketContext.Provider value={{ connected: wsConnected }}>
        {children}
      </WebSocketContext.Provider>
    </AuthContext.Provider>
  );
};
