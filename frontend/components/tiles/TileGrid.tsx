"use client";

import { useCategory } from "@/components/CategoryProvider";
import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

type Intro = paths["/api/v1/overview"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMap = Record<string, string[]>;

interface Props {
  defaultIntro: Intro;
  allIntros: Intro[];
  tiles: Tile[];
}

export default function TileGrid({ defaultIntro, allIntros, tiles }: Props) {
  const { category } = useCategory();
  const audience = category ?? "default";
  const audienceSet = new Set<string>(audience === "default" ? [] : [audience]);

  const visibleTiles = tiles
    .filter((t) => !t.isEmpty)
    .filter((t) => {
      if (t.audiences.length === 0) return true;
      return t.audiences.some((a) => audienceSet.has(a));
    })
    .sort((a, b) => b.priority - a.priority);

  const intro = allIntros.find((i) => i.audience === audience) ?? defaultIntro;

  return (
    <div className="space-y-16 w-full max-w-5xl mx-auto">
      {/* Overview Intro — full width */}
      <header className="space-y-4">
        <h1 className="text-4xl font-semibold tracking-tight">
          {intro.headline}
        </h1>
        <div className="prose max-w-none text-muted-foreground">
          <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
            {intro.body}
          </ReactMarkdown>
        </div>
        {intro.cta_label && intro.cta_url && (
          <Link
            href={intro.cta_url}
            className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            {intro.cta_label}
          </Link>
        )}
      </header>

      {/* Tile grid */}
      {visibleTiles.length > 0 && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {visibleTiles.map((tile) => (
            <Link
              key={tile.id}
              href={tile.href}
              className="block rounded-lg border border-border bg-card p-6 transition-colors hover:border-ring"
            >
              <h2 className="text-xl font-semibold">{tile.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground line-clamp-3">
                {tile.summary}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
