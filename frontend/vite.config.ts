import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.SKN27_BACKEND_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/v1/ws": {
        target: backendTarget,
        changeOrigin: true,
        ws: true,
      },
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/healthz": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});

