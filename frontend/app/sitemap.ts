import type { MetadataRoute } from "next";
import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";

type Project = paths["/api/v1/projects"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ProsePage = paths["/api/v1/prose"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TimelineEntry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

const STATIC_ROUTES = [
  "/",
  "/timeline",
  "/projects",
  "/skills",
  "/certifications",
  "/tech-rabbithole",
  "/how-i-use-ai",
  "/vc-for-founders",
  "/thesis",
  "/books",
  "/anime-manga",
  "/contact",
  "/dealflow",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [];

  for (const route of STATIC_ROUTES) {
    entries.push({
      url: `${BASE_URL}${route}`,
      lastModified: new Date(),
    });
  }

  try {
    const projects = await apiFetch<Project[]>("/projects", {
      tags: [CACHE_TAGS.projects],
    });
    for (const p of projects) {
      entries.push({
        url: `${BASE_URL}/projects/${p.slug}`,
        lastModified: new Date(p.updated_at),
      });
    }
  } catch {}

  try {
    const prose = await apiFetch<ProsePage[]>("/prose", {
      tags: [CACHE_TAGS.prose],
    });
    for (const page of prose) {
      entries.push({
        url: `${BASE_URL}/${page.slug}`,
        lastModified: new Date(page.updated_at),
      });
    }
  } catch {}

  try {
    const timeline = await apiFetch<TimelineEntry[]>("/timeline", {
      tags: [CACHE_TAGS.timeline],
    });
    for (const e of timeline) {
      entries.push({
        url: `${BASE_URL}/timeline/${e.id}`,
        lastModified: new Date(e.updated_at),
      });
    }
  } catch {}

  return entries;
}
