/**
 * The guided story, `/`. In part A of C6 this is C3's stub moved into its own module, unchanged, so the view can be
 * split by path; part B builds the nine beats here.
 */
import { AgainstThesis } from "./AgainstThesis";
import { explorerHis } from "./copy";
import type { DataIndex } from "./data";
import { His, Title } from "./parts";

export function Story({ index }: { index: DataIndex }) {
  return (
    <>
      <Title route={{ kind: "story" }} />
      <His text={explorerHis.landingQuestion} />
      <His text={explorerHis.scopeSentence} />
      <AgainstThesis index={index} />
    </>
  );
}
