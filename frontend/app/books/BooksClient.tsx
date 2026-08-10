"use client";

import type { paths } from "@/src/api";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

const SECTION_CONFIG: Record<string, string> = {
  Tech: "Tech",
  Business: "Business",
  "Personal Development": "Personal Development",
  Uncategorized: "Uncategorized",
};

export default function BooksClient({ grouped }: { grouped: Record<string, Item[]> }) {
  const sections = Object.keys(grouped).sort(
    (a, b) => (Object.keys(SECTION_CONFIG).indexOf(a) || 999) - (Object.keys(SECTION_CONFIG).indexOf(b) || 999)
  );

  return (
    <div className="space-y-10">
      {sections.map((section) => (
        <section key={section}>
          <h2 className="text-xl font-semibold mb-4 border-b border-border pb-2">
            {SECTION_CONFIG[section] ?? section}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {grouped[section].map((book) => (
              <div key={book.id} className="flex flex-col items-center text-center group">
                <div className="relative aspect-[2/3] w-full overflow-hidden rounded-md border border-border bg-muted/30 mb-2">
                  {book.cover_key ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_R2_PUBLIC_URL}/${book.cover_key}`}
                      alt={book.title}
                      className="object-cover w-full h-full"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-2">
                      {book.title}
                    </div>
                  )}
                </div>
                <p className="text-sm font-medium leading-tight line-clamp-2">{book.title}</p>
                {book.creator && (
                  <p className="text-xs text-muted-foreground">{book.creator}</p>
                )}
                {book.status && (
                  <span className="text-xs text-muted-foreground mt-0.5 capitalize">
                    {book.status.replace(/_/g, " ")}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      ))}
      {sections.length === 0 && (
        <p className="text-center text-muted-foreground py-12">No books yet.</p>
      )}
    </div>
  );
}
