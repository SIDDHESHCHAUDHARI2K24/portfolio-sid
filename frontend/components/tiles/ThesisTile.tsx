import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type ThesisItem = paths["/api/v1/thesis"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildThesisTile(entries: ThesisItem[]): Tile {
  if (entries.length === 0) {
    return {
      id: "thesis",
      title: "",
      summary: "",
      href: "/thesis",
      audiences: [],
      priority: 15,
      isEmpty: true,
    };
  }

  const pinned = entries.find((e) => e.is_pinned);
  const sorted = entries
    .slice()
    .sort(
      (a, b) =>
        new Date(b.published_date).getTime() - new Date(a.published_date).getTime()
    );
  const display = pinned ?? sorted[0];

  return {
    id: "thesis",
    title: "Investment Thesis",
    summary: display.title,
    href: "/thesis",
    audiences: ["investors"],
    priority: 15,
    isEmpty: false,
  };
}
