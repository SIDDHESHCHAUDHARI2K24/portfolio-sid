import type { Metadata } from "next";

const isIndexable = process.env.NEXT_PUBLIC_INDEXABLE === "true";

export function buildRootMetadata(): Metadata {
  return {
    title: "Siddhesh Chaudhari",
    description:
      "Siddhesh Chaudhari — portfolio. Audience-segmented views over one body of work.",
    robots: isIndexable
      ? { index: true, follow: true }
      : { index: false, follow: false },
  };
}
