import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const repoRootDir = path.resolve(frontendDir, "..");

export default defineConfig(({ mode }) => {
  const frontendEnv = loadEnv(mode, frontendDir, "");
  const rootEnv = loadEnv(mode, repoRootDir, "");
  const turnstileSiteKey =
    frontendEnv.VITE_TURNSTILE_SITE_KEY ||
    frontendEnv.TURNSTILE_SITE_KEY ||
    rootEnv.VITE_TURNSTILE_SITE_KEY ||
    rootEnv.TURNSTILE_SITE_KEY ||
    "";

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_TURNSTILE_SITE_KEY": JSON.stringify(turnstileSiteKey),
      "import.meta.env.TURNSTILE_SITE_KEY": JSON.stringify(turnstileSiteKey),
    },
    server: {
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
