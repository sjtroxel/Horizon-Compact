import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The policy CloudFront serves (Phase 1.5 IMPLEMENTATION doc section 9), word for word. `npm run preview` serves
// the production build under it, so a request or inline style it forbids shows up here, not on the deploy.
const CONTENT_SECURITY_POLICY = [
  "default-src 'none'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "base-uri 'none'",
  "form-action 'none'",
  "frame-ancestors 'none'",
].join("; ");

const headers = {
  "Content-Security-Policy": CONTENT_SECURITY_POLICY,
  // Removed at Phase 6.5's go-live, with the CloudFront header of the same name.
  "X-Robots-Tag": "noindex",
};

export default defineConfig({
  plugins: [react()],
  build: {
    // Nothing is inlined as a data: URI (the policy allows data: for images only), and no preload polyfill.
    assetsInlineLimit: 0,
    modulePreload: { polyfill: false },
    cssCodeSplit: false,
    sourcemap: false,
  },
  preview: { headers },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    css: false,
  },
});
