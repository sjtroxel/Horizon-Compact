import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { labels } from "../copy";

export interface ControlProps {
  /** "all", or an objective id. */
  chosen: string;
  onChoose: (id: string) => void;
  objectiveIds: string[];
}

/**
 * The priority control: one button per panel, and an indicator that slides and resizes to the chosen one.
 * Selection is shown by weight and by aria-pressed as well as by the bar, never by color alone.
 */
export function Control({ chosen, onChoose, objectiveIds }: ControlProps) {
  const wrap = useRef<HTMLDivElement>(null);
  const buttons = useRef(new Map<string, HTMLButtonElement>());
  const [bar, setBar] = useState({ x: 0, y: 0, width: 0 });
  // The bar moves only once the page has settled: it is placed, not animated, on load, on a resize and when the
  // fonts arrive.
  const [animate, setAnimate] = useState(false);

  const place = useCallback(
    (instant: boolean) => {
      const button = buttons.current.get(chosen);
      const container = wrap.current;
      if (!button || !container) return;
      const c = container.getBoundingClientRect();
      const b = button.getBoundingClientRect();
      setBar({ x: b.left - c.left, y: b.bottom - c.bottom, width: b.width });
      if (instant) {
        setAnimate(false);
        requestAnimationFrame(() => requestAnimationFrame(() => setAnimate(true)));
      }
    },
    [chosen],
  );

  const first = useRef(true);
  useLayoutEffect(() => {
    place(first.current);
    first.current = false;
  }, [place]);

  useEffect(() => {
    const again = () => place(true);
    // The control's own size changes when the window is resized and when its buttons wrap to another row.
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(again);
    if (wrap.current) observer?.observe(wrap.current);
    const fonts = typeof document !== "undefined" ? document.fonts : undefined;
    void fonts?.ready.then(again);
    return () => observer?.disconnect();
  }, [place]);

  const entries = [{ id: "all", text: labels.allFive }].concat(
    objectiveIds.map((id) => ({ id, text: labels.priorities[id] ?? id })),
  );

  return (
    <div ref={wrap} className="control" role="group" aria-label={labels.priorityControl}>
      {entries.map(({ id, text }) => (
        <button
          key={id}
          type="button"
          ref={(el) => {
            if (el) buttons.current.set(id, el);
            else buttons.current.delete(id);
          }}
          aria-pressed={chosen === id}
          data-label={text}
          onClick={() => onChoose(id)}
        >
          {text}
        </button>
      ))}
      <span
        className={animate ? "bar animate" : "bar"}
        aria-hidden="true"
        style={{ width: bar.width, transform: `translate(${bar.x}px, ${bar.y}px)` }}
      />
    </div>
  );
}
