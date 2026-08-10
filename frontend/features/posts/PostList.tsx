"use client";

import { useCategory } from "@/components/CategoryProvider";
import { isRelevant } from "@/lib/relevance";
import { useMemo } from "react";

type TagRef = { id: string; slug: string; label: string };
type PostItem = {
  id: string;
  title: string;
  summary: string | null;
  url: string;
  platform: string;
  published_date: string | null;
  collections: string[];
  sort_order: number;
  created_at: string;
  updated_at: string;
  topic_tags: TagRef[];
  audience_override?: string[] | null;
};

type TagMap = Record<string, string[]>;

interface Props {
  posts: PostItem[];
  tagMap: TagMap;
  heading: string;
  description: string;
}

const PLATFORM_LABELS: Record<string, string> = {
  substack: "Substack",
  medium: "Medium",
  youtube: "YouTube",
  other: "External",
};

export default function PostList({ posts, tagMap, heading, description }: Props) {
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
        <h1 className="text-3xl font-semibold tracking-tight mb-2">{heading}</h1>
        <p className="text-muted-foreground">{description}</p>
      </section>

      {posts.length === 0 ? (
        <p className="text-muted-foreground">No posts published yet.</p>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          {posts.map((post) => {
            const itemTagSlugs = new Set<string>(
              post.topic_tags.map((t: TagRef) => t.slug)
            );
            const overrides = new Set<string>(post.audience_override ?? []);
            const relevant =
              audience === "default" ||
              isRelevant(itemTagSlugs, overrides, audience, tagMapNormalized);

            return (
              <a
                key={post.id}
                href={post.url}
                rel="noopener noreferrer"
                target="_blank"
                className={`block rounded-lg border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-sm ${
                  relevant ? "opacity-100" : "opacity-50"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-mono text-secondary-foreground">
                    {PLATFORM_LABELS[post.platform] ?? post.platform}
                  </span>
                  {post.published_date && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(post.published_date).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                      })}
                    </span>
                  )}
                </div>
                <h2 className="text-lg font-semibold mb-1">{post.title}</h2>
                {post.summary && (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {post.summary}
                  </p>
                )}
                {post.topic_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {post.topic_tags.map((t: TagRef) => (
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
