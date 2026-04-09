import "@/App.css";
import { HashRouter } from "react-router-dom";
import { Toaster } from "sonner";

import { AuthProvider, AuthContext, useAuth, useWebSocket } from "./contexts/AuthContext";
import AppRouter from "./router/AppRouter";
import ErrorBoundary from "./components/ErrorBoundary";
import useGoogleScripts from "./hooks/useGoogleScripts";

// Re-exports para compatibilidad — todos los módulos importan desde aquí
export { api } from "./lib/api";
export { AuthContext, useAuth, useWebSocket };

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
          <AppRouter />
        </AuthProvider>
      </HashRouter>
    </ErrorBoundary>
  );
}

export default App;
