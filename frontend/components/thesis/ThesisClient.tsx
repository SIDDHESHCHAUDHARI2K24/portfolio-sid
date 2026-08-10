"use client";

import { useCategory } from "@/components/CategoryProvider";
import { isRelevant } from "@/lib/relevance";
import { useMemo } from "react";

type TagRef = { id: string; slug: string; label: string };
type ThesisEntry = {
  id: string;
  title: string;
  summary: string | null;
  drive_url: string;
  published_date: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
  topic_tags: TagRef[];
  audience_override?: string[] | null;
};

type TagMap = Record<string, string[]>;

interface Props {
  entries: ThesisEntry[];
  tagMap: TagMap;
}

export default function ThesisClient({ entries, tagMap }: Props) {
  const { category } = useCategory();
  const audience = category ?? "default";

  const tagMapNormalized = useMemo(() => {
    const map: Record<string, Set<string>> = {};
    for (const [key, slugs] of Object.entries(tagMap)) {
      map[key] = new Set(slugs);
    }
    return map;
  }, [tagMap]);

  return (
    <div className="space-y-8 w-full max-w-3xl mx-auto">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight mb-2">
          Investment Thesis
        </h1>
        <p className="text-muted-foreground">
          Documents on how I think about markets, technology, and early-stage investing.
        </p>
      </section>

      {entries.length === 0 ? (
        <p className="text-muted-foreground">No thesis entries published yet.</p>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          {entries.map((entry) => {
            const itemTagSlugs = new Set<string>(
              entry.topic_tags.map((t: TagRef) => t.slug)
            );
            const overrides = new Set<string>(entry.audience_override ?? []);
            const relevant =
              audience === "default" ||
              isRelevant(itemTagSlugs, overrides, audience, tagMapNormalized);

            return (
              <a
                key={entry.id}
                href={entry.drive_url}
                rel="noopener noreferrer"
                target="_blank"
                className={`block rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-sm ${
                  relevant ? "opacity-100" : "opacity-50"
                }`}
              >
                <div className="mb-1">
                  <span className="text-xs text-muted-foreground">
                    {new Date(entry.published_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
                <h2 className="text-lg font-semibold mb-1">{entry.title}</h2>
                {entry.summary && (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {entry.summary}
                  </p>
                )}
                {entry.topic_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {entry.topic_tags.map((t: TagRef) => (
                      <span
                        key={t.slug}
                        className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                      >
                        {t.label}
                      </span>
                    ))}
                  </div>
                )}
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
