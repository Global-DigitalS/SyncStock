import { useLocation, Link, useNavigate } from "react-router-dom";
import { useAuth, api } from "../App";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Truck,
  Package,
  BookOpen,
  Percent,
  Download,
  ShoppingCart,
  TrendingUp,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronLeft
} from "lucide-react";

const navItems = [
  { path: "/", label: "Panel de Control", icon: LayoutDashboard },
  { path: "/suppliers", label: "Proveedores", icon: Truck },
  { path: "/products", label: "Productos", icon: Package },
  { path: "/catalogs", label: "Catálogos", icon: BookOpen },
  { path: "/margin-rules", label: "Reglas de Margen", icon: Percent },
  { path: "/export", label: "Exportar", icon: Download },
  { path: "/woocommerce", label: "WooCommerce", icon: ShoppingCart },
  { path: "/price-history", label: "Historial de Precios", icon: TrendingUp },
  { path: "/notifications", label: "Notificaciones", icon: Bell },
];

const Sidebar = ({ open, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

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

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  const NavContent = () => (
    <>
      {/* Logo */}
      <div className="p-6 border-b border-slate-200">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-sm flex items-center justify-center">
            <Package className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900 tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
              StockHub
            </h1>
            <p className="text-xs text-slate-500">Gestión de Catálogos</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
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
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-9 h-9 bg-slate-200 rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-slate-600">
              {user?.name?.charAt(0).toUpperCase() || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
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
