import { apiFetch, isNotFoundError } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import { buildArticleJsonLd } from "@/lib/jsonld";
import Markdown from "@/components/Markdown";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

type PostList = paths["/api/v1/posts"]["get"]["responses"]["200"]["content"]["application/json"];
type PostDetail = paths["/api/v1/posts/slug/{slug}"]["get"]["responses"]["200"]["content"]["application/json"];

// Static + ISR (conventions invariant 3): no cookies()/headers() in this route.
export const revalidate = 3600;

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams(): Promise<{ slug: string }[]> {
  try {
    const posts = await apiFetch<PostList>("/posts", { tags: [CACHE_TAGS.posts] });
    return posts
      .filter((p) => p.platform === "internal" && p.slug)
      .map((p) => ({ slug: p.slug as string }));
  } catch {
    // API unreachable at build time: render on demand, then cache (ISR).
    return [];
  }
}

function fetchPost(slug: string) {
  return apiFetch<PostDetail>(`/posts/slug/${encodeURIComponent(slug)}`, {
    tags: [CACHE_TAGS.posts],
    revalidate,
  });
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const post = await fetchPost(slug);
    const description = post.summary ?? post.body.replace(/[#*_`>\[\]]/g, "").slice(0, 160);
    return {
      title: `${post.title} — Siddhesh Chaudhari`,
      description,
      alternates: { canonical: `/writing/${slug}` },
      openGraph: {
        title: `${post.title} — Siddhesh Chaudhari`,
        description,
        type: "article",
      },
      twitter: { card: "summary" },
    };
  } catch (err) {
    // Only a definitive 404 is "not found"; anything else rethrows so ISR keeps the stale page.
    if (!isNotFoundError(err)) throw err;
    return { title: "Article Not Found — Siddhesh Chaudhari" };
  }
}

export default async function WritingPage({ params }: Props) {
  const { slug } = await params;
  let post: PostDetail;
  try {
    post = await fetchPost(slug);
  } catch (err) {
    // 404 -> not-found page. Anything else (5xx, timeout, network) rethrows so ISR
    // keeps serving the last good page instead of caching a 404.
    if (isNotFoundError(err)) notFound();
    throw err;
  }

  const date = post.published_date ?? post.created_at;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildArticleJsonLd(post)).replace(/</g, "\\u003c"),
        }}
      />
      <main className="flex flex-1 flex-col px-6 py-12">
        <article className="w-full max-w-[68ch] mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">{post.title}</h1>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <time dateTime={date}>
                {new Date(date).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </time>
              {post.topic_tags.map((t) => (
                <span
                  key={t.slug}
                  className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                >
                  {t.label}
                </span>
              ))}
            </div>
          </header>
          <Markdown body={post.body} />
        </article>
      </main>
    </>
  );
}
