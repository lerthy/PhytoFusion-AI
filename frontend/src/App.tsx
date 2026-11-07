import { useEffect, useRef, useState } from "react";
import { Icon } from "./components/Icon";
import { ErrorBoundary } from "./components/ui";
import type { ParsedGenome } from "./gff3";
import { NAV, navOf, parseRoute, ROUTES, routeHash, TAB_LABEL, type RouteId } from "./router";
import { About } from "./screens/About";
import { CrisprStudio } from "./screens/CrisprStudio";
import { Dashboard } from "./screens/Dashboard";
import { Evidence } from "./screens/Evidence";
import { GeneBridge } from "./screens/GeneBridge";
import { GenomeExplorer } from "./screens/GenomeExplorer";
import { PathwayExplorer } from "./screens/PathwayExplorer";
import { VirtualPlantReport } from "./screens/VirtualPlantReport";
import type { SimulateResult } from "./types";

export default function App() {
  const [route, setRoute] = useState<RouteId>(() => parseRoute(window.location.hash));
  const [host, setHost] = useState<ParsedGenome | null>(null);
  const [donor, setDonor] = useState<ParsedGenome | null>(null);
  const [result, setResult] = useState<SimulateResult | null>(null);
  const first = useRef(true);

  // Deep links and the back button: the URL hash is the source of truth.
  useEffect(() => {
    const onHash = () => setRoute(parseRoute(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // After navigating, move focus to the page title so screen readers announce the new screen.
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    document.getElementById("page-title")?.focus({ preventScroll: true });
    document.title = `${ROUTES.find((r) => r.id === route)?.label} · PhytoFusion AI`;
  }, [route]);

  const goTo = (id: RouteId) => { window.location.hash = routeHash(id); };
  const step = navOf(route);

  if (route === "about") return <About onStart={() => goTo("dashboard")} />;

  return (
    <div className="shell">
      <a className="skip" href="#content" onClick={(e) => { e.preventDefault(); document.getElementById("page-title")?.focus(); }}>Skip to content</a>
      <header className="topbar">
        <a className="brand" href={routeHash("about")} aria-label="PhytoFusion AI, about this site"><span className="logo"><Icon name="dna" size={24} /></span>PhytoFusion AI</a>
        <nav className="topnav" aria-label="Main">
          <ul>
            {NAV.map((n, i) => (
              <li key={n.id}>
                <button className="navlink" aria-current={n.id === step.id ? "page" : undefined} onClick={() => goTo(n.routes[0])}>
                  {i > 0 && <span className="num" aria-hidden="true">{i}</span>}{n.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main id="content">
        {step.routes.length > 1 && (
          <div className="subnav" role="tablist" aria-label={`${step.label} sections`}>
            {step.routes.map((r) => (
              <button key={r} role="tab" aria-selected={r === route} aria-current={r === route ? "page" : undefined} onClick={() => goTo(r)}>{TAB_LABEL[r]}</button>
            ))}
          </div>
        )}
        <ErrorBoundary key={route}>
          <div className="page">
          {route === "dashboard" && <Dashboard host={host} donor={donor} goTo={goTo} />}
          {route === "genome" && <GenomeExplorer host={host} donor={donor} setHost={setHost} setDonor={setDonor} />}
          {route === "evidence" && <Evidence />}
          {route === "genebridge" && <GeneBridge />}
          {route === "pathway" && <PathwayExplorer />}
          {route === "crispr" && <CrisprStudio host={host} donor={donor} onResult={setResult} goToReport={() => goTo("report")} />}
          {route === "report" && <VirtualPlantReport result={result} onOpen={setResult} goToScenario={() => goTo("crispr")} />}
          </div>
        </ErrorBoundary>
        <footer className="app-foot">Hypothetical, computational scenarios only. Evidence levels say how well a claim is supported, not whether it would work.</footer>
      </main>
    </div>
  );
}
