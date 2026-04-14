import "@/App.css";
import { HashRouter } from "react-router-dom";
import { Toaster } from "sonner";

import { AuthProvider, AuthContext, useAuth, useWebSocket } from "./contexts/AuthContext";
import { SyncProgressProvider } from "./contexts/SyncProgressContext";
import SyncProgressPanel from "./components/sync/SyncProgressPanel";
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
          <SyncProgressProvider>
            <Toaster
              position="top-right"
              richColors
              toastOptions={{
                style: { fontFamily: 'Inter, sans-serif' }
              }}
            />
            <SyncProgressPanel />
            <AppRouter />
          </SyncProgressProvider>
        </AuthProvider>
      </HashRouter>
    </ErrorBoundary>
  );
}

export default App;
