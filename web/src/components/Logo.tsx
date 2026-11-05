// The header mark, "1e" in the Phase 1.5 previews: the sun cut by the horizon, a short line below, three rays.
// Colors come from CSS classes (--sun and --ink), never from presentation attributes holding var().
// The page draws one logo, so the clip path's id is a constant and unique in the document.
const CLIP_ID = "logo-above-horizon";

export function Logo({ size = 56 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false" className="logo">
      <clipPath id={CLIP_ID}>
        <rect x="0" y="0" width="32" height="21" />
        <rect x="0" y="24.25" width="32" height="2.25" />
      </clipPath>
      <circle className="logo-sun" cx="16" cy="21" r="7.25" clipPath={`url(#${CLIP_ID})`} />
      <g className="logo-ray" strokeWidth="2.4" strokeLinecap="round">
        <line x1="24.19" y1="15.26" x2="27.06" y2="13.26" />
        <line x1="16" y1="11" x2="16" y2="7.5" />
        <line x1="7.81" y1="15.26" x2="4.94" y2="13.26" />
      </g>
      <rect className="logo-bar" x="1.5" y="21" width="29" height="2.5" rx="1.25" />
      <rect className="logo-bar" x="8" y="27" width="16" height="2.5" rx="1.25" />
    </svg>
  );
}
