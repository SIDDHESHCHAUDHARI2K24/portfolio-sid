"use client";

import { useCategory } from "@/components/CategoryProvider";
import { isRelevant } from "@/lib/relevance";
import type { paths } from "@/src/api";
import { Briefcase, GraduationCap } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { useEffect, useMemo, useState } from "react";
import FilterChips from "./FilterChips";

type Entry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMap = Record<string, string[]>;

interface Props {
  entries: Entry[];
  tagMap: TagMap;
}

export default function TimelineClient({ entries, tagMap }: Props) {
  const { category } = useCategory();
  const audience = category ?? "default";
  const searchParams = useSearchParams();

  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());

  useEffect(() => {
    const tagsParam = searchParams.get("tags");
    if (tagsParam) {
      setSelectedTags(new Set(tagsParam.split(",")));
    }
  }, [searchParams]);

  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash.startsWith("#entry-")) {
        setSelectedTags(new Set());
        const id = window.location.hash.slice(1);
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const el = document.getElementById(id);
            if (el) {
              el.scrollIntoView({ behavior: "smooth", block: "center" });
              el.classList.add("ring-2", "ring-primary", "rounded");
              setTimeout(() => {
                el.classList.remove("ring-2", "ring-primary", "rounded");
              }, 2000);
            }
          });
        });
      }
    };
    handleHash();
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  const tagMapNormalized: Record<string, Set<string>> = useMemo(() => {
    const map: Record<string, Set<string>> = {};
    for (const [key, slugs] of Object.entries(tagMap)) {
      map[key] = new Set(slugs);
    }
    return map;
  }, [tagMap]);

  const allTagSlugs = useMemo(() => {
    const slugs = new Map<string, string>();
    for (const entry of entries) {
      for (const tag of entry.topic_tags) {
        if (!slugs.has(tag.slug)) {
          slugs.set(tag.slug, tag.label);
        }
      }
    }
    return [...slugs.entries()].map(([slug, label]) => ({ slug, label }));
  }, [entries]);

  const filteredEntries = useMemo(() => {
    let result = entries;
    if (selectedTags.size > 0) {
      result = result.filter((entry) =>
        entry.topic_tags.some((t) => selectedTags.has(t.slug)),
      );
    }
    return result;
  }, [entries, selectedTags]);

  return (
    <div className="space-y-8 w-full max-w-3xl mx-auto">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight mb-4">Timeline</h1>
        <FilterChips
          allTagSlugs={allTagSlugs}
          selected={selectedTags}
          onChange={setSelectedTags}
        />
      </section>

      <div className="relative border-l border-border pl-6 space-y-10">
        {filteredEntries.map((entry) => {
          const itemTagSlugs = new Set(entry.topic_tags.map((t) => t.slug));
          const overrides = new Set<string>([]);
          const relevant =
            audience === "default" ||
            isRelevant(itemTagSlugs, overrides, audience, tagMapNormalized);

          return (
            <article
              key={entry.id}
              id={`entry-${entry.id}`}
              className={`relative transition-opacity ${
                relevant ? "opacity-100" : "opacity-50"
              }`}
            >
              <div className="absolute -left-[calc(1.5rem+2px)] top-1 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card">
                {entry.kind === "education" ? (
                  <GraduationCap className="h-4 w-4" />
                ) : (
                  <Briefcase className="h-4 w-4" />
                )}
              </div>

              <div className="space-y-2">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                  <Link
                    href={`/timeline/${entry.id}`}
                    className="text-lg font-semibold hover:underline hover:text-primary transition-colors"
                  >
                    {entry.title}
                  </Link>
                  <span className="text-sm text-muted-foreground">
                    at {entry.organisation}
                  </span>
                </div>

                <p className="text-sm text-muted-foreground">
                  {formatDate(entry.start_date)}
                  {entry.end_date ? ` — ${formatDate(entry.end_date)}` : " — Present"}
                  {entry.location ? ` · ${entry.location}` : ""}
                </p>

                {entry.summary && (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      rehypePlugins={[rehypeSanitize]}
                      remarkPlugins={[remarkGfm]}
                    >
                      {entry.summary}
                    </ReactMarkdown>
                  </div>
                )}

                {entry.highlights && entry.highlights.length > 0 && (
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {entry.highlights.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                )}

                {entry.topic_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
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
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short" });
}
