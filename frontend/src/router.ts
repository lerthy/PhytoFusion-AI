export const ROUTES = [
  { id: "about", label: "About" },
  { id: "dashboard", label: "Home" },
  { id: "genome", label: "Genomes" },
  { id: "evidence", label: "Evidence" },
  { id: "genebridge", label: "Compare genes" },
  { id: "pathway", label: "Pathways" },
  { id: "crispr", label: "New scenario" },
  { id: "report", label: "Report" },
] as const;

export type RouteId = (typeof ROUTES)[number]["id"];

/** The landing page ("about") sits outside the app navigation.
    Four top-level steps. Related screens live behind one step as tabs. */
export const NAV = [
  { id: "dashboard", label: "Home", routes: ["dashboard"] },
  { id: "genome", label: "Genomes", routes: ["genome"] },
  { id: "compare", label: "Compare", routes: ["genebridge", "pathway", "evidence"] },
  { id: "simulate", label: "Simulate", routes: ["crispr", "report"] },
] as const satisfies readonly { id: string; label: string; routes: readonly RouteId[] }[];

export type NavItem = (typeof NAV)[number];

/** Short tab names shown inside a step that has more than one screen. */
export const TAB_LABEL: Record<RouteId, string> = {
  about: "About", dashboard: "Home", genome: "Genomes", genebridge: "Genes", pathway: "Pathways",
  evidence: "Evidence", crispr: "Scenario", report: "Report",
};

export const navOf = (route: RouteId): NavItem => NAV.find((n) => (n.routes as readonly RouteId[]).includes(route)) ?? NAV[0];

/** "#/genome" -> "genome". An empty or unknown hash opens the About page, the front door. */
export function parseRoute(hash: string): RouteId {
  const id = hash.replace(/^#\/?/, "").split("?")[0];
  return ROUTES.find((r) => r.id === id)?.id ?? "about";
}

export const routeHash = (id: RouteId) => `#/${id}`;
