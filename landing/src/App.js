import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import posthog from "posthog-js";
import { AppProvider, useApp } from "./context/AppContext";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Features from "./pages/Features";
import Pricing from "./pages/Pricing";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import Blog from "./pages/Blog";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

function PostHogPageviewTracker() {
  const { pathname } = useLocation();
  useEffect(() => {
    posthog.capture("$pageview");
  }, [pathname]);
  return null;
}

// Observador global de scroll-reveal: añade .visible a los elementos
// con clases .reveal-up/.reveal-left/.reveal-right/.reveal-scale
// cuando entran en el viewport. Funciona con contenido cargado dinámicamente.
function ScrollReveal() {
  const { pathname } = useLocation();

  useEffect(() => {
    const SELECTOR = ".reveal-up, .reveal-left, .reveal-right, .reveal-scale";

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -60px 0px" }
    );

    const observeAll = () => {
      document.querySelectorAll(SELECTOR).forEach((el) => {
        if (!el.classList.contains("visible")) observer.observe(el);
      });
    };

    // Observar elementos iniciales y los que se rendericen después
    observeAll();
    const mutation = new MutationObserver(observeAll);
    mutation.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutation.disconnect();
    };
  }, [pathname]); // Re-ejecutar al cambiar de página

  return null;
}

function AppLayout() {
  const { theme } = useApp();
  const dark = theme === "dark";

  // El título y meta tags son gestionados por el hook useSEO en cada página.

  return (
    <div className={dark ? "dark bg-slate-950 text-white" : "bg-white text-slate-900"}>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/caracteristicas" element={<Features />} />
          <Route path="/precios" element={<Pricing />} />
          <Route path="/nosotros" element={<About />} />
          <Route path="/contacto" element={<Contact />} />
          <Route path="/privacidad" element={<Privacy />} />
          <Route path="/terminos" element={<Terms />} />
          <Route path="/blog" element={<Blog />} />
          {/* Catch-all → home */}
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <ScrollToTop />
        <PostHogPageviewTracker />
        <ScrollReveal />
        <AppLayout />
      </BrowserRouter>
    </AppProvider>
  );
}
