import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import PostList from "@/features/posts/PostList";

type PostItem = paths["/api/v1/posts"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = { [key: string]: string[] };

export const metadata: Metadata = {
  title: "VC for Founders — Siddhesh Chaudhari",
  description: "What I look for as an investor and how I think about early-stage startups.",
  alternates: { canonical: "/vc-for-founders" },
  openGraph: {
    title: "VC for Founders — Siddhesh Chaudhari",
    description: "What I look for as an investor and how I think about early-stage startups.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function VcForFoundersPage() {
  const [posts, tagMap] = await Promise.all([
    apiFetch<PostItem[]>("/posts?collection=vc_for_founders", {
      tags: [CACHE_TAGS.posts],
      revalidate: 3600,
    }),
    apiFetch<TagMapResponse>("/relevance/map", {
      tags: [CACHE_TAGS.relevance],
      revalidate: 3600,
    }),
  ]);

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <PostList
        posts={posts}
        tagMap={tagMap}
        heading="VC for Founders"
        description="What I look for as an investor and how I think about early-stage startups."
      />
    </main>
  );
}
