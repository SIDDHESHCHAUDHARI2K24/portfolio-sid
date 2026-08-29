"use client";

import type { paths } from "@/src/api";
import SkillIcon from "@/components/skills/SkillIcon";

type Skill = paths["/api/v1/skills"]["get"]["responses"]["200"]["content"]["application/json"][number];
type GroupedSkills = Record<string, Record<string, Skill[]>>;
type SectionConfig = Record<string, { label: string; showPerSkillIcon: boolean }>;

const TECH_SECTIONS = ["languages", "tools", "frameworks", "ai"];
const SECTION_ORDER = [...TECH_SECTIONS, "business"];

interface Props {
  grouped: GroupedSkills;
  config: SectionConfig;
}

export default function SkillsClient({ grouped, config }: Props) {
  return (
    <div className="space-y-12">
      {SECTION_ORDER.map((sectionKey) => {
        const subsections = grouped[sectionKey];
        if (!subsections) return null;

        const cfg = config[sectionKey];
        if (!cfg) return null;

        const isBusiness = sectionKey === "business";

        return (
          <section key={sectionKey}>
            <h2 className="text-xl font-semibold mb-4">{cfg.label}</h2>

            {Object.entries(subsections).map(([subsection, skills]) => (
              <div key={subsection} className="mb-6">
                {subsection !== "__root__" && (
                  <div className="flex items-center gap-2 mb-3">
                    {isBusiness && skills[0] && (
                      <SkillIcon
                        slug={skills[0].icon_slug}
                        iconUrl={skills[0].icon_url ?? null}
                        label={subsection}
                        size={20}
                      />
                    )}
                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                      {subsection}
                    </h3>
                  </div>
                )}

                <div
                  className={
                    isBusiness
                      ? "flex flex-wrap gap-2"
                      : "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2"
                  }
                >
                  {skills.map((skill) => (
                    <div
                      key={skill.id}
                      className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 transition-colors hover:bg-accent/50"
                    >
                      {cfg.showPerSkillIcon && (
                        <SkillIcon
                          slug={skill.icon_slug}
                          iconUrl={skill.icon_url ?? null}
                          label={skill.name}
                          size={20}
                        />
                      )}
                      {isBusiness && (
                        <span className="rounded-full bg-muted w-2 h-2 shrink-0" />
                      )}
                      <span className="text-sm">{skill.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}
