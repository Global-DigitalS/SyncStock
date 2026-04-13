import { Link } from "react-router-dom";
import { Twitter, Linkedin, Facebook, Mail, ExternalLink } from "lucide-react";
import { useApp } from "../context/AppContext";

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

const SOCIAL_CLASS = "p-2.5 rounded-lg transition-all hover:scale-110 text-slate-500 hover:text-white hover:bg-slate-800";
const LINK_CLASS = "text-sm text-slate-500 hover:text-slate-300 transition-colors";

export default function Footer() {
  const { branding, content, APP_URL, API_URL } = useApp();
  const year = new Date().getFullYear();

  const logoSrc = branding.logo_url
    ? (branding.logo_url.startsWith("http") ? branding.logo_url : `${API_URL}${branding.logo_url}`)
    : null;

  const social = content?.footer?.social || {};
  const companyDesc = content?.footer?.company_description || `${branding.app_name} es la plataforma líder en sincronización de inventarios para eCommerce.`;
  const footerText = branding.footer_text;

  return (
    <footer className="bg-slate-950 border-t border-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">

          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-3 mb-5">
              {logoSrc ? (
                <img src={logoSrc} alt={branding.app_name} className="h-10 w-auto object-contain" />
              ) : (
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-lg flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-base">{branding.app_name?.[0] || "S"}</span>
                </div>
              )}
              <span className="font-display font-bold text-lg text-white">
                {branding.app_name}
              </span>
            </Link>
            <p className="text-sm leading-relaxed mb-6 text-slate-400">
              {companyDesc}
            </p>
            {/* Social links */}
            <div className="flex items-center gap-3">
              {social.twitter && (
                <a href={social.twitter} target="_blank" rel="noopener noreferrer" className={SOCIAL_CLASS}>
                  <Twitter size={18} />
                </a>
              )}
              {social.linkedin && (
                <a href={social.linkedin} target="_blank" rel="noopener noreferrer" className={SOCIAL_CLASS}>
                  <Linkedin size={18} />
                </a>
              )}
              {social.facebook && (
                <a href={social.facebook} target="_blank" rel="noopener noreferrer" className={SOCIAL_CLASS}>
                  <Facebook size={18} />
                </a>
              )}
              <a href="/contacto" className={SOCIAL_CLASS}>
                <Mail size={18} />
              </a>
            </div>
          </div>

          {/* Producto */}
          <div>
            <h3 className="font-display font-bold text-sm uppercase tracking-widest text-slate-500 mb-5">
              Producto
            </h3>
            <ul className="space-y-3">
              {PRODUCT_LINKS.map(link => (
                <li key={link.href}>
                  {link.href.startsWith("/#") ? (
                    <a href={link.href} className={LINK_CLASS}>
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className={LINK_CLASS}>
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
              <li>
                <a href={`${APP_URL}/#/register`} className="text-sm font-semibold transition-colors flex items-center gap-2 text-indigo-400 hover:text-indigo-300">
                  Prueba Gratuita <ExternalLink size={14} />
                </a>
              </li>
            </ul>
          </div>

          {/* Empresa */}
          <div>
            <h3 className="font-display font-bold text-sm uppercase tracking-widest text-slate-500 mb-5">
              Empresa
            </h3>
            <ul className="space-y-3">
              {COMPANY_LINKS.map(link => (
                <li key={link.href}>
                  <Link to={link.href} className={LINK_CLASS}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-display font-bold text-sm uppercase tracking-widest text-slate-500 mb-5">
              Legal
            </h3>
            <ul className="space-y-3">
              {LEGAL_LINKS.map(link => (
                <li key={link.href}>
                  <Link to={link.href} className={LINK_CLASS}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-900 mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-600">
            {footerText || `© ${year} ${branding.app_name}. Todos los derechos reservados.`}
          </p>
          <div className="flex items-center gap-2">
            <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">🔒 SSL</span>
            <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">🇪🇺 RGPD</span>
            <span className="text-[10px] border border-slate-800 text-slate-600 px-2 py-0.5 rounded">99.9% SLA</span>
          </div>
          <div className="flex items-center gap-4">
            {LEGAL_LINKS.map(link => (
              <Link
                key={link.href}
                to={link.href}
                className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
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
