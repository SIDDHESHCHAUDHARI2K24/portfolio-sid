import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import Markdown from "./Markdown";

const render = (body: string) => renderToStaticMarkup(<Markdown body={body} />);

describe("Markdown", () => {
  it("renders GFM tables", () => {
    const html = render("| a | b |\n|---|---|\n| 1 | 2 |");
    expect(html).toContain("<table>");
    expect(html).toContain("<td>1</td>");
  });

  it("renders a raw <script> tag as inert text, never as an element", () => {
    const html = render("hello\n\n<script>alert(1)</script>\n");
    expect(html).not.toMatch(/<script/i);
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
  });

  it("does not render raw html elements such as <img onerror>", () => {
    const html = render('<img src=x onerror="alert(1)">');
    expect(html).not.toMatch(/<img/i);
    expect(html).toContain("&lt;img");
  });

  it("strips javascript: link targets", () => {
    const html = render("[click](javascript:alert(1))");
    expect(html).not.toMatch(/javascript:/i);
  });

  it("renders headings and links normally", () => {
    const html = render("# Title\n\n[ok](https://example.com)");
    expect(html).toContain("<h1>Title</h1>");
    expect(html).toContain('href="https://example.com"');
  });
});
