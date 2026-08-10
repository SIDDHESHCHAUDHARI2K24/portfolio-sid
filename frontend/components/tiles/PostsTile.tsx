import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type PostItem = paths["/api/v1/posts"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildTechRabbitholeTile(posts: PostItem[]): Tile {
  const filtered = posts.filter((p) =>
    p.collections.includes("tech_rabbithole")
  );

  if (filtered.length === 0) {
    return {
      id: "tech_rabbithole",
      title: "",
      summary: "",
      href: "/tech-rabbithole",
      audiences: [],
      priority: 24,
      isEmpty: true,
    };
  }

  const latest = filtered[0];
  return {
    id: "tech_rabbithole",
    title: "Tech Rabbithole",
    summary: latest.title,
    href: "/tech-rabbithole",
    audiences: [],
    priority: 24,
    isEmpty: false,
  };
}

export function buildHowIUseAiTile(posts: PostItem[]): Tile {
  const filtered = posts.filter((p) =>
    p.collections.includes("how_i_use_ai")
  );

  if (filtered.length === 0) {
    return {
      id: "how_i_use_ai",
      title: "",
      summary: "",
      href: "/how-i-use-ai",
      audiences: [],
      priority: 23,
      isEmpty: true,
    };
  }

  const latest = filtered[0];
  return {
    id: "how_i_use_ai",
    title: "How I Use AI",
    summary: latest.title,
    href: "/how-i-use-ai",
    audiences: ["techies", "founders", "recruiters", "investors"],
    priority: 23,
    isEmpty: false,
  };
}

export function buildVcForFoundersTile(posts: PostItem[]): Tile {
  const filtered = posts.filter((p) =>
    p.collections.includes("vc_for_founders")
  );

  if (filtered.length === 0) {
    return {
      id: "vc_for_founders",
      title: "",
      summary: "",
      href: "/vc-for-founders",
      audiences: [],
      priority: 22,
      isEmpty: true,
    };
  }

  const latest = filtered[0];
  return {
    id: "vc_for_founders",
    title: "VC for Founders",
    summary: latest.title,
    href: "/vc-for-founders",
    audiences: ["founders"],
    priority: 22,
    isEmpty: false,
  };
}
