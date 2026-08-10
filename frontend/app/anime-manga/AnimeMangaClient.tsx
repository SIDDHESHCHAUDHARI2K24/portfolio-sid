"use client";

import type { paths } from "@/src/api";

type Item = paths["/api/v1/collections"]["get"]["responses"]["200"]["content"]["application/json"][number];

export default function AnimeMangaClient({ anime, manhwa }: { anime: Item[]; manhwa: Item[] }) {
  return (
    <div className="space-y-10">
      {anime.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4 border-b border-border pb-2">Anime</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {anime.map((item) => (
              <div key={item.id} className="flex flex-col items-center text-center group">
                <div className="relative aspect-[2/3] w-full overflow-hidden rounded-md border border-border bg-muted/30 mb-2">
                  {item.cover_key ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_R2_PUBLIC_URL}/${item.cover_key}`}
                      alt={item.title}
                      className="object-cover w-full h-full"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-2">
                      {item.title}
                    </div>
                  )}
                </div>
                <p className="text-sm font-medium leading-tight line-clamp-2">{item.title}</p>
                {item.creator && (
                  <p className="text-xs text-muted-foreground">{item.creator}</p>
                )}
                {item.status && (
                  <span className="text-xs text-muted-foreground mt-0.5 capitalize">
                    {item.status.replace(/_/g, " ")}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {manhwa.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4 border-b border-border pb-2">Manhwa</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {manhwa.map((item) => (
              <div key={item.id} className="flex flex-col items-center text-center group">
                <div className="relative aspect-[2/3] w-full overflow-hidden rounded-md border border-border bg-muted/30 mb-2">
                  {item.cover_key ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_R2_PUBLIC_URL}/${item.cover_key}`}
                      alt={item.title}
                      className="object-cover w-full h-full"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-2">
                      {item.title}
                    </div>
                  )}
                </div>
                <p className="text-sm font-medium leading-tight line-clamp-2">{item.title}</p>
                {item.creator && (
                  <p className="text-xs text-muted-foreground">{item.creator}</p>
                )}
                {item.status && (
                  <span className="text-xs text-muted-foreground mt-0.5 capitalize">
                    {item.status.replace(/_/g, " ")}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {anime.length === 0 && manhwa.length === 0 && (
        <p className="text-center text-muted-foreground py-12">No anime or manhwa yet.</p>
      )}
    </div>
  );
}
