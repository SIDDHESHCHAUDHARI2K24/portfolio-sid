import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import ContactForm from "@/features/forms/ContactForm";
import ContactResumes from "./ContactResumes";
import type { Metadata } from "next";

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

type Resume = paths["/api/v1/resumes"]["get"]["responses"]["200"]["content"]["application/json"][number];

const EMAIL = "siddhesh@example.com";
const LINKEDIN_URL = "https://www.linkedin.com/in/siddheshchaudhari/";
const CAL_URL = "https://cal.com/siddhesh";
const GITHUB_URL = "https://github.com/siddhesh";
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: "Contact — Siddhesh Chaudhari",
  description: "Get in touch — email, LinkedIn, booking a call, and resume downloads.",
  alternates: { canonical: "/contact" },
  openGraph: {
    title: "Contact — Siddhesh Chaudhari",
    description: "Get in touch — email, LinkedIn, booking a call, and resume downloads.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default async function ContactPage() {
  let resumes: Resume[] = [];
  try {
    resumes = await apiFetch<Resume[]>("/resumes", {
      tags: [CACHE_TAGS.resumes],
      revalidate: 3600,
    });
  } catch {
    // if API unavailable, page still renders
  }

  // 6 canonical variants per backend/scripts/resume_canon.json:resumes
  const VARIANT_ORDER = [
    "business",
    "generic",
    "vc",
    "ai_consultant",
    "ai_workflow",
    "product_engineer",
  ];
  const sortedResumes = [...resumes].sort(
    (a, b) => VARIANT_ORDER.indexOf(a.variant) - VARIANT_ORDER.indexOf(b.variant),
  );

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Person",
    name: "Siddhesh Chaudhari",
    email: EMAIL,
    sameAs: [LINKEDIN_URL, GITHUB_URL],
    url: `${BASE_URL}/contact`,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <main className="flex flex-1 flex-col px-6 py-12 max-w-2xl mx-auto w-full">
        <h1 className="text-3xl font-semibold mb-8">Contact</h1>

        <section className="mb-10 space-y-4">
          <div>
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Email
            </h2>
            <span className="text-lg">{EMAIL}</span>
          </div>

          <div>
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              LinkedIn
            </h2>
            <a
              href={LINKEDIN_URL}
              rel="noopener noreferrer"
              target="_blank"
              className="text-lg underline underline-offset-2 hover:text-primary transition-colors"
            >
              linkedin.com/in/siddheshchaudhari
            </a>
          </div>

          <div>
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Book a call
            </h2>
            <a
              href={CAL_URL}
              rel="noopener noreferrer"
              target="_blank"
              className="text-lg underline underline-offset-2 hover:text-primary transition-colors"
            >
              {CAL_URL}
            </a>
          </div>
        </section>

          <ContactResumes resumes={sortedResumes} />

        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-4">Send a message</h2>
          <ContactForm consentText="I consent to having my data stored for the purpose of this contact submission." />
        </section>
      </main>
    </>
  );
}
