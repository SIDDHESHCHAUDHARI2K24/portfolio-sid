import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";

type Resume = paths["/api/v1/resumes"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ProsePage = paths["/api/v1/prose"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Project = paths["/api/v1/projects"]["get"]["responses"]["200"]["content"]["application/json"][number];

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
const PERSON_NAME = "Siddhesh Chaudhari";

export async function GET() {
  const lines: string[] = [];

  lines.push(`# ${PERSON_NAME}`);
  lines.push("");
  lines.push(
    "This site follows the llms.txt convention (llmstxt.org) — an emerging standard",
    "for making websites machine-readable to large language models.",
  );
  lines.push("");

  const sections: { title: string; url: string; description: string }[] = [
    { title: "Home", url: BASE_URL, description: "Audience-segmented portfolio overview" },
    { title: "Timeline", url: `${BASE_URL}/timeline`, description: "Career history — education, experience, and milestones" },
    { title: "Projects", url: `${BASE_URL}/projects`, description: "Software projects, tools, and experiments" },
    { title: "Skills", url: `${BASE_URL}/skills`, description: "Technical and business skills across languages, frameworks, AI, and strategy" },
    { title: "Certifications", url: `${BASE_URL}/certifications`, description: "Professional certifications (technical and business)" },
    { title: "Tech Rabbithole", url: `${BASE_URL}/tech-rabbithole`, description: "Deep dives into engineering problems and architecture decisions" },
    { title: "How I Use AI", url: `${BASE_URL}/how-i-use-ai`, description: "Tools, workflows, and prompts for practical AI use" },
    { title: "VC for Founders", url: `${BASE_URL}/vc-for-founders`, description: "Investment perspective and early-stage startup thinking" },
    { title: "Investment Thesis", url: `${BASE_URL}/thesis`, description: "Thesis statements on technology, markets, and trends" },
    { title: "Bookshelf", url: `${BASE_URL}/books`, description: "Curated reading list with notes" },
    { title: "Anime & Manhwa", url: `${BASE_URL}/anime-manga`, description: "Anime and manhwa collections with ratings" },
    { title: "Contact", url: `${BASE_URL}/contact`, description: "Email, LinkedIn, booking, and resume downloads" },
    { title: "Dealflow", url: `${BASE_URL}/dealflow`, description: "Investor introduction form" },
  ];

  lines.push("## Sections");
  lines.push("");
  for (const s of sections) {
    lines.push(`- [${s.title}](${s.url}): ${s.description}`);
  }
  lines.push("");

  try {
    const prose = await apiFetch<ProsePage[]>("/prose", {
      tags: [CACHE_TAGS.prose],
      revalidate: 3600,
    });
    if (prose.length > 0) {
      lines.push("## Prose Pages");
      lines.push("");
      for (const p of prose) {
        lines.push(`- [${p.title}](${BASE_URL}/${p.slug})`);
      }
      lines.push("");
    }
  } catch {}

  try {
    const projects = await apiFetch<Project[]>("/projects", {
      tags: [CACHE_TAGS.projects],
      revalidate: 3600,
    });
    if (projects.length > 0) {
      lines.push("## Project Detail Pages");
      lines.push("");
      for (const p of projects) {
        lines.push(`- [${p.title}](${BASE_URL}/projects/${p.slug})`);
      }
      lines.push("");
    }
  } catch {}

  try {
    const resumes = await apiFetch<Resume[]>("/resumes", {
      tags: [CACHE_TAGS.resumes],
      revalidate: 3600,
    });
    if (resumes.length > 0) {
      lines.push("## Resumes");
      lines.push("");
      for (const r of resumes) {
        lines.push(`- [${r.label} (${r.variant})](${BASE_URL}/media/${r.file_key})`);
      }
      lines.push("");
    }
  } catch {}

  return new NextResponse(lines.join("\n"), {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
