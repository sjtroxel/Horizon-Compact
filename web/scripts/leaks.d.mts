export interface OfficialIds {
  runIds: Set<string>;
  sweepIds: Set<string>;
}

export interface Leaks {
  runs: Array<{ file: string; id: string }>;
  sweeps: Array<{ file: string; id: string }>;
}

export function walk(dir: string): string[];
export function loadOfficialIds(webRoot: string): OfficialIds;
export function loadDataHashes(webRoot: string): Map<string, string>;
export function findLeaks(files: readonly string[], ids: OfficialIds): Leaks;
export function findDataCopies(
  files: readonly string[],
  hashes: Map<string, string>,
): Array<{ file: string; copyOf: string }>;
