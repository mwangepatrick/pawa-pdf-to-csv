import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const repoRootDir = path.resolve(frontendDir, "..");

export default defineConfig(({ mode }) => {
  const runtimeTurnstileSiteKey = process.env.VITE_TURNSTILE_SITE_KEY || process.env.TURNSTILE_SITE_KEY;
  const frontendTurnstileEnv = loadEnv(mode, frontendDir, "TURNSTILE_");
  const frontendPublicTurnstileEnv = loadEnv(mode, frontendDir, "VITE_TURNSTILE_");
  const rootTurnstileEnv = loadEnv(mode, repoRootDir, "TURNSTILE_");
  const rootPublicTurnstileEnv = loadEnv(mode, repoRootDir, "VITE_TURNSTILE_");
  const turnstileSiteKey =
    runtimeTurnstileSiteKey ||
    frontendTurnstileEnv.TURNSTILE_SITE_KEY ||
    frontendPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY ||
    rootTurnstileEnv.TURNSTILE_SITE_KEY ||
    rootPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY ||
    "";

  if (!turnstileSiteKey) {
    throw new Error(
      "TURNSTILE_SITE_KEY is required to build the frontend. Set it in the root .env or pass VITE_TURNSTILE_SITE_KEY or TURNSTILE_SITE_KEY for local-only overrides.",
    );
  }

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_TURNSTILE_SITE_KEY": JSON.stringify(turnstileSiteKey),
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
