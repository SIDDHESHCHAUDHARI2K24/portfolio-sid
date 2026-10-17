import { describe, expect, it } from "vitest";
import { buildArticleJsonLd } from "./jsonld";

describe("buildArticleJsonLd", () => {
  const post = {
    title: "Hello",
    slug: "hello",
    summary: "A summary",
    published_date: "2026-05-01",
    created_at: "2026-04-30T10:00:00Z",
    updated_at: "2026-05-02T10:00:00Z",
    topic_tags: [{ id: "1", slug: "ai", label: "AI" }],
  };

  it("builds an Article with the canonical /writing url", () => {
    const ld = buildArticleJsonLd(post);
    expect(ld["@type"]).toBe("Article");
    expect(ld.headline).toBe("Hello");
    expect(ld.url).toMatch(/\/writing\/hello$/);
    expect(ld.mainEntityOfPage).toBe(ld.url);
    expect(ld.datePublished).toBe("2026-05-01");
    expect(ld.dateModified).toBe(post.updated_at);
    expect(ld.keywords).toBe("AI");
  });

  it("falls back to created_at when there is no published_date", () => {
    expect(buildArticleJsonLd({ ...post, published_date: null }).datePublished).toBe(
      post.created_at,
    );
  });
});
