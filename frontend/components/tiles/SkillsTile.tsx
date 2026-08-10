import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type Skill = paths["/api/v1/skills"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildSkillsTile(skills: Skill[]): Tile {
  if (skills.length === 0) {
    return {
      id: "skills",
      title: "",
      summary: "",
      href: "/skills",
      audiences: [],
      priority: 15,
      isEmpty: true,
    };
  }

  const sections = new Set(skills.map((s) => s.section));
  const sectionLabels: Record<string, string> = {
    languages: "languages",
    tools: "tools",
    frameworks: "frameworks",
    ai: "AI/Data",
    business: "business",
  };

  const summary = [...sections]
    .map((s) => sectionLabels[s] ?? s)
    .join(", ");

  return {
    id: "skills",
    title: "Skills",
    summary: `${skills.length} skills across ${summary}`,
    href: "/skills",
    audiences: ["recruiters", "techies", "investors", "founders"],
    priority: 15,
    isEmpty: false,
  };
}
