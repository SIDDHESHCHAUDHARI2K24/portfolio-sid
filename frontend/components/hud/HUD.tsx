"use client";

import { useCategory } from "@/components/CategoryProvider";
import { useEffect, useState } from "react";

const CATEGORIES = [
  { value: "recruiters", label: "Recruiters" },
  { value: "techies", label: "Techies" },
  { value: "investors", label: "Investors" },
  { value: "founders", label: "Founders" },
  { value: "personal", label: "Personal" },
];

export default function HUD() {
  const { category, setCategory, clear } = useCategory();
  const [scrollPct, setScrollPct] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement;
      const total = h.scrollHeight - h.clientHeight;
      setScrollPct(total > 0 ? Math.round((h.scrollTop / total) * 100) : 0);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-50">
      <div className="pointer-events-auto flex flex-col items-end gap-3">
        {open && (
          <div className="rounded-lg border border-border bg-card p-3 shadow-lg">
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => {
                    setCategory(value);
                    setOpen(false);
                  }}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                    category === value
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground hover:bg-border"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {category && (
              <button
                onClick={() => {
                  clear();
                  setOpen(false);
                }}
                className="mt-2 w-full rounded-md px-3 py-1 text-xs text-muted-foreground hover:bg-secondary"
              >
                Show everything
              </button>
            )}
            {/* Audio slot for Phase 2 */}
            <div id="hud-audio-slot" />
          </div>
        )}

        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground shadow-lg transition-colors hover:bg-secondary"
          aria-label="Toggle category selector"
        >
          <span>{scrollPct}%</span>
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary" />
          <span>{category ? category : "All"}</span>
        </button>
      </div>
    </div>
  );
}
