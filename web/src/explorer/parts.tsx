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

/** The view's title: his words for the kind of page, and the scenario's id or the case's label after it. */
export function Title({ route }: { route: PageRoute }) {
  const title = pageMeta(route, explorerHis.pages).title;
  return (
    <h1
      tabIndex={-1}
      className={isPlaceholder(explorerHis.pages[route.kind].title) ? "placeholder" : undefined}
    >
      {title}
    </h1>
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
