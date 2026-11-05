import { StrictMode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./shared/queryClient";
import { createRoot } from "react-dom/client";
import { App } from "./app";
import { applyTheme, storedTheme } from "./workspace/theme";
import "./styles.css";

applyTheme(storedTheme()); // before first render, so a saved light theme does not flash dark

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
