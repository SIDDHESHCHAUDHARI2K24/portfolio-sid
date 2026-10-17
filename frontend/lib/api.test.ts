import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, isNotFoundError } from "./api";

function mockFetch(status: number, body: unknown = {}) {
  const fn = vi.fn(async () =>
    new Response(JSON.stringify(body), { status, statusText: status === 404 ? "Not Found" : "Err" }),
  );
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch errors", () => {
  it("returns parsed JSON on 200", async () => {
    mockFetch(200, { ok: true });
    await expect(apiFetch("/x")).resolves.toEqual({ ok: true });
  });

  it("throws ApiError carrying status on 404 and keeps the old message shape", async () => {
    mockFetch(404);
    const err = await apiFetch("/x").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toBeInstanceOf(Error);
    expect((err as ApiError).status).toBe(404);
    expect((err as Error).message).toBe("API 404: Not Found");
    expect(isNotFoundError(err)).toBe(true);
  });

  it("is not a 'not found' for 5xx, so pages rethrow and ISR keeps the stale page", async () => {
    mockFetch(503);
    const err = await apiFetch("/x").catch((e: unknown) => e);
    expect((err as ApiError).status).toBe(503);
    expect(isNotFoundError(err)).toBe(false);
  });

  it("network failures are not 'not found'", () => {
    expect(isNotFoundError(new TypeError("fetch failed"))).toBe(false);
    expect(isNotFoundError(undefined)).toBe(false);
  });
});
