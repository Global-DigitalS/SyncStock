import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, Sun, Moon, ChevronDown } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn, Button } from "./ui";

const NAV_LINKS = [
  { label: "Características", href: "/caracteristicas" },
  { label: "Integraciones", href: "/#integrations" },
  { label: "Precios", href: "/precios" },
  { label: "Blog", href: "/blog" },
  { label: "Nosotros", href: "/nosotros" },
];

export default function Navbar() {
  const { branding, theme, toggleTheme, APP_URL, API_URL } = useApp();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const dark = theme === "dark";

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => { setOpen(false); }, [location.pathname]);

  const logoSrc = branding.logo_url
    ? (branding.logo_url.startsWith("http") ? branding.logo_url : `${API_URL}${branding.logo_url}`)
    : null;

  const isActive = (href) => {
    if (href.startsWith("/#")) return false;
    return location.pathname === href;
  };

  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
      scrolled
        ? dark ? "bg-slate-900/95 backdrop-blur-md shadow-lg border-b border-slate-800" : "bg-white/95 backdrop-blur-md shadow-sm border-b border-slate-100"
        : dark ? "bg-transparent" : "bg-transparent"
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-18">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 flex-shrink-0">
            {logoSrc ? (
              <img src={logoSrc} alt={branding.app_name} className="h-8 w-auto object-contain" />
            ) : (
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-sm">{branding.app_name?.[0] || "S"}</span>
              </div>
            )}
            <span className={cn("font-bold text-lg hidden sm:block", dark ? "text-white" : "text-slate-900")}>
              {branding.app_name}
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {NAV_LINKS.map(link => (
              link.href.startsWith("/#") ? (
                <a
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    dark ? "text-slate-300 hover:text-white hover:bg-slate-800" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.href}
                  to={link.href}
                  className={cn(
                    "px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive(link.href)
                      ? dark ? "text-white bg-slate-800" : "text-indigo-600 bg-indigo-50"
                      : dark ? "text-slate-300 hover:text-white hover:bg-slate-800" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  )}
                >
                  {link.label}
                </Link>
              )
            ))}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className={cn(
                "p-2 rounded-lg transition-colors theme-toggle-icon",
                dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
              )}
              aria-label="Cambiar tema"
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <a
              href={`${APP_URL}/#/login`}
              className={cn(
                "hidden sm:inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                dark ? "text-slate-300 hover:text-white hover:bg-slate-800" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              )}
            >
              Iniciar sesión
            </a>

            <a
              href={`${APP_URL}/#/register`}
              className="hidden sm:inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-sm"
            >
              Prueba gratis
            </a>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setOpen(v => !v)}
              className={cn(
                "lg:hidden p-2 rounded-lg transition-colors",
                dark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-100"
              )}
              aria-label="Menú"
            >
              {open ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {open && (
          <div className={cn(
            "lg:hidden border-t py-4 mobile-menu-enter",
            dark ? "border-slate-800 bg-slate-900" : "border-slate-100 bg-white"
          )}>
            <div className="flex flex-col gap-1 mb-4">
              {NAV_LINKS.map(link => (
                link.href.startsWith("/#") ? (
                  <a
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "px-4 py-3 rounded-lg text-sm font-medium",
                      dark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-50"
                    )}
                  >
                    {link.label}
                  </a>
                ) : (
                  <Link
                    key={link.href}
                    to={link.href}
                    className={cn(
                      "px-4 py-3 rounded-lg text-sm font-medium",
                      isActive(link.href)
                        ? dark ? "text-white bg-slate-800" : "text-indigo-600 bg-indigo-50"
                        : dark ? "text-slate-300 hover:bg-slate-800" : "text-slate-700 hover:bg-slate-50"
                    )}
                  >
                    {link.label}
                  </Link>
                )
              ))}
            </div>
            <div className="flex flex-col gap-2 px-4">
              <a
                href={`${APP_URL}/#/login`}
                className={cn(
                  "w-full text-center px-4 py-3 rounded-lg text-sm font-medium border transition-colors",
                  dark ? "border-slate-700 text-slate-300 hover:bg-slate-800" : "border-slate-200 text-slate-700 hover:bg-slate-50"
                )}
              >
                Iniciar sesión
              </a>
              <a
                href={`${APP_URL}/#/register`}
                className="w-full text-center px-4 py-3 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
              >
                Prueba gratis — 14 días
              </a>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
