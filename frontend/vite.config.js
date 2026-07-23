import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";

const backendTarget = process.env.VITE_BACKEND_URL || "http://localhost:9980";

const backendPaths = [
  "/api",
  "/api-auth",
  "/api_user_details",
  "/admin",
  "/media",
  "/login",
  "/logout",
  "/get_navigation_tree",
  "/password_reset",
  "/danke",
  "/openapi"
];

export default defineConfig({
  base: "/vue/",
  server: {
    host: true,
    allowedHosts: true,
    proxy: Object.fromEntries(
      backendPaths.map((path) => [
        path,
        {
          target: backendTarget,
          changeOrigin: true
        }
      ])
    )
  },
  build: {
    assetsDir: "vue-assets"
  },
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
});
