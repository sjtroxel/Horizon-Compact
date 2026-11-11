import { Component, useEffect } from "react";
import type { ReactNode } from "react";

interface BoundaryProps {
  /** The failure's place: a change of this value (a navigation to another path) clears a failure. */
  resetKey: string;
  /** What to show in place of the view when it throws, which is what a view chunk that will not load does. */
  fallback: ReactNode;
  children: ReactNode;
}

interface BoundaryState {
  failed: boolean;
  key: string;
}

/**
 * An error boundary around the routed view (Phase 6 IMPLEMENTATION doc section 28). A view is a lazy chunk; if the
 * chunk fails to load, React throws at the view, and without this the page would go blank. It shows the fallback
 * instead, and a navigation to another path clears it, so one view that will not load does not take the others down.
 */
export class ViewBoundary extends Component<BoundaryProps, BoundaryState> {
  override state: BoundaryState = { failed: false, key: this.props.resetKey };

  static getDerivedStateFromError(): Partial<BoundaryState> {
    return { failed: true };
  }

  static getDerivedStateFromProps(props: BoundaryProps, state: BoundaryState): Partial<BoundaryState> | null {
    return props.resetKey !== state.key ? { failed: false, key: props.resetKey } : null;
  }

  override render(): ReactNode {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

/**
 * Rendered inside the `Suspense` boundary, after the routed view: its effect runs only once the view has mounted
 * (React commits nothing in a boundary that is still waiting for a lazy chunk), and again when `token` changes, which
 * is once per navigation. The shell uses it to move focus and scroll to the hash's target, which does not exist until
 * the view has.
 */
export function Arrived({ token, onArrive }: { token: number; onArrive: (token: number) => void }) {
  useEffect(() => {
    onArrive(token);
  }, [token, onArrive]);
  return null;
}
