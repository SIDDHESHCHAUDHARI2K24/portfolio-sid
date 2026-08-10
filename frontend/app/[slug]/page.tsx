import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import ProseClient from "./ProseClient";
import type { Metadata } from "next";

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
    return {
      title: `${page.title} — Siddhesh Chaudhari`,
      alternates: { canonical: `/${slug}` },
    };
  } catch {
    return { title: "Page Not Found — Siddhesh Chaudhari" };
  }
}

export default async function ProsePageRoute({ params }: Props) {
  const { slug } = await params;
  try {
    const page: ProsePage = await apiFetch<ProsePage>(`/prose/slug/${slug}`, {
      tags: [CACHE_TAGS.prose],
      revalidate: 3600,
    });
    return (
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="w-full max-w-[68ch] mx-auto">
          <h1 className="text-3xl font-semibold tracking-tight mb-8">{page.title}</h1>
          <ProseClient body={page.body} ctaLabel={page.cta_label} ctaUrl={page.cta_url} />
        </div>
      </main>
    );
  } catch {
    return (
      <main className="flex flex-1 flex-col px-6 py-12">
        <div className="w-full max-w-[68ch] mx-auto">
          <h1 className="text-3xl font-semibold tracking-tight">Not Found</h1>
          <p className="text-muted-foreground mt-4">This page does not exist.</p>
        </div>
      </main>
    );
  }
}
