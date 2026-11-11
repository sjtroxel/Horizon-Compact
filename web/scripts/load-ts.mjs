// Loads a TypeScript module of the explorer from a plain Node script, through Vite's module runner (Vite 8's
// `runnerImport`, marked experimental in its own types and used here for build scripts only). Node 22.13 does not run
// .ts files, and the card text must come from the very modules the views use (copy.ts, format.ts, models.ts, ...), not a
// copy. The server `runnerImport` starts is closed when it returns.
import { join } from "node:path";
import { runnerImport } from "vite";

/** The module at `relative` (from web/), evaluated with Vite's transforms, with no vite.config.ts and no plugins. */
export async function loadTs(webRoot, relative) {
  const { module } = await runnerImport(join(webRoot, relative), {
    configFile: false,
    root: webRoot,
    logLevel: "error",
  });
  return module;
}
