"use client";

import { motion } from "framer-motion";

const WORDS = ["CURIOUS", "NERDY", "CREATIVE", "SCRAPPY", "AMBITIOUS", "BOLD"];
const START_DELAY = 200;
const WORD_INTERVAL = 450;

const ease: [number, number, number, number] = [0.16, 1, 0.3, 1];

interface IntroPlayerProps {
  wordIndex: number;
}

export default function IntroPlayer({ wordIndex }: IntroPlayerProps) {
  return (
    <div className="flex flex-col items-center gap-8">
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 px-4">
        {WORDS.map((word, i) => (
          <motion.span
            key={word}
            initial={false}
            animate={
              i <= wordIndex
                ? { opacity: 1, y: 0 }
                : { opacity: 0, y: 20 }
            }
            transition={{ duration: 0.35, ease }}
            className="font-display text-3xl md:text-5xl lg:text-6xl font-black uppercase tracking-tight text-text"
          >
            {word}
          </motion.span>
        ))}
      </div>
    </div>
  );
}

export { WORDS, START_DELAY, WORD_INTERVAL, ease };
