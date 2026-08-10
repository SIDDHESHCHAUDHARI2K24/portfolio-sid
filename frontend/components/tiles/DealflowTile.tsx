import type { Tile } from "@/lib/tiles";

export function buildDealflowTile(): Tile {
  return {
    id: "dealflow",
    title: "Dealflow",
    summary: "Investors: share your firm and focus area to reach me directly.",
    href: "/dealflow",
    audiences: ["investors"],
    priority: 30,
    isEmpty: false,
  };
}
