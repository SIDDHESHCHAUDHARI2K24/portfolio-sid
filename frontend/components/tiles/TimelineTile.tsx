import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type Entry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildTimelineTile(entries: Entry[]): Tile {
  if (entries.length === 0) {
    return {
      id: "timeline",
      title: "",
      summary: "",
      href: "/timeline",
      audiences: [],
      priority: 20,
      isEmpty: true,
    };
  }

  const latest = entries[0];

  return {
    id: "timeline",
    title: "Timeline",
    summary: latest.summary ?? `${latest.title} at ${latest.organisation}`,
    href: "/timeline",
    audiences: [],
    priority: 20,
    isEmpty: false,
  };
}
