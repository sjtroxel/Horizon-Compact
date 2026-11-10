import { cpSync, existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
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

const root = fileURLToPath(new URL(".", import.meta.url));
const DATA_SOURCES = [
  // The explorer's data, then the grid memo extract, which lands under data/memos/ (Phase 6 doc section 5.3).
  { from: join(root, "explorer-data"), to: "data" },
  { from: join(root, "explorer-memos"), to: "data/memos" },
] as const;

function hasFiles(dir: string): boolean {
  return existsSync(dir) && readdirSync(dir, { recursive: true }).length > 0;
}

/**
 * Explorer mode only (Phase 6 IMPLEMENTATION doc, C3 decision 4). The data reaches the explorer by `fetch` from its
 * own origin, never by import, so none of it is in the JavaScript. After the bundle is written this copies the two
 * data folders into the output byte for byte, and fails the build if either is missing or empty. The dev server
 * serves the same files at the same paths, and answers any page path with the explorer's HTML.
 */
function explorerData(): Plugin {
  return {
    name: "explorer-data",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const path = decodeURIComponent((request.url ?? "/").split("?")[0] ?? "/");
        if (path.startsWith("/data/")) {
          // Longest destination first, so data/memos/... is the memo folder's and not explorer-data's.
          for (const source of [...DATA_SOURCES].reverse()) {
            const prefix = `/${source.to}/`;
            if (!path.startsWith(prefix)) continue;
            const file = resolve(source.from, path.slice(prefix.length));
            if (
              !file.startsWith(`${source.from}${sep}`) ||
              !existsSync(file) ||
              statSync(file).isDirectory()
            ) {
              continue;
            }
            response.setHeader("Content-Type", "application/json; charset=utf-8");
            response.end(readFileSync(file));
            return;
          }
          response.statusCode = 404;
          response.end("not found");
          return;
        }
        // A page path (no file extension, not a Vite internal): the explorer's single HTML entry.
        if (!/\.[a-z0-9]+$/i.test(path) && !path.startsWith("/@") && !path.startsWith("/node_modules/")) {
          request.url = "/explorer.html";
        }
        next();
      });
    },
    writeBundle(options) {
      const outDir = options.dir;
      if (!outDir) throw new Error("explorer-data: no output directory");
      for (const source of DATA_SOURCES) {
        if (!hasFiles(source.from)) {
          throw new Error(
            `explorer-data: ${source.from} is missing or empty; run the builder (hc site explorer / hc site memos)`,
          );
        }
        cpSync(source.from, join(outDir, source.to), { recursive: true });
      }
    },
  };
}

export default defineConfig(({ mode }) => {
  const explorer = mode === "explorer";
  return {
    plugins: [react(), preloadFonts(), ...(explorer ? [explorerData()] : [])],
    build: {
      // Nothing is inlined as a data: URI (the policy allows data: for images only), and no preload polyfill.
      assetsInlineLimit: 0,
      modulePreload: { polyfill: false },
      cssCodeSplit: false,
      sourcemap: false,
      // Explorer mode is its own entry and its own folder, which Deploy never syncs (C3 decision 1). Placeholder
      // mode, with no --mode, keeps Vite's defaults: index.html in, dist/ out.
      ...(explorer
        ? {
            outDir: "dist-explorer",
            rollupOptions: { input: join(root, "explorer.html") },
          }
        : {}),
    },
    preview: { headers },
    test: {
      environment: "jsdom",
      include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
      css: false,
    },
  };
});
