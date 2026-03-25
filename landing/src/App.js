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

function AppLayout() {
  const { branding, theme } = useApp();
  const dark = theme === "dark";

  // Update page title from branding
  useEffect(() => {
    document.title = branding.page_title || `${branding.app_name} — Sincronización de Inventario B2B`;
  }, [branding.page_title, branding.app_name]);

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
        <AppLayout />
      </BrowserRouter>
    </AppProvider>
  );
}
