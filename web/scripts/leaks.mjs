// What a public build must not contain (Phase 6 IMPLEMENTATION doc section 6, C3 decision 8): the official run ids and
// sweep ids, and any byte-for-byte copy of an explorer data file. check-dist.mjs runs these on `dist/` and on the
// explorer's output; the Vitest negative control runs the same functions on a folder with an id planted in it.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

/** Every file under `dir`, as absolute paths, sorted. */
export function walk(dir) {
  return readdirSync(dir)
    .sort()
    .flatMap((name) => {
      const path = join(dir, name);
      return statSync(path).isDirectory() ? walk(path) : [path];
    });
}

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));

/**
 * The official ids, read from the committed data in `webRoot` (the web/ folder): every `run_id` in
 * `explorer-memos/**` `.jsonl`, and every sweep id the index, the thinking files and the case results name.
 * The sweep ids come from the index's own `files` block, so a new file is covered without a list kept here.
 */
export function loadOfficialIds(webRoot) {
  const runIds = new Set();
  const memos = join(webRoot, "explorer-memos");
  for (const file of walk(memos).filter((f) => f.endsWith(".jsonl"))) {
    for (const line of readFileSync(file, "utf8").split("\n")) {
      if (line.trim() === "") continue;
      const runId = JSON.parse(line).run_id;
      if (typeof runId !== "string" || runId === "") throw new Error(`${file}: a line has no run_id`);
      runIds.add(runId);
    }
  }

  const data = join(webRoot, "explorer-data");
  const index = readJson(join(data, "index.json"));
  const sweepIds = new Set(index.models.map((m) => m.sweep_id));
  const paths = [
    ...Object.values(index.files.thinking).flatMap((byScenario) => Object.values(byScenario)),
    ...Object.values(index.files.case_results).flatMap((byModel) => Object.values(byModel)),
  ];
  for (const relative of paths) sweepIds.add(readJson(join(data, relative)).sweep_id);
  return { runIds, sweepIds };
}

/** The sha256 of every file under `explorer-data/` and `explorer-memos/`, each mapped to one path it came from. */
export function loadDataHashes(webRoot) {
  const hashes = new Map();
  for (const folder of ["explorer-data", "explorer-memos"]) {
    for (const file of walk(join(webRoot, folder))) hashes.set(sha256(readFileSync(file)), file);
  }
  return hashes;
}

/**
 * Looks in each file for any of the ids. A file is read as latin1, so a binary file is scanned byte for byte and no
 * id is lost to a decoding error.
 * @returns {{runs: Array<{file: string, id: string}>, sweeps: Array<{file: string, id: string}>}}
 */
export function findLeaks(files, { runIds, sweepIds }) {
  const runs = [];
  const sweeps = [];
  for (const file of files) {
    const text = readFileSync(file, "latin1");
    for (const id of runIds) if (text.includes(id)) runs.push({ file, id });
    for (const id of sweepIds) if (text.includes(id)) sweeps.push({ file, id });
  }
  return { runs, sweeps };
}

/** Files whose bytes equal a file of the explorer's data, as `{file, copyOf}`. */
export function findDataCopies(files, hashes) {
  const copies = [];
  for (const file of files) {
    const copyOf = hashes.get(sha256(readFileSync(file)));
    if (copyOf !== undefined) copies.push({ file, copyOf });
  }
  return copies;
}
