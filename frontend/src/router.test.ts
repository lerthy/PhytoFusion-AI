import { describe, expect, it } from "vitest";
import { NAV, navOf, parseRoute, ROUTES, routeHash, TAB_LABEL } from "./router";

describe("router", () => {
  it("round-trips every route through the hash", () => {
    for (const r of ROUTES) expect(parseRoute(routeHash(r.id))).toBe(r.id);
  });

  it.each(["", "#", "#/", "#/nope", "#/genome/extra"])("opens the About page for %j", (hash) => {
    expect(parseRoute(hash)).toBe("about");
  });

  it("ignores a query string", () => {
    expect(parseRoute("#/evidence?x=1")).toBe("evidence");
  });

  it("keeps primary navigation to four steps and puts every screen in exactly one", () => {
    expect(NAV).toHaveLength(4);
    const all = NAV.flatMap((n) => [...n.routes]);
    // About is the landing page, outside the app navigation.
    expect([...all].sort()).toEqual(ROUTES.map((r) => r.id).filter((id) => id !== "about").sort());
    expect(new Set(all).size).toBe(all.length);
  });

  it("groups old deep links under their new step", () => {
    expect(navOf("pathway").id).toBe("compare");
    expect(navOf("evidence").id).toBe("compare");
    expect(navOf("report").id).toBe("simulate");
    expect(navOf("crispr").id).toBe("simulate");
  });

  it("has a tab label for every route", () => {
    for (const r of ROUTES) expect(TAB_LABEL[r.id]).toBeTruthy();
  });
});
