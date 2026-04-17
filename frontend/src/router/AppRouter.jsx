import { useState, lazy, Suspense } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import posthog from "posthog-js";

import { useAuth } from "../contexts/AuthContext";
import Sidebar from "../components/Sidebar";
import ErrorBoundary from "../components/ErrorBoundary";

// Páginas — cargadas lazy para code splitting
const Login = lazy(() => import("../pages/Login"));
const Register = lazy(() => import("../pages/Register"));
const CheckoutSuccess = lazy(() => import("../pages/CheckoutSuccess"));
const Setup = lazy(() => import("../pages/Setup"));
const ForgotPassword = lazy(() => import("../pages/ForgotPassword"));
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Suppliers = lazy(() => import("../pages/Suppliers"));
const SupplierDetail = lazy(() => import("../pages/SupplierDetail"));
const Products = lazy(() => import("../pages/Products"));
const Catalogs = lazy(() => import("../pages/Catalogs"));
const CatalogDetail = lazy(() => import("../pages/CatalogDetail"));
const Export = lazy(() => import("../pages/Export"));
const WooCommerceExport = lazy(() => import("../pages/WooCommerceExport"));
const PriceHistory = lazy(() => import("../pages/PriceHistory"));
const Notifications = lazy(() => import("../pages/Notifications"));
const SyncHistory = lazy(() => import("../pages/SyncHistory"));
const UserManagement = lazy(() => import("../pages/UserManagement"));
const SuperAdminDashboard = lazy(() => import("../pages/SuperAdminDashboard"));
const Subscriptions = lazy(() => import("../pages/Subscriptions"));
const Webhooks = lazy(() => import("../pages/Webhooks"));
const EmailConfig = lazy(() => import("../pages/EmailConfig"));
const CRMPage = lazy(() => import("../pages/CRM"));
const Marketplaces = lazy(() => import("../pages/Marketplaces"));
const Competitors = lazy(() => import("../pages/Competitors"));
const SyncSettings = lazy(() => import("../pages/SyncSettings"));
const Profile = lazy(() => import("../pages/Profile"));
const Support = lazy(() => import("../pages/Support"));
const Landing = lazy(() => import("../pages/Landing"));
const Orders = lazy(() => import("../pages/Orders"));

// Páginas de administración
const AdminBranding = lazy(() => import("../pages/AdminBranding"));
const AdminPlans = lazy(() => import("../pages/AdminPlans"));
const AdminEmailTemplates = lazy(() => import("../pages/AdminEmailTemplates"));
const AdminStripe = lazy(() => import("../pages/AdminStripe"));
const AdminEmailAccounts = lazy(() => import("../pages/AdminEmailAccounts"));
const AdminLanding = lazy(() => import("../pages/AdminLanding"));
const AdminGoogleServices = lazy(() => import("../pages/AdminGoogleServices"));
const AdminSupport = lazy(() => import("../pages/AdminSupport"));
const PageManager = lazy(() => import("../pages/admin/PageManager"));
const PageEditor = lazy(() => import("../pages/admin/PageEditor"));

// Redirección de home: superadmin → /admin/dashboard, otros → Dashboard
const HomeRedirect = () => {
  const { user } = useAuth();
  if (user?.role === "superadmin") {
    return <Navigate to="/admin/dashboard" replace />;
  }
  return <Dashboard />;
};

// Ruta protegida — redirige a /login si no hay sesión activa
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

// Layout principal con Sidebar + ErrorBoundary por página
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

// Captura pageviews en cada cambio de ruta (necesario con HashRouter)
function PostHogPageviewTracker() {
  const location = useLocation();
  useEffect(() => {
    posthog.capture("$pageview");
  }, [location.pathname]);
  return null;
}

// Componente helper para rutas protegidas con layout
const ProtectedPage = ({ children }) => (
  <ProtectedRoute>
    <MainLayout>{children}</MainLayout>
  </ProtectedRoute>
);

export default function AppRouter() {
  return (
    <>
      <PostHogPageviewTracker />
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="spinner"></div>
        </div>
      }>
        <Routes>
          {/* Configuración inicial */}
          <Route path="/setup" element={<Setup />} />

          {/* Landing Page (público) */}
          <Route path="/landing" element={<Landing />} />

          {/* Rutas públicas */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/checkout-success" element={<CheckoutSuccess />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ForgotPassword />} />

          {/* Rutas protegidas */}
          <Route path="/" element={<ProtectedPage><HomeRedirect /></ProtectedPage>} />
          <Route path="/suppliers" element={<ProtectedPage><Suppliers /></ProtectedPage>} />
          <Route path="/suppliers/:supplierId" element={<ProtectedPage><SupplierDetail /></ProtectedPage>} />
          <Route path="/products" element={<ProtectedPage><Products /></ProtectedPage>} />
          <Route path="/catalogs" element={<ProtectedPage><Catalogs /></ProtectedPage>} />
          <Route path="/catalogs/:catalogId" element={<ProtectedPage><CatalogDetail /></ProtectedPage>} />
          <Route path="/catalog" element={<Navigate to="/catalogs" replace />} />
          <Route path="/margin-rules" element={<Navigate to="/catalogs" replace />} />
          <Route path="/export" element={<ProtectedPage><Export /></ProtectedPage>} />
          <Route path="/stores" element={<ProtectedPage><WooCommerceExport /></ProtectedPage>} />
          <Route path="/marketplaces" element={<ProtectedPage><Marketplaces /></ProtectedPage>} />
          <Route path="/competitors" element={<ProtectedPage><Competitors /></ProtectedPage>} />
          <Route path="/price-history" element={<ProtectedPage><PriceHistory /></ProtectedPage>} />
          <Route path="/notifications" element={<ProtectedPage><Notifications /></ProtectedPage>} />
          <Route path="/sync-history" element={<ProtectedPage><SyncHistory /></ProtectedPage>} />
          <Route path="/orders" element={<ProtectedPage><Orders /></ProtectedPage>} />
          <Route path="/webhooks" element={<ProtectedPage><Webhooks /></ProtectedPage>} />
          <Route path="/users" element={<ProtectedPage><UserManagement /></ProtectedPage>} />
          <Route path="/superadmin" element={<ProtectedPage><SuperAdminDashboard /></ProtectedPage>} />
          <Route path="/subscriptions" element={<ProtectedPage><Subscriptions /></ProtectedPage>} />
          <Route path="/profile" element={<ProtectedPage><Profile /></ProtectedPage>} />
          <Route path="/email-config" element={<ProtectedPage><EmailConfig /></ProtectedPage>} />
          <Route path="/support" element={<ProtectedPage><Support /></ProtectedPage>} />
          <Route path="/crm" element={<ProtectedPage><CRMPage /></ProtectedPage>} />
          <Route path="/sync-settings" element={<ProtectedPage><SyncSettings /></ProtectedPage>} />

          {/* Rutas de administración */}
          <Route path="/admin/dashboard" element={<ProtectedPage><SuperAdminDashboard /></ProtectedPage>} />
          <Route path="/admin/users" element={<ProtectedPage><UserManagement /></ProtectedPage>} />
          <Route path="/admin/plans" element={<ProtectedPage><AdminPlans /></ProtectedPage>} />
          <Route path="/admin/subscriptions" element={<ProtectedPage><AdminPlans /></ProtectedPage>} />
          <Route path="/admin/stripe" element={<ProtectedPage><AdminStripe /></ProtectedPage>} />
          <Route path="/admin/branding" element={<ProtectedPage><AdminBranding /></ProtectedPage>} />
          <Route path="/admin/email-config" element={<ProtectedPage><AdminEmailAccounts /></ProtectedPage>} />
          <Route path="/admin/email-templates" element={<ProtectedPage><AdminEmailTemplates /></ProtectedPage>} />
          <Route path="/admin/landing" element={<ProtectedPage><AdminLanding /></ProtectedPage>} />
          <Route path="/admin/google-services" element={<ProtectedPage><AdminGoogleServices /></ProtectedPage>} />
          <Route path="/admin/support" element={<ProtectedPage><AdminSupport /></ProtectedPage>} />
          <Route path="/admin/pages-list" element={<ProtectedPage><PageManager /></ProtectedPage>} />
          <Route path="/admin/pages" element={<ProtectedPage><PageEditor /></ProtectedPage>} />
          <Route path="/admin/pages/:id" element={<ProtectedPage><PageEditor /></ProtectedPage>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </>
  );
}
