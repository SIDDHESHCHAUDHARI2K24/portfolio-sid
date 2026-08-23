import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import ProseClient from "./ProseClient";
import { buildBlogPostingJsonLd } from "@/lib/jsonld";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

type ProsePage = paths["/api/v1/prose/slug/{slug}"]["get"]["responses"]["200"]["content"]["application/json"];

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const page: ProsePage = await apiFetch<ProsePage>(`/prose/slug/${slug}`, {
      tags: [CACHE_TAGS.prose],
      revalidate: 3600,
    });
    const plainDescription = page.body.replace(/<[^>]*>/g, "").slice(0, 160);
    return {
      title: `${page.title} — Siddhesh Chaudhari`,
      description: plainDescription,
      alternates: { canonical: `/${slug}` },
      openGraph: {
        title: `${page.title} — Siddhesh Chaudhari`,
        description: plainDescription,
        type: "article",
      },
      twitter: {
        card: "summary",
      },
    };
  } catch {
    return { title: "Page Not Found — Siddhesh Chaudhari" };
  }
}

export default async function ProsePageRoute({ params }: Props) {
  const { slug } = await params;
  let page: ProsePage;
  try {
    page = await apiFetch<ProsePage>(`/prose/slug/${slug}`, {
      tags: [CACHE_TAGS.prose],
      revalidate: 3600,
    });
  } catch {
    notFound();
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildBlogPostingJsonLd(page)),
        }}
      />
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="w-full max-w-[68ch] mx-auto">
          <h1 className="text-3xl font-semibold tracking-tight mb-8">{page.title}</h1>
          <ProseClient body={page.body} ctaLabel={page.cta_label} ctaUrl={page.cta_url} />
        </div>
      </main>
    </>
  );
}
