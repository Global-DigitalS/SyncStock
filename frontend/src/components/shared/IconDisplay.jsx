import { useCustomIcons } from "../../hooks/useCustomIcons";

/**
 * Displays a custom icon if available, otherwise renders the fallback Lucide icon.
 *
 * Props:
 *   iconKey      - string key like "supplier_url", "store_woocommerce", etc.
 *   FallbackIcon - Lucide React component to render when no custom icon exists
 *   iconClass    - className applied to the Lucide icon (e.g. "w-6 h-6 text-blue-600")
 *   imgClass     - className applied to the <img> tag (default: "w-8 h-8 object-contain")
 *   alt          - alt text for the image
 */
const IconDisplay = ({
  iconKey,
  FallbackIcon,
  iconClass = "w-6 h-6",
  imgClass = "w-8 h-8 object-contain",
  alt = "",
}) => {
  const { getIconUrl } = useCustomIcons();
  const url = getIconUrl(iconKey);

  if (url) {
    return <img src={url} alt={alt} className={imgClass} />;
  }

  if (FallbackIcon) {
    return <FallbackIcon className={iconClass} />;
  }

  return null;
};

export default IconDisplay;
