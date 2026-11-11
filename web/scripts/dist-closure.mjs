// The JavaScript a path loads, from Vite's manifest (Phase 6 IMPLEMENTATION doc section 17, C6 part A). Pure functions,
// no file reads, so a Vitest test can drive them over a small fixture manifest; check-dist.mjs reads the real manifest
// (dist-explorer/.vite/manifest.json) and calls them.
//
// A manifest is an object from a key (a source path, or for a shared chunk a name starting with "_") to a chunk:
// `{ file, src?, isEntry?, isDynamicEntry?, imports?: string[], dynamicImports?: string[], css?: string[] }`. `imports`
// and `dynamicImports` name other keys. The browser loads a chunk's static `imports` with it, transitively, and a
// dynamic import only when the code reaches it, so only static imports are followed here.

/**
 * Every manifest key reachable from `startKeys` by static imports, including the start keys themselves. A key the
 * manifest does not have is an error (a manifest that names a chunk it does not describe is broken), and a cycle is
 * walked once.
 * @param {Record<string, {file: string, imports?: string[]}>} manifest
 * @param {readonly string[]} startKeys
 * @returns {Set<string>}
 */
export function staticClosure(manifest, startKeys) {
  const seen = new Set();
  const queue = [...startKeys];
  while (queue.length > 0) {
    const key = queue.pop();
    if (seen.has(key)) continue;
    const chunk = manifest[key];
    if (chunk === undefined) throw new Error(`the manifest has no entry for "${key}"`);
    seen.add(key);
    for (const next of chunk.imports ?? []) queue.push(next);
  }
  return seen;
}

/**
 * The JavaScript files one path loads: the entry chunk and its static imports, plus the path's view chunk and its
 * static imports. Each distinct file once, sorted. Never a dynamic import: those are the other paths' views.
 * @param {Record<string, {file: string, imports?: string[]}>} manifest
 * @param {string} entryKey the manifest key of the explorer's entry
 * @param {string} viewKey the manifest key of the path's view module
 * @returns {string[]}
 */
export function pathFiles(manifest, entryKey, viewKey) {
  const keys = staticClosure(manifest, [entryKey, viewKey]);
  return [...new Set([...keys].map((key) => manifest[key].file))]
    .filter((file) => file.endsWith(".js"))
    .sort();
}

/**
 * Whether the entry reaches a module by static imports, which would mean the module was not split out (it is in
 * the first load of every path).
 * @param {Record<string, {file: string, imports?: string[]}>} manifest
 * @param {string} entryKey
 * @param {string} moduleKey
 */
export function reachedFromEntry(manifest, entryKey, moduleKey) {
  return staticClosure(manifest, [entryKey]).has(moduleKey);
}

/** The manifest's one entry: the key of the chunk marked `isEntry`. More or fewer than one is an error. */
export function entryKeyOf(manifest) {
  const keys = Object.keys(manifest).filter((key) => manifest[key].isEntry === true);
  if (keys.length !== 1) throw new Error(`the manifest has ${keys.length} entries, expected exactly one`);
  return keys[0];
}
