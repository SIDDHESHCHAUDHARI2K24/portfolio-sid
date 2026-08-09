import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { Project } from "@/features/projects/lib/types";
import ProjectsClient from "@/features/projects/components/ProjectsClient";
import type { Metadata } from "next";
import { Suspense } from "react";

type TagMapResponse = { [key: string]: string[] };

export const metadata: Metadata = {
  title: "Projects — Siddhesh Chaudhari",
  alternates: { canonical: "/projects" },
};

export default async function ProjectsPage() {
  const [projects, tagMap] = await Promise.all([
    apiFetch<Project[]>("/projects", { tags: [CACHE_TAGS.projects], revalidate: 3600 }),
    apiFetch<TagMapResponse>("/relevance/map", { tags: [CACHE_TAGS.relevance], revalidate: 3600 }),
  ]);

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <Suspense>
        <ProjectsClient projects={projects} tagMap={tagMap} />
      </Suspense>
    </main>
  );
}
