import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import PostList from "@/features/posts/PostList";

type PostItem = paths["/api/v1/posts"]["get"]["responses"]["200"]["content"]["application/json"][number];
type TagMapResponse = { [key: string]: string[] };

export const metadata: Metadata = {
  title: "Tech Rabbithole — Siddhesh Chaudhari",
  alternates: { canonical: "/tech-rabbithole" },
};

export default async function TechRabbitholePage() {
  const [posts, tagMap] = await Promise.all([
    apiFetch<PostItem[]>("/posts?collection=tech_rabbithole", {
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
        heading="Tech Rabbithole"
        description="Deep dives into engineering problems, architecture decisions, and what broke in production."
      />
    </main>
  );
}
