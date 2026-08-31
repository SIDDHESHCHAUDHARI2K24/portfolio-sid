import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import { buildBreadcrumbJsonLd, buildTimelineEntryJsonLd } from "@/lib/jsonld";
import type { paths } from "@/src/api";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { Briefcase, GraduationCap } from "lucide-react";

type TimelineEntry =
  paths["/api/v1/timeline/{entry_id}"]["get"]["responses"]["200"]["content"]["application/json"];
type Project =
  paths["/api/v1/projects"]["get"]["responses"]["200"]["content"]["application/json"][number];

interface Props {
  params: Promise<{ id: string }>;
}

export const revalidate = 3600;

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short" });
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  try {
    const entry = await apiFetch<TimelineEntry>(`/timeline/${id}`, {
      tags: [CACHE_TAGS.timeline],
      revalidate: 3600,
    });
    const title = `${entry.title} — ${entry.organisation} — Siddhesh Chaudhari`;
    const description = entry.summary ?? `${entry.title} at ${entry.organisation}`;
    return {
      title,
      description,
      alternates: { canonical: `/timeline/${id}` },
      openGraph: {
        title,
        description,
        type: "article",
      },
      twitter: { card: "summary" },
    };
  } catch {
    return { title: "Timeline — Siddhesh Chaudhari" };
  }
}

export default async function TimelineDetailPage({ params }: Props) {
  const { id } = await params;

  let entry: TimelineEntry;
  try {
    entry = await apiFetch<TimelineEntry>(`/timeline/${id}`, {
      tags: [CACHE_TAGS.timeline],
      revalidate: 3600,
    });
  } catch {
    notFound();
  }

  let projects: Project[] = [];
  try {
    projects = await apiFetch<Project[]>(`/timeline/${id}/projects`, {
      tags: [CACHE_TAGS.timeline, CACHE_TAGS.projects],
      revalidate: 3600,
    });
  } catch {
    projects = [];
  }

  const breadcrumbJsonLd = buildBreadcrumbJsonLd([
    { name: "Timeline", url: "/timeline" },
    { name: `${entry.title} at ${entry.organisation}`, url: `/timeline/${entry.id}` },
  ]);

  const entryJsonLd = buildTimelineEntryJsonLd(entry as unknown as TimelineEntry & { topic_tags: { label: string; slug: string; id: string }[] });

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(entryJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="space-y-8 w-full max-w-3xl mx-auto">
          <Link
            href="/timeline"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; All Timeline
          </Link>

          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card">
                {entry.kind === "education" ? (
                  <GraduationCap className="h-4 w-4" />
                ) : (
                  <Briefcase className="h-4 w-4" />
                )}
              </div>
              <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium capitalize text-secondary-foreground">
                {entry.kind}
              </span>
            </div>

            <h1 className="text-3xl font-semibold tracking-tight">
              {entry.title}{" "}
              <span className="text-muted-foreground font-normal text-2xl">
                at {entry.organisation}
              </span>
            </h1>

            <p className="text-sm text-muted-foreground">
              {formatDate(entry.start_date)}
              {entry.end_date ? ` — ${formatDate(entry.end_date)}` : " — Present"}
              {entry.location ? ` · ${entry.location}` : ""}
            </p>

            {entry.external_url && (
              <p>
                <a
                  href={entry.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  {entry.external_url} &rarr;
                </a>
              </p>
            )}
          </section>

          {entry.summary && (
            <section className="prose prose-neutral dark:prose-invert max-w-none">
              <ReactMarkdown rehypePlugins={[rehypeSanitize]} remarkPlugins={[remarkGfm]}>
                {entry.summary}
              </ReactMarkdown>
            </section>
          )}

          {entry.highlights && entry.highlights.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-3">Highlights</h2>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {entry.highlights.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </section>
          )}

          {entry.topic_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {entry.topic_tags.map((t) => (
                <span
                  key={t.slug}
                  className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                >
                  {t.label}
                </span>
              ))}
            </div>
          )}

          {projects.length > 0 && (
            <section className="space-y-4 pt-6 border-t border-border">
              <h2 className="text-xl font-semibold">Related Projects</h2>
              <div className="grid gap-6 sm:grid-cols-2">
                {projects.map((project) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.slug}`}
                    className="block rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-sm"
                  >
                    <h3 className="text-lg font-semibold mb-1">{project.title}</h3>
                    {project.summary && (
                      <p className="text-sm text-muted-foreground line-clamp-3">{project.summary}</p>
                    )}
                    {project.topic_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-3">
                        {project.topic_tags.map((t) => (
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
                ))}
              </div>
            </section>
          )}

          <div className="pt-4">
            <Link
              href={`/timeline#entry-${entry.id}`}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Back to timeline &rarr; #{entry.id.slice(0, 8)}
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
