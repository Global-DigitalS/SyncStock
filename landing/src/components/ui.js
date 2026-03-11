import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs) => twMerge(clsx(inputs));

export const Button = ({ children, className = "", variant = "primary", size = "md", as: Tag = "button", ...props }) => {
  const base = "inline-flex items-center justify-center font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none rounded-lg";
  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm hover:shadow-md",
    secondary: "bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 shadow-sm",
    ghost: "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
    dark: "bg-slate-900 text-white hover:bg-slate-800 shadow-sm",
    white: "bg-white text-indigo-600 hover:bg-slate-50 shadow-lg",
    outline: "border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50",
    danger: "bg-red-600 text-white hover:bg-red-700 shadow-sm",
  };
  const sizes = {
    sm: "text-sm px-3 py-1.5 gap-1.5",
    md: "text-sm px-4 py-2 gap-2",
    lg: "text-base px-6 py-3 gap-2",
    xl: "text-lg px-8 py-4 gap-2.5",
  };
  return (
    <Tag className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </Tag>
  );
};

export const Badge = ({ children, className = "", variant = "default" }) => {
  const variants = {
    default: "bg-indigo-100 text-indigo-700",
    success: "bg-emerald-100 text-emerald-700",
    warning: "bg-amber-100 text-amber-700",
    danger: "bg-red-100 text-red-700",
    slate: "bg-slate-100 text-slate-700",
    dark: "bg-slate-800 text-slate-200",
  };
  return (
    <span className={cn("inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold", variants[variant], className)}>
      {children}
    </span>
  );
};

export const Card = ({ children, className = "", hover = false, ...props }) => (
  <div className={cn("bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm", hover && "card-hover", className)} {...props}>
    {children}
  </div>
);

export const SectionLabel = ({ children }) => (
  <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-full px-4 py-1.5 text-sm font-semibold mb-4">
    {children}
  </div>
);

export const SectionTitle = ({ children, className = "" }) => (
  <h2 className={cn("text-3xl md:text-4xl font-bold text-slate-900 dark:text-white leading-tight", className)}>
    {children}
  </h2>
);

export const SectionSubtitle = ({ children, className = "" }) => (
  <p className={cn("text-lg text-slate-500 dark:text-slate-400 leading-relaxed", className)}>
    {children}
  </p>
);
