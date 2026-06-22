import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// base cấu hình được cho GitHub Pages (SPEC 13 §3): đặt VITE_BASE=/<repo>/ khi build Pages.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
