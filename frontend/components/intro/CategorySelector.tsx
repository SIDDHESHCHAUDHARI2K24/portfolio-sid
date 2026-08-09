"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { useCategory } from "@/components/CategoryProvider";

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
  { id: "all", label: "Show everything", sub: "See it all" },
];

interface CategorySelectorProps {
  onSelect: () => void;
}

export default function CategorySelector({ onSelect }: CategorySelectorProps) {
  const { setCategory, clear } = useCategory();

  const handleSelect = useCallback(
    (tile: CategoryTile) => {
      if (tile.id === "all") {
        clear();
      } else {
        setCategory(tile.id);
      }
      onSelect();
    },
    [setCategory, clear, onSelect]
  );

  return (
    <div className="flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="mb-8 text-center"
      >
        <h2 className="font-display text-2xl md:text-3xl font-black uppercase tracking-tight text-text">
          Who are you?
        </h2>
        <p className="text-muted-foreground text-sm mt-2">
          I tailor this site to what you need. Choose your lens.
        </p>
      </motion.div>
    </div>
  );
}
