import type { ReactNode } from "react";
import { isPlaceholder, explorerHis, explorerLabels } from "./copy";
import { PROTOCOL_READINGS } from "./protocol";
import type { ReadingKey } from "./protocol";
import { pageMeta } from "./page-meta.mjs";
import type { PageRoute } from "./page-meta.mjs";

/** A sentence of his; while it is still a marked placeholder it shows in the secondary ink. */
export function His({ text, className }: { text: string; className?: string }) {
  const classes = [className, isPlaceholder(text) ? "placeholder" : undefined].filter(Boolean).join(" ");
  return <p className={classes || undefined}>{text}</p>;
}

/** A word or line of his inside a sentence or a note line, not a paragraph of its own; a placeholder shows in the secondary ink. */
export function HisInline({ text }: { text: string }) {
  return <span className={isPlaceholder(text) ? "placeholder" : undefined}>{text}</span>;
}

/** A heading of his, by level; a placeholder shows in the secondary ink. */
export function HisHeading({ text, level, id }: { text: string; level: 2 | 3; id?: string }) {
  const className = isPlaceholder(text) ? "placeholder" : undefined;
  return level === 2 ? (
    <h2 id={id} className={className}>
      {text}
    </h2>
  ) : (
    <h3 id={id} className={className}>
      {text}
    </h3>
  );
}

/**
 * The view's title block, on the light band under the site header (Phase 6 IMPLEMENTATION doc section 30, study item 6):
 * his words for the kind of page, and the scenario's id or the case's label after it, then whatever line or menu the page
 * puts under its title (`children`). The band spans the page; its contents keep the page's column.
 */
export function Title({ route, id, children }: { route: PageRoute; id?: string; children?: ReactNode }) {
  const title = pageMeta(route, explorerHis.pages).title;
  return (
    <div className="title-band">
      <div className="title-inner">
        <h1
          id={id}
          tabIndex={-1}
          className={isPlaceholder(explorerHis.pages[route.kind].title) ? "placeholder" : undefined}
        >
          {title}
        </h1>
        {children}
      </div>
    </div>
  );
}

/**
 * The protocol's pre-registered reading of a pattern, quoted as written, or, where the protocol wrote none for the
 * pair, a label saying so. Nothing is written in the protocol's place.
 */
export function ProtocolReading({ readingKey }: { readingKey: ReadingKey | null }) {
  if (readingKey === null) return <p className="fine muted protocol-none">{explorerLabels.noReading}</p>;
  const reading = PROTOCOL_READINGS[readingKey];
  return (
    <blockquote className="reading" data-reading={readingKey}>
      <p className="fine muted">
        {explorerLabels.protocolReadingLabel} <span className="pattern">{reading.pattern}</span>
      </p>
      <p>{reading.reading}</p>
    </blockquote>
  );
}
