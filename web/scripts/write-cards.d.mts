import type { PageRoute } from "../src/explorer/page-meta.mjs";

export function writeCards(
  webRoot: string,
  outDir?: string,
): Promise<Array<{ route: PageRoute; slug: string; bytes: number }>>;
