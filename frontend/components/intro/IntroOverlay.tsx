"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useCategory } from "@/components/CategoryProvider";
import IntroPlayer, {
  WORDS,
  START_DELAY,
  WORD_INTERVAL,
  ease,
} from "./IntroPlayer";

export interface CategoryTile {
  id: string;
  label: string;
  sub: string;
}

export const CATEGORY_TILES: CategoryTile[] = [
  { id: "recruiters", label: "Recruiters", sub: "Hire me" },
  { id: "techies", label: "Techies", sub: "Build with me" },
  { id: "investors", label: "Investors", sub: "Back me" },
  { id: "founders", label: "Founders", sub: "Partner with me" },
  { id: "personal", label: "Personal", sub: "Know me" },
];

const MORPH_SETTLE_MS = 300; // accounts for shared layout morph animation settle time

export default function IntroOverlay() {
  const { setCategory } = useCategory();
  const reducedMotion = useReducedMotion();
  // null = unknown until mounted. Never read sessionStorage during render:
  // an SSR/client divergence here makes React abandon the subtree, leaving
  // the SSR overlay orphaned on top of the page (observed in e2e).
  const [phase, setPhase] = useState<"intro" | "selector" | "done" | null>(
    null
  );
  const [wordIndex, setWordIndex] = useState(-1);
  const [counter, setCounter] = useState(0);

  useEffect(() => {
    const seen = sessionStorage.getItem("intro-seen") === "true";
    if (seen || reducedMotion) setPhase("done");
    else setPhase("intro");
  }, [reducedMotion]);

  useEffect(() => {
    if (phase !== "intro") return;

    const morphDelay = 250;
    const totalDuration =
      START_DELAY + (WORDS.length - 1) * WORD_INTERVAL + morphDelay + MORPH_SETTLE_MS;

    const counterStart = performance.now();
    let frame: number;
    const tick = () => {
      const pct = Math.min(
        (performance.now() - counterStart) / totalDuration,
        1
      );
      setCounter(Math.round(pct * 100));
      if (pct < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    const timers: NodeJS.Timeout[] = [];
    timers.push(setTimeout(() => setWordIndex(0), START_DELAY));
    for (let i = 1; i < WORDS.length; i++) {
      timers.push(
        setTimeout(
          () => setWordIndex(i),
          START_DELAY + i * WORD_INTERVAL
        )
      );
    }

    const morphTime =
      START_DELAY + (WORDS.length - 1) * WORD_INTERVAL + morphDelay;
    timers.push(setTimeout(() => setPhase("selector"), morphTime));

    return () => {
      cancelAnimationFrame(frame);
      timers.forEach(clearTimeout);
    };
  }, [phase]);

  const skip = useCallback(() => {
    if (phase === "intro") {
      sessionStorage.setItem("intro-seen", "true");
      setPhase("selector");
    }
  }, [phase]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") skip();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [skip]);

  const handleSelect = useCallback(
    (tileId: string) => {
      setCategory(tileId);
      sessionStorage.setItem("intro-seen", "true");
      setPhase("done");
    },
    [setCategory]
  );

  const showOverlay = phase === "intro" || phase === "selector";
  const showIntro = phase === "intro";

  // Opaque cover while the real phase resolves post-mount. Same output on
  // server and client, so hydration adopts it cleanly; prevents a flash of
  // the page beneath before sessionStorage is known.
  if (phase === null) {
    return <div className="fixed inset-0 z-[100] bg-background" aria-hidden="true" />;
  }

  return (
    <AnimatePresence>
      {showOverlay && (
        <motion.div
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background overflow-hidden"
          onClick={showIntro ? skip : undefined}
          onKeyDown={(e) => {
            if (showIntro && (e.key === 'Enter' || e.key === 'Escape')) {
              skip();
            }
          }}
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          key="intro-overlay"
          role="button"
          tabIndex={0}
        >
          <AnimatePresence mode="wait">
            {showIntro && (
              <motion.div
                key="intro-content"
                className="flex flex-col items-center justify-center"
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <IntroPlayer wordIndex={wordIndex} />
                <motion.div
                  className="mt-8 font-mono text-xs text-muted-foreground tabular-nums"
                  exit={{ opacity: 0 }}
                >
                  {counter}%
                </motion.div>
              </motion.div>
            )}
            {!showIntro && (
              <motion.div
                key="selector-header"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="flex flex-col items-center mb-8"
              >
                <h2 className="font-display text-2xl md:text-3xl font-black uppercase tracking-tight text-foreground">
                  Who are you?
                </h2>
                <p className="text-muted-foreground text-sm mt-2">
                  I tailor this site to what you need. Choose your lens.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div
            layout
            className={
              showIntro
                ? "mt-8 grid grid-cols-2 grid-rows-3 gap-2"
                : "grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4 max-w-xl w-full px-6 md:px-0"
            }
            transition={{ duration: 0.5, ease }}
          >
            {CATEGORY_TILES.map((tile, i) => (
              <motion.div
                key={tile.id}
                layoutId={`square-${i}`}
                className={
                  showIntro
                    ? `w-8 h-8 rounded ${
                        i <= wordIndex ? "bg-relevant" : "bg-card"
                      }`
                    : "rounded border border-border bg-card hover:bg-secondary cursor-pointer p-4 md:p-6"
                }
                transition={{ duration: 0.5, ease }}
                onClick={(e) => {
                  if (!showIntro) {
                    e.stopPropagation();
                    handleSelect(tile.id);
                  }
                }}
              >
                {!showIntro && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2, delay: 0.15 }}
                  >
                    <div className="font-display text-sm md:text-lg font-black uppercase tracking-tight text-foreground">
                      {tile.label}
                    </div>
                    <div className="text-muted-foreground text-xs md:text-sm mt-1">
                      {tile.sub}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
