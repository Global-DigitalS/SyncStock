import { useLocation, Link, useNavigate } from "react-router-dom";
import { useAuth, api } from "../App";
import { useState, useEffect } from "react";
import axios from "axios";
import {
  LayoutDashboard,
  Truck,
  Package,
  BookOpen,
  Download,
  Store,
  TrendingUp,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  History,
  Users,
  Wifi,
  WifiOff,
  Crown,
  CreditCard,
  Webhook,
  Mail,
  Palette,
  FileText,
  Settings,
  ChevronDown,
  ChevronRight,
  DollarSign,
  Link2,
  Building2,
  RefreshCw,
  Layout,
  BarChart3,
  LifeBuoy
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const navItems = [
  { path: "/", label: "Panel de Control", icon: LayoutDashboard },
  { path: "/suppliers", label: "Proveedores", icon: Truck },
  { path: "/products", label: "Productos", icon: Package },
  { path: "/catalogs", label: "Catálogos", icon: BookOpen },
  { path: "/export", label: "Exportar", icon: Download },
  { path: "/webhooks", label: "Webhooks", icon: Webhook },
  { path: "/price-history", label: "Historial de Precios", icon: TrendingUp },
  { path: "/sync-history", label: "Historial de Syncs", icon: History },
  { path: "/sync-settings", label: "Sincronización", icon: RefreshCw },
  { path: "/notifications", label: "Notificaciones", icon: Bell },
  { path: "/subscriptions", label: "Suscripciones", icon: CreditCard },
];

// Conexiones submenu items
const connectionItems = [
  { path: "/stores", label: "Tiendas", icon: Store },
  { path: "/crm", label: "CRM", icon: Building2 },
];

const adminItems = [
  { path: "/admin/users", label: "Usuarios", icon: Users },
  { path: "/admin/subscriptions", label: "Suscripciones", icon: CreditCard },
  { path: "/admin/stripe", label: "Config. Stripe", icon: DollarSign },
  { path: "/admin/branding", label: "Personalización", icon: Palette },
  { path: "/admin/landing", label: "Landing Page", icon: Layout },
  { path: "/admin/email-config", label: "Config. Email", icon: Mail },
  { path: "/admin/email-templates", label: "Plantillas Email", icon: FileText },
  { path: "/admin/google-services", label: "Google Services", icon: BarChart3 },
  { path: "/admin/support", label: "Soporte / Tickets", icon: LifeBuoy },
];

const Sidebar = ({ open, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [adminExpanded, setAdminExpanded] = useState(true);
  const [connectionsExpanded, setConnectionsExpanded] = useState(false);
  const [generalExpanded, setGeneralExpanded] = useState(false);
  const [branding, setBranding] = useState({
    app_name: "StockHub",
    app_slogan: "Gestión de Catálogos",
    logo_url: null,
    primary_color: "#4f46e5"
  });

  // Load branding
  useEffect(() => {
    const loadBranding = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/branding/public`);
        if (res.data) {
          setBranding(prev => ({ ...prev, ...res.data }));
          // Update page title
          if (res.data.page_title) {
            document.title = res.data.page_title;
          }
        }
      } catch (error) {
        console.log("Using default branding");
      }
    };
    loadBranding();
  }, []);

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        const res = await api.get("/notifications?unread_only=true&limit=1");
        const statsRes = await api.get("/dashboard/stats");
        setUnreadCount(statsRes.data.unread_notifications);
      } catch (error) {
        console.error("Error fetching notifications:", error);
      }
    };
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  // Auto-expand sections based on current route
  useEffect(() => {
    if (location.pathname.startsWith("/admin")) {
      setAdminExpanded(true);
    }
    if (location.pathname === "/stores" || location.pathname === "/crm") {
      setConnectionsExpanded(true);
      setGeneralExpanded(true);
    }
    // If superadmin navigates to a general route, expand the general menu
    const generalPaths = navItems.map((i) => i.path);
    if (generalPaths.some((p) => p !== "/" ? location.pathname.startsWith(p) : location.pathname === "/")) {
      setGeneralExpanded(true);
    }
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  const isSuperAdmin = user?.role === "superadmin";

  const NavContent = () => (
    <>
      {/* Logo */}
      <div className="p-6 border-b border-slate-200">
        <Link to="/" className="flex items-center gap-3">
          {branding.logo_url ? (
            <img 
              src={branding.logo_url.startsWith('/') ? `${BACKEND_URL}${branding.logo_url}` : branding.logo_url}
              alt={branding.app_name}
              className="h-10 object-contain"
            />
          ) : (
            <div 
              className="w-10 h-10 rounded-sm flex items-center justify-center"
              style={{ backgroundColor: branding.primary_color }}
            >
              <Package className="w-6 h-6 text-white" strokeWidth={1.5} />
            </div>
          )}
          <div>
            <h1 className="font-bold text-lg text-slate-900 tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {branding.app_name}
            </h1>
            <p className="text-xs text-slate-500">{branding.app_slogan}</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">

        {/* ── SuperAdmin: Administración primero ── */}
        {isSuperAdmin && (
          <div className="mb-2">
            <Link
              to="/admin/dashboard"
              onClick={() => setAdminExpanded(!adminExpanded)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-sm transition-all duration-200 font-medium ${
                location.pathname === "/admin/dashboard"
                  ? "bg-purple-100 text-purple-700"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
              data-testid="admin-section-toggle"
            >
              <div className="flex items-center gap-3">
                <Crown className="w-5 h-5 text-purple-600" strokeWidth={1.5} />
                <span className="text-purple-700 font-semibold">Administración</span>
              </div>
              {adminExpanded ? (
                <ChevronDown className="w-4 h-4 text-purple-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-purple-500" />
              )}
            </Link>

            {adminExpanded && (
              <div className="mt-1 ml-2 space-y-1">
                {adminItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      data-testid={`nav-${item.path.replace("/admin/", "admin-")}`}
                      className={`flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-all duration-200 ${
                        active
                          ? "bg-purple-100 text-purple-700 font-medium"
                          : "text-slate-600 hover:bg-purple-50 hover:text-purple-700"
                      }`}
                      onClick={() => setMobileOpen(false)}
                    >
                      <Icon className="w-4 h-4" strokeWidth={1.5} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ── Menú general: siempre visible para no-superadmin, colapsable para superadmin ── */}
        {isSuperAdmin ? (
          <div className="pt-2 border-t border-slate-200">
            <button
              onClick={() => setGeneralExpanded(!generalExpanded)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-sm transition-all duration-200 font-medium text-slate-600 hover:bg-slate-50"
              data-testid="general-section-toggle"
            >
              <div className="flex items-center gap-3">
                <LayoutDashboard className="w-5 h-5 text-slate-500" strokeWidth={1.5} />
                <span className="text-slate-600 font-semibold">Menú general</span>
              </div>
              {generalExpanded ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {generalExpanded && (
              <div className="mt-1 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  const showBadge = item.path === "/notifications" && unreadCount > 0;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      data-testid={`nav-${item.path.replace("/", "") || "dashboard"}`}
                      className={active ? "sidebar-item-active" : "sidebar-item"}
                      onClick={() => setMobileOpen(false)}
                    >
                      <div className="relative">
                        <Icon className="w-5 h-5" strokeWidth={1.5} />
                        {showBadge && (
                          <span className="notification-badge">{unreadCount > 99 ? "99+" : unreadCount}</span>
                        )}
                      </div>
                      <span>{item.label}</span>
                    </Link>
                  );
                })}

                {/* Conexiones dentro del menú general colapsado */}
                <div className="pt-1">
                  <button
                    onClick={() => setConnectionsExpanded(!connectionsExpanded)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-sm transition-all duration-200 font-medium ${
                      (location.pathname === "/stores" || location.pathname === "/crm")
                        ? "bg-blue-100 text-blue-700"
                        : "text-slate-600 hover:bg-slate-50"
                    }`}
                    data-testid="connections-section-toggle"
                  >
                    <div className="flex items-center gap-3">
                      <Link2 className="w-5 h-5 text-blue-600" strokeWidth={1.5} />
                      <span className="text-blue-700 font-semibold">Conexiones</span>
                    </div>
                    {connectionsExpanded ? (
                      <ChevronDown className="w-4 h-4 text-blue-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-blue-500" />
                    )}
                  </button>

                  {connectionsExpanded && (
                    <div className="mt-1 ml-2 space-y-1">
                      {connectionItems.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            data-testid={`nav-${item.path.replace("/", "")}`}
                            className={`flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-all duration-200 ${
                              active
                                ? "bg-blue-100 text-blue-700 font-medium"
                                : "text-slate-600 hover:bg-blue-50 hover:text-blue-700"
                            }`}
                            onClick={() => setMobileOpen(false)}
                          >
                            <Icon className="w-4 h-4" strokeWidth={1.5} />
                            <span>{item.label}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Menú normal para no-superadmin */
          <>
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              const showBadge = item.path === "/notifications" && unreadCount > 0;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.path.replace("/", "") || "dashboard"}`}
                  className={active ? "sidebar-item-active" : "sidebar-item"}
                  onClick={() => setMobileOpen(false)}
                >
                  <div className="relative">
                    <Icon className="w-5 h-5" strokeWidth={1.5} />
                    {showBadge && (
                      <span className="notification-badge">{unreadCount > 99 ? "99+" : unreadCount}</span>
                    )}
                  </div>
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* Conexiones Section */}
            <div className="pt-2 mt-2">
              <button
                onClick={() => setConnectionsExpanded(!connectionsExpanded)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-sm transition-all duration-200 font-medium ${
                  (location.pathname === "/stores" || location.pathname === "/crm")
                    ? "bg-blue-100 text-blue-700"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
                data-testid="connections-section-toggle"
              >
                <div className="flex items-center gap-3">
                  <Link2 className="w-5 h-5 text-blue-600" strokeWidth={1.5} />
                  <span className="text-blue-700 font-semibold">Conexiones</span>
                </div>
                {connectionsExpanded ? (
                  <ChevronDown className="w-4 h-4 text-blue-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-blue-500" />
                )}
              </button>

              {connectionsExpanded && (
                <div className="mt-1 ml-2 space-y-1">
                  {connectionItems.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.path);
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        data-testid={`nav-${item.path.replace("/", "")}`}
                        className={`flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-all duration-200 ${
                          active
                            ? "bg-blue-100 text-blue-700 font-medium"
                            : "text-slate-600 hover:bg-blue-50 hover:text-blue-700"
                        }`}
                        onClick={() => setMobileOpen(false)}
                      >
                        <Icon className="w-4 h-4" strokeWidth={1.5} />
                        <span>{item.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-slate-200">
        <Link
          to="/profile"
          data-testid="nav-profile"
          className={`flex items-center gap-3 px-3 py-2 mb-2 rounded-sm transition-all duration-200 ${
            location.pathname === "/profile"
              ? "bg-indigo-50 text-indigo-700"
              : "hover:bg-slate-50"
          }`}
          onClick={() => setMobileOpen(false)}
        >
          <div className="w-9 h-9 bg-slate-200 rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-slate-600">
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
          <Settings className="w-4 h-4 text-slate-400" />
        </Link>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-all duration-200 font-medium"
        >
          <LogOut className="w-5 h-5" strokeWidth={1.5} />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-slate-200 rounded-sm shadow-sm"
        onClick={() => setMobileOpen(!mobileOpen)}
        data-testid="mobile-menu-btn"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`lg:hidden fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200 z-50 transform transition-transform duration-300 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          <NavContent />
        </div>
      </aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200 flex-col z-30">
        <NavContent />
      </aside>
    </>
  );
};

export default Sidebar;
