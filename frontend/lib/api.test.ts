import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

describe("apiFetch build-phase retries", () => {
  function sequenceFetch(steps: Array<number | Error>) {
    let i = 0;
    const fn = vi.fn(async () => {
      const step = steps[Math.min(i++, steps.length - 1)];
      if (step instanceof Error) throw step;
      return new Response(JSON.stringify({ ok: true }), { status: step, statusText: step === 404 ? "Not Found" : "Err" });
    });
    vi.stubGlobal("fetch", fn);
    return fn;
  }

  async function run<T>(p: Promise<T>): Promise<T | unknown> {
    const settled = p.catch((e: unknown) => e);
    await vi.runAllTimersAsync();
    return settled;
  }

  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("skips retrying an unresolvable private host and retries the public proxy", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    vi.stubEnv("BACKEND_URL", "http://backend.railway.internal:8080");
    vi.stubEnv("PUBLIC_API_PROXY", "https://proxy.example.com");
    vi.resetModules();
    const { apiFetch: freshApiFetch } = await import("./api");
    const enotfound = Object.assign(new TypeError("fetch failed"), { cause: { code: "ENOTFOUND" } });
    const fn = sequenceFetch([enotfound, 502, 200]);
    await expect(run(freshApiFetch("/x"))).resolves.toEqual({ ok: true });
    const urls = fn.mock.calls.map((c) => String((c as unknown[])[0]));
    expect(urls).toEqual([
      "http://backend.railway.internal:8080/api/v1/x",
      "https://proxy.example.com/api/v1/x",
      "https://proxy.example.com/api/v1/x",
    ]);
  });

  it("retries 502, 502, 200 at build phase", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    const fn = sequenceFetch([502, 502, 200]);
    await expect(run(apiFetch("/x"))).resolves.toEqual({ ok: true });
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it("does not retry at runtime", async () => {
    const fn = sequenceFetch([502, 502, 200]);
    const err = await run(apiFetch("/x"));
    expect(err).toBeInstanceOf(ApiError);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("does not retry 404 at build phase", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    const fn = sequenceFetch([404]);
    const err = await run(apiFetch("/x"));
    expect(isNotFoundError(err)).toBe(true);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("does not retry 500 at build phase", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    const fn = sequenceFetch([500, 200]);
    const err = await run(apiFetch("/x"));
    expect((err as ApiError).status).toBe(500);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("retries a network error then succeeds at build phase", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    const fn = sequenceFetch([new TypeError("fetch failed"), 200]);
    await expect(run(apiFetch("/x"))).resolves.toEqual({ ok: true });
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it("gives up after 6 retries", async () => {
    vi.stubEnv("NEXT_PHASE", "phase-production-build");
    const fn = sequenceFetch([503]);
    const err = await run(apiFetch("/x"));
    expect((err as ApiError).status).toBe(503);
    expect(fn).toHaveBeenCalledTimes(7);
  });
});
