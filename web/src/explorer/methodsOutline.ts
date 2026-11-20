// The methods page's words, as methods.json holds them (Phase 6.5 step 5): the types, and the thirteen sections' ids and
// anchors. The words themselves are not in the page's code: the page fetches methods.json as a file (see data.ts,
// `loadMethodsWords`), so its prose does not count against a path's JavaScript budget. The ids and anchors are here,
// so the contents list draws at once; a test holds them equal to methods.json's, and the page refuses words whose
// sections differ.

/**
 * Where a figure in a block's text comes from. Either a file of the repository and the words in it that hold the
 * figure (`match`, or the figure's own text when it is absent), or a count made from the results files (`count`),
 * which the test recomputes from the explorer's data.
 */
export interface Figure {
  text: string;
  source?: string;
  match?: string;
  count?: CountSpec;
}

/** A count of runs or cells, over one sweep of one model, one scenario or all of them. */
export interface CountSpec {
  sweep: "grid" | "thinking";
  model: string;
  scenario?: string;
  measure:
    | "attempted"
    | "unsuccessful"
    | "unsuccessful_percent"
    | "cells_over_limit"
    | "cells_with_unsuccessful"
    | "runs_per_cell";
}

interface BlockBase {
  /** The disclosure ledger's ids (doc section 1) this block states; empty for a block the ledger does not name. */
  ledger: string[];
  /** Files of the repository the block rests on, linked at the end of its section. */
  sources?: string[];
  figures?: Figure[];
}

/** A block of the page's words. */
export type Block =
  | (BlockBase & { kind: "p"; lead?: string; text: string })
  /** Words quoted exactly: each text is found, word for word, in `source` (the test checks it). */
  | (BlockBase & { kind: "quote"; lead?: string; source: string; texts: string[] })
  /** A list; an item may link to the section that explains it. */
  | (BlockBase & { kind: "list"; lead?: string; items: Array<{ text: string; anchor?: string }> })
  /** His scope sentence (his.json), shown first. */
  | (BlockBase & { kind: "scope" })
  /** The five goals, from index.json's objectives. */
  | (BlockBase & { kind: "objectives" })
  /** The four scenarios in brief (his.json) and each one's main result (index.json). */
  | (BlockBase & { kind: "scenarios" })
  /**
   * The video (Phase 6.5 step 9, doc section 6): its file, poster and captions, each a file name under media/, and
   * its words as spoken, one caption cue to a line (a test holds them equal to the captions file's cues). The words are
   * the video's, checked against the site when it was made (docs/phases/evidence/phase-6.5/video/), not the page's own
   * figures, so the figure trace does not read them.
   */
  | (BlockBase & {
      kind: "video";
      title: string;
      file: string;
      poster: string;
      captions: string;
      spoken: string[];
      onScreen: string;
    })
  /** A part a later step writes: the placeholder shows, and `note` says which step (it is never shown). */
  | (BlockBase & { kind: "pending"; note: string });

/** One section of the outline: the file's shape, which the tests also read. */
export interface OutlineSection {
  id: string;
  anchor: string;
  /** The disclosure ledger's line ids (doc section 1) this section carries. */
  ledger: string[];
  /** What else the outline's column names (Delivers and definition-of-done rows) when it gives no ledger line. */
  also: string[];
  /** The section's blocks of words. A section with none shows the body placeholder. */
  blocks: Block[];
}

/** The file's shape. */
export interface MethodsWordsFile {
  sections: OutlineSection[];
}

/** The thirteen sections, in order: each one's id and its anchor on the page. */
export const SECTIONS: ReadonlyArray<{ id: string; anchor: string }> = [
  { id: "M0", anchor: "opening" },
  { id: "M1", anchor: "objectives" },
  { id: "M2", anchor: "company-and-scenarios" },
  { id: "M3", anchor: "models-dates-and-runs" },
  { id: "M4", anchor: "pre-registration" },
  { id: "M5", anchor: "statistics" },
  { id: "M6", anchor: "real-cases" },
  { id: "M7", anchor: "checking-it-yourself" },
  { id: "M8", anchor: "cost" },
  { id: "M9", anchor: "known-limits" },
  { id: "M10", anchor: "words" },
  { id: "M11", anchor: "video" },
  { id: "M12", anchor: "changes" },
];
