"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback } from "react";

interface Props {
  /** All unique tag slugs from loaded entries. */
  allTagSlugs: { slug: string; label: string }[];
  /** Currently selected tag slugs. */
  selected: Set<string>;
  /** Called when selection changes. */
  onChange: (slugs: Set<string>) => void;
}

export default function FilterChips({ allTagSlugs, selected, onChange }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const toggleTag = useCallback(
    (slug: string) => {
      const next = new Set(selected);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      onChange(next);

      const params = new URLSearchParams(searchParams.toString());
      if (next.size > 0) {
        params.set("tags", [...next].sort().join(","));
      } else {
        params.delete("tags");
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [selected, onChange, router, pathname, searchParams],
  );

  if (allTagSlugs.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by tag">
      {allTagSlugs.map(({ slug, label }) => {
        const active = selected.has(slug);
        return (
          <button
            key={slug}
            onClick={() => toggleTag(slug)}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors border ${
              active
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background text-muted-foreground border-border hover:border-ring"
            }`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
