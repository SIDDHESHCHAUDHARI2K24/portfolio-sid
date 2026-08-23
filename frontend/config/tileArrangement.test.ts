import { describe, expect, it } from "vitest";
import { tileArrangement } from "@/config/tileArrangement";

const AUDIENCES = ["recruiters", "techies", "investors", "founders", "personal", "default"] as const;

describe("tileArrangement (TD-31 card contract)", () => {
  it("defines an arrangement for every audience plus default", () => {
    for (const audience of AUDIENCES) {
      expect(Array.isArray(tileArrangement[audience])).toBe(true);
      expect(tileArrangement[audience].length).toBeGreaterThan(0);
    }
  });

  it("places contact directly below the main tile (first) for every audience", () => {
    for (const audience of AUDIENCES) {
      expect(tileArrangement[audience][0]).toBe("contact");
    }
  });

  it("default arrangement is complete — includes every tile used by any audience", () => {
    const all = new Set(Object.values(tileArrangement).flat());
    for (const id of all) {
      expect(tileArrangement.default, `default must include "${id}"`).toContain(id);
    }
  });

  it("default shows everything exactly once", () => {
    expect(new Set(tileArrangement.default).size).toBe(tileArrangement.default.length);
  });

  it("personal deliberately excludes professional-only tiles", () => {
    for (const excluded of ["projects", "skills", "certifications", "thesis", "dealflow"]) {
      expect(tileArrangement.personal, `"${excluded}" must not appear for personal`).not.toContain(
        excluded,
      );
    }
  });

  it("no audience arrangement contains duplicates or unknown ordering gaps", () => {
    for (const audience of AUDIENCES) {
      const ids = tileArrangement[audience];
      expect(new Set(ids).size).toBe(ids.length);
    }
  });
});
