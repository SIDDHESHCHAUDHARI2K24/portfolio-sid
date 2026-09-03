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
type Contact = paths["/api/v1/contact"]["get"]["responses"]["200"]["content"]["application/json"];

const FALLBACK_CONTACT: Contact = {
  email: "siddhesh@example.com",
  linkedin_url: "https://www.linkedin.com/in/siddheshchaudhari/",
  linkedin_label: "linkedin.com/in/siddheshchaudhari",
  cal_url: "https://cal.com/siddhesh",
  cal_label: "https://cal.com/siddhesh",
  github_url: "https://github.com/siddhesh",
  consent_text: "I consent to having my data stored for the purpose of this contact submission.",
};

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

  let contact: Contact = FALLBACK_CONTACT;
  try {
    contact = await apiFetch<Contact>("/contact", {
      tags: [CACHE_TAGS.contact],
      revalidate: 3600,
    });
  } catch {
    // seeded row missing (e.g. build-time against an older backend) — render defaults
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
    email: contact.email,
    sameAs: [contact.linkedin_url, contact.github_url],
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
            <span className="text-lg">{contact.email}</span>
          </div>

          <div>
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              LinkedIn
            </h2>
            <a
              href={contact.linkedin_url}
              rel="noopener noreferrer"
              target="_blank"
              className="text-lg underline underline-offset-2 hover:text-primary transition-colors"
            >
              {contact.linkedin_label}
            </a>
          </div>

          <div>
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Book a call
            </h2>
            <a
              href={contact.cal_url}
              rel="noopener noreferrer"
              target="_blank"
              className="text-lg underline underline-offset-2 hover:text-primary transition-colors"
            >
              {contact.cal_label}
            </a>
          </div>
        </section>

          <ContactResumes resumes={sortedResumes} />

        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-4">Send a message</h2>
          <ContactForm consentText={contact.consent_text} />
        </section>
      </main>
    </>
  );
}
