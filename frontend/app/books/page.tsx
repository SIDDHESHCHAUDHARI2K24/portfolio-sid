import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import BooksClient from "./BooksClient";
import type { Metadata } from "next";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

export const metadata: Metadata = {
  title: "Bookshelf — Siddhesh Chaudhari",
  description: "Curated reading list — books with notes, ratings, and recommendations.",
  alternates: { canonical: "/books" },
  openGraph: {
    title: "Bookshelf — Siddhesh Chaudhari",
    description: "Curated reading list — books with notes, ratings, and recommendations.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function BooksPage() {
  const items: Item[] = await apiFetch<Item[]>("/collections", {
    tags: [CACHE_TAGS.collections],
    revalidate: 3600,
  });

  const books = items.filter((i) => i.kind === "book");

  const grouped: Record<string, Item[]> = {};
  for (const book of books) {
    const section = book.section ?? "Uncategorized";
    if (!grouped[section]) grouped[section] = [];
    grouped[section].push(book);
  }

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="w-full max-w-6xl mx-auto space-y-12">
        <h1 className="text-3xl font-semibold tracking-tight">Bookshelf</h1>
        <BooksClient grouped={grouped} />
      </div>
    </main>
  );
}
