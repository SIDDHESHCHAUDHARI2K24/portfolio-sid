import type { paths } from "@/src/api";

type TimelineEntry = paths["/api/v1/timeline"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Skill = paths["/api/v1/skills"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Cert = paths["/api/v1/certifications"]["get"]["responses"]["200"]["content"]["application/json"][number];
type Project = paths["/api/v1/projects"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ProsePage = paths["/api/v1/prose/slug/{slug}"]["get"]["responses"]["200"]["content"]["application/json"];

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";
const LINKEDIN_URL = "https://www.linkedin.com/in/siddheshchaudhari/";
const GITHUB_URL = "https://github.com/siddhesh";
const EMAIL = "siddhesh@example.com";
const PERSON_NAME = "Siddhesh Chaudhari";

export function buildPersonJsonLd(
  timeline: TimelineEntry[],
  skills: Skill[],
  certs: Cert[],
) {
  const education = timeline
    .filter((e) => e.kind === "education")
    .map((e) => ({
      "@type": "EducationalOrganization" as const,
      name: e.organisation,
    }));

  const currentExperience = timeline.filter(
    (e) => e.kind === "experience" && !e.end_date,
  );

  const worksFor = currentExperience.map((e) => ({
    "@type": "Organization" as const,
    name: e.organisation,
    description: e.title,
  }));

  return {
    "@context": "https://schema.org",
    "@type": "Person",
    name: PERSON_NAME,
    url: BASE_URL,
    email: EMAIL,
    sameAs: [LINKEDIN_URL, GITHUB_URL],
    alumniOf: education.length > 0 ? education : undefined,
    worksFor: worksFor.length > 0 ? worksFor : undefined,
    knowsAbout: skills.length > 0 ? skills.map((s) => s.name) : undefined,
    hasCredential: certs.length > 0 ? certs.map((c) => {
      const cred: Record<string, unknown> = {
        "@type": "EducationalOccupationalCredential",
        name: c.title,
        credentialCategory: c.kind,
      };
      if (c.issuer) cred.recognizedBy = { "@type": "Organization", name: c.issuer };
      if (c.credential_url) cred.url = c.credential_url;
      return cred;
    }) : undefined,
  };
}

export function buildCreativeWorkJsonLd(project: Project) {
  return {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    name: project.title,
    description: project.summary ?? project.description ?? undefined,
    url: `${BASE_URL}/projects/${project.slug}`,
    dateCreated: project.created_at,
    dateModified: project.updated_at,
    author: {
      "@type": "Person",
      name: PERSON_NAME,
      url: BASE_URL,
    },
  };
}

export function buildTimelineEntryJsonLd(entry: TimelineEntry) {
  return {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    name: `${entry.title} at ${entry.organisation}`,
    description: entry.summary ?? undefined,
    url: `${BASE_URL}/timeline/${entry.id}`,
    dateCreated: entry.created_at,
    dateModified: entry.updated_at,
    author: {
      "@type": "Person",
      name: PERSON_NAME,
      url: BASE_URL,
    },
    keywords: entry.topic_tags?.map((t) => t.label).join(", ") || undefined,
  };
}

export function buildBreadcrumbJsonLd(items: { name: string; url: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: item.url.startsWith("http") ? item.url : `${BASE_URL}${item.url}`,
    })),
  };
}

export function buildBlogPostingJsonLd(page: ProsePage) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: page.title,
    url: `${BASE_URL}/${page.slug}`,
    datePublished: page.created_at,
    dateModified: page.updated_at,
    author: {
      "@type": "Person",
      name: PERSON_NAME,
      url: BASE_URL,
    },
  };
}
