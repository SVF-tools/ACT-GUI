import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const servicePort = process.env.ACT_GUI_SERVICE_PORT ?? "18765";

// Development: the browser dev server proxies /api (REST + SSE) to the FastAPI service on loopback.
export default defineConfig({
  root: "visual_bench",
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: Number(process.env.ACT_GUI_WEB_PORT ?? 5173),
    strictPort: true,
    // Regex key: a plain "/api" prefix would also capture the module /api.ts.
    proxy: { "^/api/": { target: `http://127.0.0.1:${servicePort}` } },
  },
  build: { outDir: "../dist/web", emptyOutDir: true },
  test: { include: ["**/*.test.ts"] },
});
