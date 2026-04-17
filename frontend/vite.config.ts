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
  const devOverrideSiteKey =
    frontendTurnstileEnv.TURNSTILE_SITE_KEY_OVERRIDE ||
    frontendPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY_OVERRIDE ||
    rootTurnstileEnv.TURNSTILE_SITE_KEY_OVERRIDE ||
    rootPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY_OVERRIDE ||
    process.env.VITE_TURNSTILE_SITE_KEY_OVERRIDE ||
    process.env.TURNSTILE_SITE_KEY_OVERRIDE ||
    "";
  const turnstileSiteKey =
    runtimeTurnstileSiteKey ||
    frontendTurnstileEnv.TURNSTILE_SITE_KEY ||
    frontendPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY ||
    rootTurnstileEnv.TURNSTILE_SITE_KEY ||
    rootPublicTurnstileEnv.VITE_TURNSTILE_SITE_KEY ||
    "";

  const resolvedTurnstileSiteKey = mode === "development" || mode === "test" ? devOverrideSiteKey || turnstileSiteKey : turnstileSiteKey;

  if (!resolvedTurnstileSiteKey) {
    throw new Error(
      "TURNSTILE_SITE_KEY is required to build the frontend. Set it in the root .env or pass TURNSTILE_SITE_KEY_OVERRIDE for local dev/test overrides.",
    );
  }

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_TURNSTILE_SITE_KEY": JSON.stringify(resolvedTurnstileSiteKey),
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
