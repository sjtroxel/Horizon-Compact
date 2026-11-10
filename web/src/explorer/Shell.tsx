import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { Logo } from "../components/Logo";
import { explorerHis, explorerLabels } from "./copy";
import { defaultData } from "./data";
import type { CasesIndex, DataApi, DataIndex } from "./data";
import { Footer } from "./Footer";
import { ModelSwitch } from "./ModelSwitch";
import { pageMeta } from "./page-meta.mjs";
import { modelFromSearch, parseRoute, pathOf, searchWithModel, withModel } from "./route";
import type { Route } from "./route";
import { View } from "./views";

interface Where {
  pathname: string;
  search: string;
}

function readLocation(): Where {
  return { pathname: window.location.pathname, search: window.location.search };
}

/** The anchor a click landed on, if the browser should leave it to us: a plain primary-button click on a link to
 * this site, not opening a new tab or window, not a download, not a jump within the same page. */
function interceptedAnchor(event: MouseEvent<HTMLElement>): HTMLAnchorElement | null {
  if (event.defaultPrevented || event.button !== 0) return null;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return null;
  const target = event.target;
  if (!(target instanceof Element)) return null;
  const anchor = target.closest("a");
  if (!anchor || !anchor.hasAttribute("href") || anchor.hasAttribute("download")) return null;
  if (anchor.target !== "" && anchor.target !== "_self") return null;
  if (anchor.origin !== window.location.origin) return null;
  const samePage = anchor.pathname === window.location.pathname && anchor.search === window.location.search;
  if (samePage && anchor.hash !== "") return null; // an in-page jump is the browser's
  return anchor;
}

function titleOf(route: Route): string {
  return route.kind === "not_found" ? explorerLabels.notFoundTitle : pageMeta(route, explorerHis.pages).title;
}

interface Catalog {
  index: DataIndex;
  casesIndex: CasesIndex;
}

/**
 * The explorer's frame: the header and navigation, the one model switch, the routed view and the footer. Routing is
 * plain links and the History API: a click on a link to this site is turned into `pushState` and a re-render, and
 * every link is still a real `<a href>`, so a reload, a new tab or a crawler gets the same page.
 */
export function Shell({ data = defaultData }: { data?: DataApi }) {
  const [where, setWhere] = useState<Where>(readLocation);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [failed, setFailed] = useState(false);
  const [navigations, setNavigations] = useState(0);
  const main = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let live = true;
    Promise.all([data.loadIndex(), data.loadCasesIndex()]).then(
      ([index, casesIndex]) => {
        if (live) setCatalog({ index, casesIndex });
      },
      () => {
        if (live) setFailed(true);
      },
    );
    return () => {
      live = false;
    };
  }, [data]);

  // Back and forward.
  useEffect(() => {
    const onPopState = () => {
      setWhere(readLocation());
      setNavigations((n) => n + 1);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const known = useMemo(
    () =>
      catalog && {
        scenarioIds: catalog.index.scenarios.map((s) => s.scenario_id),
        caseLabels: catalog.casesIndex.cases.map((c) => c.label),
      },
    [catalog],
  );
  const route: Route | null = known ? parseRoute(where.pathname, known) : null;
  const model = catalog
    ? modelFromSearch(
        where.search,
        catalog.index.models.map((m) => m.model_key),
      )
    : modelFromSearch(where.search, []);

  const title = route ? titleOf(route) : null;
  useEffect(() => {
    if (title !== null) document.title = title;
  }, [title]);

  // After a navigation the new view's heading takes focus, so a keyboard or screen-reader user lands on it.
  useEffect(() => {
    if (navigations === 0 || route === null) return;
    window.scrollTo(0, 0);
    main.current?.querySelector<HTMLElement>("h1")?.focus({ preventScroll: true });
    // Runs once per navigation, not on every render, so `route` is read but not a dependency.
  }, [navigations]);

  const onClick = useCallback((event: MouseEvent<HTMLElement>) => {
    const anchor = interceptedAnchor(event);
    if (!anchor) return;
    event.preventDefault();
    window.history.pushState(null, "", `${anchor.pathname}${anchor.search}${anchor.hash}`);
    setWhere(readLocation());
    setNavigations((n) => n + 1);
  }, []);

  // The model is kept in the query string, so a link carries it. Choosing one replaces the history entry: going
  // back should leave the page, not undo a toggle.
  const chooseModel = useCallback((modelKey: string) => {
    const { pathname, search, hash } = window.location;
    window.history.replaceState(null, "", `${pathname}${searchWithModel(search, modelKey)}${hash}`);
    setWhere(readLocation());
  }, []);

  const link = (path: string) => withModel(path, model);
  const current = (path: string): "page" | "true" | undefined => {
    if (route === null || route.kind === "not_found") return undefined;
    if (pathOf(route) === path) return "page";
    return route.kind === "case" && path === "/cases/" ? "true" : undefined;
  };

  return (
    // The click handler is delegation for every link inside, not a control of its own.
    <div className="explorer" onClick={onClick}>
      <a className="skip" href="#main">
        {explorerLabels.skipToContent}
      </a>
      <header className="site-header">
        <div className="brand-row">
          <Logo size={36} />
          <a className="site-name" href={link("/")}>
            Horizon Compact
          </a>
        </div>
        {catalog && (
          <nav aria-label={explorerLabels.navLabel}>
            <ul>
              <li>
                <a href={link("/")} aria-current={current("/")}>
                  {explorerLabels.navStory}
                </a>
              </li>
              {catalog.index.scenarios.map((s) => {
                const path = pathOf({ kind: "scenario", id: s.scenario_id });
                return (
                  <li key={s.scenario_id}>
                    <a href={link(path)} aria-current={current(path)}>
                      {explorerLabels.navScenario(s.scenario_id)}
                    </a>
                  </li>
                );
              })}
              <li>
                <a href={link("/cases/")} aria-current={current("/cases/")}>
                  {explorerLabels.navCases}
                </a>
              </li>
              <li>
                <a href={link("/studies/")} aria-current={current("/studies/")}>
                  {explorerLabels.navStudies}
                </a>
              </li>
              <li>
                <a href={link("/memos/")} aria-current={current("/memos/")}>
                  {explorerLabels.navMemos}
                </a>
              </li>
            </ul>
          </nav>
        )}
      </header>
      {catalog && route && route.kind !== "not_found" && (
        <ModelSwitch models={catalog.index.models} current={model} onChoose={chooseModel} />
      )}
      <main id="main" className="view" ref={main}>
        {catalog && route ? (
          <View route={route} index={catalog.index} casesIndex={catalog.casesIndex} model={model} />
        ) : failed ? (
          <p role="alert">{explorerLabels.loadFailed}</p>
        ) : (
          <p role="status">{explorerLabels.loading}</p>
        )}
      </main>
      <Footer />
    </div>
  );
}
