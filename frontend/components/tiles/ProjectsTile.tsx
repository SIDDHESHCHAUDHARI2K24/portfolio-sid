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

  const latest = projects[0];

  return {
    id: "projects",
    title: "Projects",
    summary: latest.summary ?? latest.title,
    href: "/projects",
    audiences: ["recruiters", "techies", "investors", "founders"],
    priority: 19,
    isEmpty: false,
  };
}
