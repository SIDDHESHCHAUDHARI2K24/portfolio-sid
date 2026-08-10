import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import SkillsClient from "@/components/skills/SkillsClient";

type Skill = paths["/api/v1/skills"]["get"]["responses"]["200"]["content"]["application/json"][number];

const SECTION_CONFIG: Record<string, { label: string; showPerSkillIcon: boolean }> = {
  languages: { label: "Languages", showPerSkillIcon: true },
  tools: { label: "Tools & Platforms", showPerSkillIcon: true },
  frameworks: { label: "Frameworks & Libraries", showPerSkillIcon: true },
  ai: { label: "AI & Data", showPerSkillIcon: true },
  business: { label: "Business & Strategy", showPerSkillIcon: false },
};

export const metadata: Metadata = {
  title: "Skills — Siddhesh Chaudhari",
  alternates: { canonical: "/skills" },
};

export default async function SkillsPage() {
  const skills: Skill[] = await apiFetch<Skill[]>("/skills", {
    tags: [CACHE_TAGS.skills],
    revalidate: 3600,
  });

  const grouped: Record<string, Record<string, Skill[]>> = {};
  for (const skill of skills) {
    const section = skill.section;
    const subsection = skill.subsection ?? "__root__";
    if (!grouped[section]) grouped[section] = {};
    if (!grouped[section][subsection]) grouped[section][subsection] = [];
    grouped[section][subsection].push(skill);
  }

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="w-full max-w-3xl mx-auto space-y-12">
        <h1 className="text-3xl font-semibold tracking-tight">Skills</h1>
        <SkillsClient grouped={grouped} config={SECTION_CONFIG} />
      </div>
    </main>
  );
}
