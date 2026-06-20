import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api -> FastAPI on :8000, so the frontend can use
// relative URLs and we avoid any CORS friction during the demo.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
