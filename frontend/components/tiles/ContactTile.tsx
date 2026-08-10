import type { Tile } from "@/lib/tiles";

export function buildContactTile(): Tile {
  return {
    id: "contact",
    title: "Contact",
    summary: "Get in touch — email, LinkedIn, Cal.com booking, and resume downloads.",
    href: "/contact",
    audiences: [],
    priority: 10,
    isEmpty: false,
  };
}
