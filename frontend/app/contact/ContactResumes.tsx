"use client";

import { useCategory } from "@/components/CategoryProvider";
import type { paths } from "@/src/api";

type Resume = paths["/api/v1/resumes"]["get"]["responses"]["200"]["content"]["application/json"][number];

/**
 * Audience → resume variant mapping (D2).
 * Default (no category / null) shows all 6; each audience sees a tailored subset.
 * Variant `ai_workflow` on the backend corresponds to spec's `ai_workflow_engineer`.
 */
export const ResumeAudienceMap: Record<string, string[]> = {
  recruiters: ["business", "generic", "product_engineer"],
  techies: ["ai_workflow_engineer", "ai_consultant", "product_engineer", "generic"],
  investors: ["vc", "business", "ai_consultant"],
  founders: ["vc", "product_engineer"],
  personal: ["generic"],
};

/** Alias-normalized check so backend `ai_workflow` matches spec `ai_workflow_engineer`. */
function variantMatches(variant: string, allowed: string[]): boolean {
  if (allowed.includes(variant)) return true;
  // backend stores `ai_workflow`, spec lists `ai_workflow_engineer`
  if (variant === "ai_workflow" && allowed.includes("ai_workflow_engineer")) return true;
  if (variant === "ai_workflow_engineer" && allowed.includes("ai_workflow")) return true;
  return false;
}

const VARIANT_LABELS: Record<string, string> = {
  business: "Business / TPM",
  generic: "Product Builder",
  vc: "Venture Capital",
  ai_consultant: "AI Consultant",
  ai_workflow: "AI Workflow Engineer",
  ai_workflow_engineer: "AI Workflow Engineer",
  product_engineer: "Product Engineer",
};

export default function ContactResumes({ resumes }: { resumes: Resume[] }) {
  const { category } = useCategory();
  const allowed = category ? ResumeAudienceMap[category] : null;

  const filtered = resumes.filter((r) => {
    if (!r.file_url) return false;
    if (!allowed) return true; // default → all
    return variantMatches(r.variant, allowed);
  });

  if (resumes.length === 0) return null;
  // Keep heading even when filtered to 0 so layout stays consistent; show empty hint.
  return (
    <section className="mb-10">
      <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
        Resumes
      </h2>
      {filtered.length > 0 ? (
        <div className="flex flex-wrap gap-4">
          {filtered.map((r) => (
            <a
              key={r.id}
              href={r.file_url!}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm hover:bg-accent transition-colors"
            >
              <span className="font-medium">{VARIANT_LABELS[r.variant] ?? r.variant}</span>
              <span className="text-muted-foreground">{r.label}</span>
            </a>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No resumes for this audience.</p>
      )}
    </section>
  );
}
