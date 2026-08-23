import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { Project } from "@/features/projects/lib/types";
import ProjectDetail from "@/features/projects/components/ProjectDetail";
import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { buildCreativeWorkJsonLd } from "@/lib/jsonld";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const project = await apiFetch<Project>(`/projects/${slug}`, {
      tags: [CACHE_TAGS.projects],
    });
    const description = project.summary ?? project.description ?? undefined;
    return {
      title: `${project.title} — Siddhesh Chaudhari`,
      description,
      alternates: { canonical: `/projects/${slug}` },
      openGraph: {
        title: `${project.title} — Siddhesh Chaudhari`,
        description,
        type: "article",
      },
      twitter: {
        card: "summary",
      },
    };
  } catch {
    return { title: "Project — Siddhesh Chaudhari" };
  }
}

export default async function ProjectPage({ params }: Props) {
  const { slug } = await params;

  let project: Project;
  try {
    project = await apiFetch<Project>(`/projects/${slug}`, {
      tags: [CACHE_TAGS.projects],
    });
  } catch {
    notFound();
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildCreativeWorkJsonLd(project)),
        }}
      />
      <main className="flex flex-1 flex-col px-6 py-12">
        <Suspense>
          <ProjectDetail project={project} />
        </Suspense>
      </main>
    </>
  );
}
