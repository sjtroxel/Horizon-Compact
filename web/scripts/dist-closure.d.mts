export interface ManifestChunk {
  file: string;
  src?: string;
  isEntry?: boolean;
  isDynamicEntry?: boolean;
  imports?: string[];
  dynamicImports?: string[];
  css?: string[];
}

export type Manifest = Record<string, ManifestChunk>;

export function staticClosure(manifest: Manifest, startKeys: readonly string[]): Set<string>;
export function pathFiles(manifest: Manifest, entryKey: string, viewKey: string): string[];
export function reachedFromEntry(manifest: Manifest, entryKey: string, moduleKey: string): boolean;
export function entryKeyOf(manifest: Manifest): string;
