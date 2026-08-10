import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import AnimeMangaClient from "./AnimeMangaClient";
import type { Metadata } from "next";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

export const metadata: Metadata = {
  title: "Anime & Manhwa — Siddhesh Chaudhari",
  alternates: { canonical: "/anime-manga" },
};

export default async function AnimeMangaPage() {
  const items: Item[] = await apiFetch<Item[]>("/collections", {
    tags: [CACHE_TAGS.collections],
    revalidate: 3600,
  });

  const anime = items.filter((i) => i.kind === "anime");
  const manhwa = items.filter((i) => i.kind === "manhwa");

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="w-full max-w-6xl mx-auto space-y-12">
        <h1 className="text-3xl font-semibold tracking-tight">Anime & Manhwa</h1>
        <AnimeMangaClient anime={anime} manhwa={manhwa} />
      </div>
    </main>
  );
}
