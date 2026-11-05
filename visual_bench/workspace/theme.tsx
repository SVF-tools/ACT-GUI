// UI theme preference: dark (default) or light, persisted per browser and applied as <html data-theme>.
import { useEffect, useState } from "react";

export type Theme = "dark" | "light";
const KEY = "act-gui.theme";

export function storedTheme(): Theme {
  try {
    return localStorage.getItem(KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark"; // storage blocked (e.g. privacy mode): fall back to the default theme
  }
}

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(storedTheme);

  useEffect(() => {
    applyTheme(theme);
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      // Preference just won't persist; the theme still applies for this session.
    }
  }, [theme]);

  const next: Theme = theme === "dark" ? "light" : "dark";
  return (
    <button type="button" className="themetoggle" onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`} title={`Switch to ${next} theme`}>
      {theme === "dark" ? "☾ Dark" : "☀ Light"}
    </button>
  );
}
