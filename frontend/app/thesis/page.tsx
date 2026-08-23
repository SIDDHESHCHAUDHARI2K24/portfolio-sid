import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import ThesisClient from "@/components/thesis/ThesisClient";

type ThesisItem = paths["/api/v1/thesis"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = { [key: string]: string[] };

export const metadata: Metadata = {
  title: "Investment Thesis — Siddhesh Chaudhari",
  description: "Thesis statements and perspectives on technology, markets, and emerging trends.",
  alternates: { canonical: "/thesis" },
  openGraph: {
    title: "Investment Thesis — Siddhesh Chaudhari",
    description: "Thesis statements and perspectives on technology, markets, and emerging trends.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function ThesisPage() {
  const [entries, tagMap] = await Promise.all([
    apiFetch<ThesisItem[]>("/thesis", {
      tags: [CACHE_TAGS.thesis],
      revalidate: 3600,
    }),
    apiFetch<TagMapResponse>("/relevance/map", {
      tags: [CACHE_TAGS.relevance],
      revalidate: 3600,
    }),
  ]);

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <ThesisClient entries={entries} tagMap={tagMap} />
    </main>
  );
}
