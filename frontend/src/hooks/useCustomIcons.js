import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Module-level cache so all components share one fetch
let cachedIcons = null;
let fetchPromise = null;

const fetchIcons = () => {
  if (fetchPromise) return fetchPromise;
  fetchPromise = axios
    .get(`${BACKEND_URL}/api/icons/public`, { withCredentials: true })
    .then((res) => {
      cachedIcons = res.data.icons || {};
      return cachedIcons;
    })
    .catch(() => {
      cachedIcons = {};
      return {};
    });
  return fetchPromise;
};

export const useCustomIcons = () => {
  const [icons, setIcons] = useState(cachedIcons || {});

  useEffect(() => {
    if (cachedIcons !== null) return;
    fetchIcons().then((data) => setIcons(data));
  }, []);

  const getIconUrl = (key) => {
    const url = icons[key];
    if (!url) return null;
    return url.startsWith("/") ? `${BACKEND_URL}${url}` : url;
  };

  return { icons, getIconUrl };
};

// Invalidate cache (called after icons are updated in admin)
export const invalidateIconsCache = () => {
  cachedIcons = null;
  fetchPromise = null;
};
