import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, getStats, simulate } from "./api";

const respond = (status: number, body: unknown) =>
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })));

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("returns parsed JSON on success", async () => {
    respond(200, { genes: 4 });
    expect(await getStats()).toEqual({ genes: 4 });
  });

  it("marks a 503 as 'not configured' and keeps the server's message", async () => {
    respond(503, { detail: "Database not configured: SUPABASE_URL must be set" });
    const err = await getStats().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.notConfigured).toBe(true);
    expect(err.message).toContain("SUPABASE_URL");
  });

  it("surfaces validation details from a 422", async () => {
    respond(422, { detail: "donor_integration requires donor_species" });
    const err = await simulate({} as never).catch((e) => e);
    expect(err.status).toBe(422);
    expect(err.notConfigured).toBe(false);
    expect(err.message).toBe("donor_integration requires donor_species");
  });

  it("stringifies structured error details", async () => {
    respond(422, { detail: [{ msg: "bad" }] });
    expect((await getStats().catch((e) => e)).message).toContain("bad");
  });

  it("explains when the backend cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("network"); }));
    const err = await getStats().catch((e) => e);
    expect(err.status).toBe(0);
    expect(err.message).toMatch(/Cannot reach the backend/);
  });
});
