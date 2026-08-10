import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildBooksTile(items: Item[]): Tile {
  const books = items.filter((i) => i.kind === "book");
  if (books.length === 0) {
    return {
      id: "books",
      title: "",
      summary: "",
      href: "/books",
      audiences: [],
      priority: 12,
      isEmpty: true,
    };
  }

  const sections = [...new Set(books.map((b) => b.section).filter(Boolean))];
  const summary = sections.length > 0
    ? `${books.length} books across ${sections.join(", ")}`
    : `${books.length} books`;

  return {
    id: "books",
    title: "Bookshelf",
    summary,
    href: "/books",
    audiences: ["personal"],
    priority: 12,
    isEmpty: false,
  };
}
