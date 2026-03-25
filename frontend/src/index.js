import React from "react";
import ReactDOM from "react-dom/client";
import posthog from "posthog-js";
import "@/index.css";
import App from "@/App";

// Inicializar PostHog
const POSTHOG_KEY = process.env.REACT_APP_POSTHOG_KEY || "phc_PbRgdAqlTahRk8YrbLh0bW902nIIxKNGNn96wvr6dc0";
posthog.init(POSTHOG_KEY, {
  api_host: "https://eu.i.posthog.com",
  person_profiles: "identified_only",
  capture_pageview: false, // Se captura manualmente con el router (HashRouter)
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
