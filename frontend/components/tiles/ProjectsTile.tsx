import type { Tile } from "@/lib/tiles";
import type { Project } from "@/features/projects/lib/types";

export function buildProjectsTile(projects: Project[]): Tile {
  if (projects.length === 0) {
    return {
      id: "projects",
      title: "",
      summary: "",
      href: "/projects",
      audiences: [],
      priority: 19,
      isEmpty: true,
    };
  }

  const pinned = projects.find((p) => p.is_pinned);
  const display = pinned ?? projects[0];

  return {
    id: "projects",
    title: "Projects",
    summary: display.summary ?? display.title,
    href: "/projects",
    audiences: ["recruiters", "techies", "investors", "founders"],
    priority: 19,
    isEmpty: false,
  };
}
