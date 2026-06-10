import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PostCSS (Tailwind + autoprefixer) is configured in postcss.config.js, which
// Vite picks up automatically. See DESIGN.md for the design-token system.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
