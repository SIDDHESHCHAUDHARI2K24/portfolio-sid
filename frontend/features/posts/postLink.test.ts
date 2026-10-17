import { describe, expect, it } from "vitest";
import { postHref } from "./postLink";

describe("postHref", () => {
  it("links internal posts to /writing/<slug> in the same tab", () => {
    expect(postHref({ platform: "internal", slug: "my-post", url: null })).toEqual({
      href: "/writing/my-post",
      external: false,
    });
  });

  it("links external posts to their url in a new tab", () => {
    expect(
      postHref({ platform: "substack", slug: null, url: "https://s.example/p" }),
    ).toEqual({ href: "https://s.example/p", external: true });
  });

  it("ignores a leftover slug on external posts", () => {
    expect(
      postHref({ platform: "medium", slug: "old", url: "https://m.example/x" }),
    ).toEqual({ href: "https://m.example/x", external: true });
  });

  it("does not crash on an internal post without a slug", () => {
    expect(postHref({ platform: "internal", slug: null, url: null })).toEqual({
      href: "#",
      external: false,
    });
  });
});
