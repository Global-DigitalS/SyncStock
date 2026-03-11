import { Link } from "react-router-dom";
import { Twitter, Linkedin, Facebook, Mail, ExternalLink } from "lucide-react";
import { useApp } from "../context/AppContext";
import { cn } from "./ui";

const PRODUCT_LINKS = [
  { label: "Características", href: "/caracteristicas" },
  { label: "Precios", href: "/precios" },
  { label: "Integraciones", href: "/#integrations" },
  { label: "Blog", href: "/blog" },
];

const COMPANY_LINKS = [
  { label: "Nosotros", href: "/nosotros" },
  { label: "Contacto", href: "/contacto" },
];

const LEGAL_LINKS = [
  { label: "Privacidad", href: "/privacidad" },
  { label: "Términos", href: "/terminos" },
];

export default function Footer() {
  const { branding, content, theme, APP_URL, API_URL } = useApp();
  const dark = theme === "dark";
  const year = new Date().getFullYear();

  const logoSrc = branding.logo_url
    ? (branding.logo_url.startsWith("http") ? branding.logo_url : `${API_URL}${branding.logo_url}`)
    : null;

  const social = content?.footer?.social || {};
  const companyDesc = content?.footer?.company_description || `${branding.app_name} es la plataforma líder en sincronización de inventarios para eCommerce.`;
  const footerText = branding.footer_text;

  return (
    <footer className={cn(
      "border-t",
      dark ? "bg-slate-900 border-slate-800" : "bg-slate-50 border-slate-200"
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">

          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-4">
              {logoSrc ? (
                <img src={logoSrc} alt={branding.app_name} className="h-8 w-auto object-contain" />
              ) : (
                <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">{branding.app_name?.[0] || "S"}</span>
                </div>
              )}
              <span className={cn("font-bold text-lg", dark ? "text-white" : "text-slate-900")}>
                {branding.app_name}
              </span>
            </Link>
            <p className={cn("text-sm leading-relaxed mb-4", dark ? "text-slate-400" : "text-slate-500")}>
              {companyDesc}
            </p>
            {/* Social links */}
            <div className="flex items-center gap-2">
              {social.twitter && (
                <a href={social.twitter} target="_blank" rel="noopener noreferrer"
                  className={cn("p-2 rounded-lg transition-colors", dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                  <Twitter size={16} />
                </a>
              )}
              {social.linkedin && (
                <a href={social.linkedin} target="_blank" rel="noopener noreferrer"
                  className={cn("p-2 rounded-lg transition-colors", dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                  <Linkedin size={16} />
                </a>
              )}
              {social.facebook && (
                <a href={social.facebook} target="_blank" rel="noopener noreferrer"
                  className={cn("p-2 rounded-lg transition-colors", dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                  <Facebook size={16} />
                </a>
              )}
              <a href="/contacto"
                className={cn("p-2 rounded-lg transition-colors", dark ? "text-slate-400 hover:text-white hover:bg-slate-800" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                <Mail size={16} />
              </a>
            </div>
          </div>

          {/* Producto */}
          <div>
            <h3 className={cn("font-semibold text-sm mb-4", dark ? "text-white" : "text-slate-900")}>
              Producto
            </h3>
            <ul className="space-y-2.5">
              {PRODUCT_LINKS.map(link => (
                <li key={link.href}>
                  {link.href.startsWith("/#") ? (
                    <a href={link.href} className={cn("text-sm transition-colors", dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-900")}>
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className={cn("text-sm transition-colors", dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-900")}>
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
              <li>
                <a href={`${APP_URL}/#/register`} className={cn("text-sm transition-colors flex items-center gap-1", dark ? "text-indigo-400 hover:text-indigo-300" : "text-indigo-600 hover:text-indigo-700")}>
                  Prueba gratuita <ExternalLink size={12} />
                </a>
              </li>
            </ul>
          </div>

          {/* Empresa */}
          <div>
            <h3 className={cn("font-semibold text-sm mb-4", dark ? "text-white" : "text-slate-900")}>
              Empresa
            </h3>
            <ul className="space-y-2.5">
              {COMPANY_LINKS.map(link => (
                <li key={link.href}>
                  <Link to={link.href} className={cn("text-sm transition-colors", dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-900")}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className={cn("font-semibold text-sm mb-4", dark ? "text-white" : "text-slate-900")}>
              Legal
            </h3>
            <ul className="space-y-2.5">
              {LEGAL_LINKS.map(link => (
                <li key={link.href}>
                  <Link to={link.href} className={cn("text-sm transition-colors", dark ? "text-slate-400 hover:text-white" : "text-slate-500 hover:text-slate-900")}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className={cn("border-t mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4", dark ? "border-slate-800" : "border-slate-200")}>
          <p className={cn("text-sm", dark ? "text-slate-500" : "text-slate-400")}>
            {footerText || `© ${year} ${branding.app_name}. Todos los derechos reservados.`}
          </p>
          <div className="flex items-center gap-4">
            {LEGAL_LINKS.map(link => (
              <Link
                key={link.href}
                to={link.href}
                className={cn("text-xs transition-colors", dark ? "text-slate-500 hover:text-slate-300" : "text-slate-400 hover:text-slate-600")}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
