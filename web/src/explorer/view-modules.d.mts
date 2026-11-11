import type { PageRoute } from "./page-meta.mjs";

/** Route kind to the view's source path, relative to the web/ folder (how Vite's manifest names a module). */
export const VIEW_MODULES: Readonly<Record<PageRoute["kind"], string>>;
