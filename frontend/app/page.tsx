import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import TileGrid from "@/components/tiles/TileGrid";
import { buildTimelineTile } from "@/components/tiles/TimelineTile";
import { buildProjectsTile } from "@/components/tiles/ProjectsTile";
import { buildSkillsTile } from "@/components/tiles/SkillsTile";
import { buildCertificationsTile } from "@/components/tiles/CertificationsTile";
import { buildTechRabbitholeTile, buildHowIUseAiTile, buildVcForFoundersTile } from "@/components/tiles/PostsTile";
import { buildThesisTile } from "@/components/tiles/ThesisTile";
import { buildBooksTile } from "@/components/tiles/BooksTile";
import { buildAnimeMangaTile } from "@/components/tiles/AnimeMangaTile";
import { buildHobbiesTile, buildWorkViewsTile, buildInvestorIntroTile } from "@/components/tiles/ProseTiles";
import { buildContactTile } from "@/components/tiles/ContactTile";
import { buildDealflowTile } from "@/components/tiles/DealflowTile";
import { buildPersonJsonLd } from "@/lib/jsonld";
import type { Metadata } from "next";

type Intro = paths["/api/v1/overview"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Entry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ProjectItem = paths["/api/v1/projects"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Skill = paths["/api/v1/skills"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Cert = paths["/api/v1/certifications"]["get"]["responses"]["200"]["content"]["application/json"][number];
type PostItem = paths["/api/v1/posts"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ThesisItem = paths["/api/v1/thesis"]["get"]["responses"]["200"]["content"]["application/json"][number];
type CollectionItem = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ProsePage = paths["/api/v1/prose"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = paths["/api/v1/relevance/map"]["get"]["responses"]["200"]["content"]["application/json"];

const THIRTY_MINUTES = 1800;

export const metadata: Metadata = {
  title: "Siddhesh Chaudhari — Portfolio",
  description:
    "Audience-segmented portfolio — engineering, investing, and everything in between. Timeline, projects, skills, thesis, and more.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "Siddhesh Chaudhari — Portfolio",
    description:
      "Audience-segmented portfolio — engineering, investing, and everything in between.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function Home() {
  const [intros, entries, projects, skills, certs, posts, thesis, collections, prose] = await Promise.all([
    apiFetch<Intro[]>("/overview", { tags: [CACHE_TAGS.overview], revalidate: THIRTY_MINUTES }),
    apiFetch<Entry[]>("/timeline", { tags: [CACHE_TAGS.timeline], revalidate: THIRTY_MINUTES }),
    apiFetch<ProjectItem[]>("/projects", { tags: [CACHE_TAGS.projects], revalidate: THIRTY_MINUTES }),
    apiFetch<Skill[]>("/skills", { tags: [CACHE_TAGS.skills], revalidate: THIRTY_MINUTES }),
    apiFetch<Cert[]>("/certifications", { tags: [CACHE_TAGS.certifications], revalidate: THIRTY_MINUTES }),
    apiFetch<PostItem[]>("/posts", { tags: [CACHE_TAGS.posts], revalidate: THIRTY_MINUTES }),
    apiFetch<ThesisItem[]>("/thesis", { tags: [CACHE_TAGS.thesis], revalidate: THIRTY_MINUTES }),
    apiFetch<CollectionItem[]>("/collections", { tags: [CACHE_TAGS.collections], revalidate: THIRTY_MINUTES }),
    apiFetch<ProsePage[]>("/prose", { tags: [CACHE_TAGS.prose], revalidate: THIRTY_MINUTES }),
    apiFetch<TagMapResponse>("/relevance/map", { tags: [CACHE_TAGS.relevance], revalidate: THIRTY_MINUTES }),
  ]);

  const defaultIntro = intros.find((i) => i.audience === "default") ?? intros[0];

  const personJsonLd = buildPersonJsonLd(entries, skills, certs);

  const tiles = [
    buildContactTile(),
    buildTimelineTile(entries),
    buildProjectsTile(projects),
    buildSkillsTile(skills),
    buildTechRabbitholeTile(posts),
    buildHowIUseAiTile(posts),
    buildVcForFoundersTile(posts),
    buildThesisTile(thesis),
    buildCertificationsTile(certs),
    buildBooksTile(collections),
    buildAnimeMangaTile(collections),
    buildHobbiesTile(prose),
    buildWorkViewsTile(prose),
    buildInvestorIntroTile(prose),
    buildDealflowTile(),
  ];

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(personJsonLd) }}
      />
      <main className="flex flex-1 flex-col px-6 py-12">
        <TileGrid
          defaultIntro={defaultIntro}
          allIntros={intros}
          tiles={tiles}
        />
      </main>
    </>
  );
}
