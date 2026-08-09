import { describe, expect, it } from "vitest";
import { isRelevant } from "./relevance";

const TAG_MAP: Record<string, Set<string>> = {
  recruiters: new Set(["engineering", "consulting"]),
  techies: new Set(["ai", "engineering"]),
  investors: new Set(),
};

describe("isRelevant", () => {
  it("returns false when item has no tags", () => {
    expect(isRelevant(new Set(), new Set(), "recruiters", TAG_MAP)).toBe(false);
  });

  it("returns true only for the matching audience", () => {
    expect(isRelevant(new Set(["consulting"]), new Set(), "recruiters", TAG_MAP)).toBe(true);
    expect(isRelevant(new Set(["consulting"]), new Set(), "techies", TAG_MAP)).toBe(false);
    expect(isRelevant(new Set(["consulting"]), new Set(), "investors", TAG_MAP)).toBe(false);
  });

  it("returns true for tags matching several audiences", () => {
    expect(isRelevant(new Set(["engineering"]), new Set(), "recruiters", TAG_MAP)).toBe(true);
    expect(isRelevant(new Set(["engineering"]), new Set(), "techies", TAG_MAP)).toBe(true);
  });

  it("returns true when audience is in overrides even with no matching tags", () => {
    expect(
      isRelevant(new Set(["knitting"]), new Set(["investors"]), "investors", TAG_MAP),
    ).toBe(true);
  });

  it("returns true when audience is in overrides and tags also match", () => {
    expect(
      isRelevant(new Set(["engineering"]), new Set(["recruiters"]), "recruiters", TAG_MAP),
    ).toBe(true);
  });

  it("returns false for audience with empty tag map", () => {
    expect(isRelevant(new Set(["startup"]), new Set(), "investors", TAG_MAP)).toBe(false);
    expect(isRelevant(new Set(["startup"]), new Set(), "founders", TAG_MAP)).toBe(false);
  });

  it("returns false for default audience (not in map)", () => {
    expect("default" in TAG_MAP).toBe(false);
    expect(isRelevant(new Set(["engineering", "ai"]), new Set(), "default", TAG_MAP)).toBe(false);
  });

  it("returns true when override contains audience regardless of map", () => {
    expect(isRelevant(new Set(), new Set(["founders"]), "founders", {})).toBe(true);
    expect(isRelevant(new Set(), new Set(["founders"]), "founders", TAG_MAP)).toBe(true);
  });
});
