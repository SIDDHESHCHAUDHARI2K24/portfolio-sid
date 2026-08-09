"use client";

import { useCategory } from "@/components/CategoryProvider";
import { isRelevant } from "@/lib/relevance";
import type { Project } from "@/features/projects/lib/types";
import { useMemo } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

type TagMap = Record<string, string[]>;

interface Props {
  projects: Project[];
  tagMap: TagMap;
}

export default function ProjectsClient({ projects, tagMap }: Props) {
  const { category } = useCategory();
  const audience = category ?? "default";

  const tagMapNormalized: Record<string, Set<string>> = useMemo(() => {
    const map: Record<string, Set<string>> = {};
    for (const [key, slugs] of Object.entries(tagMap)) {
      map[key] = new Set(slugs);
    }
    return map;
  }, [tagMap]);

  return (
    <div className="space-y-8 w-full max-w-3xl mx-auto">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight mb-2">Projects</h1>
        <p className="text-muted-foreground">
          Things I&apos;ve built and shipped.
        </p>
      </section>

      {projects.length === 0 ? (
        <p className="text-muted-foreground">No projects published yet.</p>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          {projects.map((project) => {
            const itemTagSlugs = new Set<string>(
              project.topic_tags.map((t: { slug: string }) => t.slug)
            );
            const overrides = new Set<string>([]);
            const relevant =
              audience === "default" ||
              isRelevant(itemTagSlugs, overrides, audience, tagMapNormalized);

            return (
              <Link
                key={project.id}
                href={`/projects/${project.slug}`}
                className={`block rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-sm ${
                  relevant ? "opacity-100" : "opacity-50"
                }`}
              >
                <h2 className="text-lg font-semibold mb-1">{project.title}</h2>
                {project.summary && (
                  <div className="prose prose-sm max-w-none text-muted-foreground line-clamp-3">
                    <ReactMarkdown
                      rehypePlugins={[rehypeSanitize]}
                      remarkPlugins={[remarkGfm]}
                    >
                      {project.summary}
                    </ReactMarkdown>
                  </div>
                )}
                {project.topic_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {project.topic_tags.map((t: { slug: string; label: string }) => (
                      <span
                        key={t.slug}
                        className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                      >
                        {t.label}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
