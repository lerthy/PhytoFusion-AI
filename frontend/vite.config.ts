/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // the pathway example lives in ../data so the backend and the app share one file
  server: { fs: { allow: [".."] } },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
