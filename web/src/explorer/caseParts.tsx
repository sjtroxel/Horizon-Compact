/**
 * Two small pieces of a real case's card that the cases page and the guided story both show, moved out of Cases.tsx in
 * C6 part B so the story's chunk does not pull in the cases view. Neither adds a word: the exploratory label is the
 * file's own text, and the description is the file's own text or its status.
 */
import { explorerLabels as L } from "./copy";
import type { CaseEntry } from "./data";

/** The exploratory label, verbatim, in the one place every case surface puts it first. */
export function ExploratoryLabel({ text }: { text: string }) {
  return (
    <p className="exploratory-label" data-exploratory-label="">
      {text}
    </p>
  );
}

/** The coarse description's text when it is published; otherwise its status (withheld). Nothing else about the case. */
export function Description({ entry }: { entry: CaseEntry }) {
  const { description } = entry;
  return description.status === "published" && description.text !== undefined ? (
    <p className="case-description">{description.text}</p>
  ) : (
    <p className="case-description">{L.caseDescriptionStatus(description.status)}</p>
  );
}
