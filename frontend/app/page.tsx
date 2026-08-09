import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import TileGrid from "@/components/tiles/TileGrid";
import { buildTimelineTile } from "@/components/tiles/TimelineTile";
import type { Metadata } from "next";

type Intro = paths["/api/v1/overview"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Entry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = paths["/api/v1/relevance/map"]["get"]["responses"]["200"]["content"]["application/json"];

const THIRTY_MINUTES = 1800;

export default async function Home() {
  const [intros, entries, tagMap] = await Promise.all([
    apiFetch<Intro[]>("/overview", { tags: [CACHE_TAGS.overview], revalidate: THIRTY_MINUTES }),
    apiFetch<Entry[]>("/timeline", { tags: [CACHE_TAGS.timeline], revalidate: THIRTY_MINUTES }),
    apiFetch<TagMapResponse>("/relevance/map", { tags: [CACHE_TAGS.relevance], revalidate: THIRTY_MINUTES }),
  ]);

  const defaultIntro = intros.find((i) => i.audience === "default") ?? intros[0];

  const tiles = [buildTimelineTile(entries)];

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <TileGrid
        defaultIntro={defaultIntro}
        allIntros={intros}
        tiles={tiles}
      />
    </main>
  );
}
