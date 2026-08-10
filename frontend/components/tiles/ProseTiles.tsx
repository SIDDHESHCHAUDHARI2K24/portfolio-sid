import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type ProsePage = paths["/api/v1/prose"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildHobbiesTile(pages: ProsePage[]): Tile {
  const items = pages.filter((p) => p.group === "hobbies");
  if (items.length === 0) {
    return {
      id: "hobbies",
      title: "",
      summary: "",
      href: "",
      audiences: [],
      priority: 10,
      isEmpty: true,
    };
  }

  return {
    id: "hobbies",
    title: "Hobbies",
    summary: items.map((p) => p.title).join(", "),
    href: `/${items[0].slug}`,
    audiences: ["personal"],
    priority: 10,
    isEmpty: false,
  };
}

export function buildWorkViewsTile(pages: ProsePage[]): Tile {
  const items = pages.filter((p) => p.group === "work_views");
  if (items.length === 0) {
    return {
      id: "work_views",
      title: "",
      summary: "",
      href: "",
      audiences: [],
      priority: 9,
      isEmpty: true,
    };
  }

  return {
    id: "work_views",
    title: "Work Views",
    summary: items.map((p) => p.title).join(", "),
    href: `/${items[0].slug}`,
    audiences: ["recruiters", "techies"],
    priority: 9,
    isEmpty: false,
  };
}

export function buildInvestorIntroTile(pages: ProsePage[]): Tile {
  const items = pages.filter((p) => p.group === "investor_intro");
  if (items.length === 0) {
    return {
      id: "investor_intro",
      title: "",
      summary: "",
      href: "",
      audiences: [],
      priority: 14,
      isEmpty: true,
    };
  }

  return {
    id: "investor_intro",
    title: items[0].title,
    summary: items[0].body.slice(0, 200).replace(/[#*_`]/g, ""),
    href: `/${items[0].slug}`,
    audiences: ["founders"],
    priority: 14,
    isEmpty: false,
  };
}
