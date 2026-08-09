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
import { CATEGORY_TILES } from "./CategorySelector";

export default function IntroOverlay() {
  const { setCategory, clear } = useCategory();
  const reducedMotion = useReducedMotion();
  const [phase, setPhase] = useState<"intro" | "selector" | "done">(() => {
    if (typeof window === "undefined") return "intro";
    if (sessionStorage.getItem("intro-seen") === "true") return "done";
    return "intro";
  });
  const [wordIndex, setWordIndex] = useState(-1);
  const [counter, setCounter] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const seen = sessionStorage.getItem("intro-seen") === "true";
    if (reducedMotion || seen) {
      setPhase("done");
      return;
    }
  }, [reducedMotion]);

  useEffect(() => {
    if (phase !== "intro") return;

    const morphDelay = 250;
    const totalDuration =
      START_DELAY + (WORDS.length - 1) * WORD_INTERVAL + morphDelay + 300;

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
    if (phase === "intro") setPhase("selector");
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
      if (tileId === "all") {
        clear();
      } else {
        setCategory(tileId);
      }
      sessionStorage.setItem("intro-seen", "true");
      setPhase("done");
    },
    [setCategory, clear]
  );

  if (phase === "done") return null;

  const showIntro = phase === "intro";

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-ink overflow-hidden"
      onClick={showIntro ? skip : undefined}
      exit={{ opacity: 0 }}
      key="intro-overlay"
    >
      <AnimatePresence mode="wait">
        {showIntro && (
          <motion.div
            key="intro-content"
            className="flex flex-col items-center"
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
            <h2 className="font-display text-2xl md:text-3xl font-black uppercase tracking-tight text-text">
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
            ? "mt-8 grid grid-cols-3 grid-rows-2 gap-2"
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
                ? `w-6 h-6 rounded ${
                    i <= wordIndex ? "bg-relevant" : "bg-surface"
                  }`
                : "rounded border border-border bg-card hover:bg-surface-raised cursor-pointer p-4 md:p-6"
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
                <div className="font-display text-sm md:text-lg font-black uppercase tracking-tight text-text">
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
  );
}
