import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import TimelineClient from "@/components/timeline/TimelineClient";
import type { Metadata } from "next";
import { Suspense } from "react";

type Entry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = paths["/api/v1/relevance/map"]["get"]["responses"]["200"]["content"]["application/json"];

export const metadata: Metadata = {
  title: "Timeline — Siddhesh Chaudhari",
  description: "Career timeline — education, experience, and professional milestones.",
  alternates: { canonical: "/timeline" },
  openGraph: {
    title: "Timeline — Siddhesh Chaudhari",
    description: "Career timeline — education, experience, and professional milestones.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function TimelinePage() {
  const [entries, tagMap] = await Promise.all([
    apiFetch<Entry[]>("/timeline", { tags: [CACHE_TAGS.timeline], revalidate: 3600 }),
    apiFetch<TagMapResponse>("/relevance/map", { tags: [CACHE_TAGS.relevance], revalidate: 3600 }),
  ]);

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <Suspense>
        <TimelineClient entries={entries} tagMap={tagMap} />
      </Suspense>
    </main>
  );
}
