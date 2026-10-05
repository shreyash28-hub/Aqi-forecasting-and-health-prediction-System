"use client";

import { useCallback, useSyncExternalStore } from "react";

type Theme = "light" | "dark";
const STORAGE_KEY = "airware-theme";
const EVENT = "airware-theme-change";

/** Inline script for <head>: applies the saved or system theme before first paint (no flash). */
export const themeInitScript = `(function(){try{var t=localStorage.getItem('${STORAGE_KEY}');if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}document.documentElement.classList.toggle('dark',t==='dark');document.documentElement.style.colorScheme=t}catch(e){}})()`;

// The <html> class is the single source of truth; components subscribe to it.
function subscribe(onChange: () => void) {
  window.addEventListener(EVENT, onChange);
  return () => window.removeEventListener(EVENT, onChange);
}
const getSnapshot = (): Theme => (document.documentElement.classList.contains("dark") ? "dark" : "light");
const getServerSnapshot = (): Theme => "light";

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const toggle = useCallback(() => {
    const next: Theme = getSnapshot() === "dark" ? "light" : "dark";
    document.documentElement.classList.toggle("dark", next === "dark");
    document.documentElement.style.colorScheme = next;
    try { localStorage.setItem(STORAGE_KEY, next); } catch {}
    window.dispatchEvent(new Event(EVENT));
  }, []);
  return { theme, toggle };
}

/** Kept as a wrapper so the provider tree stays stable if theme state grows later. */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

/** Resolved colours for charts (ECharts can't read CSS variables). */
export function useChartColors() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  return {
    text: dark ? "#e9ebef" : "#0e1116",
    muted: dark ? "#a0a7b4" : "#5a6270",
    faint: dark ? "#737b89" : "#8a919e",
    grid: dark ? "#242932" : "#e3e6eb",
    axis: dark ? "#323843" : "#cfd4dc",
    surface: dark ? "#1a1e25" : "#ffffff",
    brand: dark ? "#3fb5b8" : "#0b6e74",
    dark,
  };
}
