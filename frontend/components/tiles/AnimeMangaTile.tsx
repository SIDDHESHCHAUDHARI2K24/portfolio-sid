import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildAnimeMangaTile(items: Item[]): Tile {
  const animeManga = items.filter((i) => i.kind === "anime" || i.kind === "manhwa");
  if (animeManga.length === 0) {
    return {
      id: "anime_manga",
      title: "",
      summary: "",
      href: "/anime-manga",
      audiences: [],
      priority: 11,
      isEmpty: true,
    };
  }

  const animeCount = animeManga.filter((i) => i.kind === "anime").length;
  const manhwaCount = animeManga.filter((i) => i.kind === "manhwa").length;

  const parts: string[] = [];
  if (animeCount > 0) parts.push(`${animeCount} anime`);
  if (manhwaCount > 0) parts.push(`${manhwaCount} manhwa`);

  return {
    id: "anime_manga",
    title: "Anime & Manhwa",
    summary: parts.join(", "),
    href: "/anime-manga",
    audiences: ["personal"],
    priority: 11,
    isEmpty: false,
  };
}
