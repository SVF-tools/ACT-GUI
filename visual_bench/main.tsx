import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app";
import { applyTheme, storedTheme } from "./workspace/theme";
import "./styles.css";

applyTheme(storedTheme()); // before first render, so a saved light theme does not flash dark

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
