"use client";

import { useCategory } from "@/components/CategoryProvider";
import { useAudio } from "@/components/audio";
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
          <div className="rounded-lg border border-border bg-card p-3 shadow-lg min-w-44">
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

            <AudioControls />
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

function AudioControls() {
  const { track, playing, volume, toggle, setVolume, nextTrack, prevTrack } =
    useAudio();

  return (
    <div className="mt-3 pt-3 border-t border-border">
      <div className="flex items-center gap-2 mb-2">
        <button
          onClick={prevTrack}
          className="p-1 text-muted-foreground hover:text-text transition-colors"
          aria-label="Previous track"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
          </svg>
        </button>
        <button
          onClick={toggle}
          className="p-1 text-muted-foreground hover:text-text transition-colors"
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 4h4v16H6zm8 0h4v16h-4z" />
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        <button
          onClick={nextTrack}
          className="p-1 text-muted-foreground hover:text-text transition-colors"
          aria-label="Next track"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        </button>
        <span className="text-xs text-muted-foreground flex-1 truncate ml-1">
          {track.label}
        </span>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={volume}
        onChange={(e) => setVolume(parseFloat(e.target.value))}
        className="w-full h-1 appearance-none bg-border rounded-full outline-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-relevant
          [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full
          [&::-moz-range-thumb]:bg-relevant [&::-moz-range-thumb]:border-0"
        aria-label="Volume"
      />
    </div>
  );
}
