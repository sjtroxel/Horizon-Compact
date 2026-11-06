import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

// The two fonts the first screen needs: the name's face and the prose face. Vite does not preload fonts that CSS
// refers to, so without this a cold load paints the fallback faces and reflows when the real ones arrive.
const PRELOADED_FONTS = [
  /(^|\/)big-shoulders-display-latin-800-normal-[^/]*\.woff2$/,
  /(^|\/)newsreader-latin-400-normal-[^/]*\.woff2$/,
];

/** At build time, finds the two emitted font files and adds a preload link for each. `crossorigin` is required even
 * on the same origin: fonts are fetched in CORS mode, and without it the browser fetches each one twice. */
function preloadFonts(): Plugin {
  let base = "/";
  return {
    name: "preload-first-screen-fonts",
    configResolved(config) {
      base = config.base;
    },
    transformIndexHtml: {
      order: "post",
      handler(_html, context) {
        if (!context.bundle) return undefined; // the dev server has no built files
        return PRELOADED_FONTS.map((pattern) => {
          const matches = Object.keys(context.bundle ?? {}).filter((name) => pattern.test(name));
          if (matches.length !== 1) {
            throw new Error(
              `preload-first-screen-fonts: expected one file for ${pattern}, found ${matches.length}`,
            );
          }
          return {
            tag: "link",
            attrs: {
              rel: "preload",
              href: `${base}${matches[0]}`,
              as: "font",
              type: "font/woff2",
              crossorigin: true,
            },
            injectTo: "head" as const,
          };
        });
      },
    },
  };
}

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
  plugins: [react(), preloadFonts()],
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
