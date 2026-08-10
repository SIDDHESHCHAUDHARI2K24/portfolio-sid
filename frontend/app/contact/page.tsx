import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import ContactForm from "@/features/forms/ContactForm";
import type { Metadata } from "next";

type Resume = paths["/api/v1/resumes"]["get"]["responses"]["200"]["content"]["application/json"][number];

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "1x00000000000000000000AA";
const EMAIL = "siddhesh@example.com";
const LINKEDIN_URL = "https://www.linkedin.com/in/siddheshchaudhari/";
const CAL_URL = "https://cal.com/siddhesh";
const GITHUB_URL = "https://github.com/siddhesh";
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: "Contact — Siddhesh Chaudhari",
  alternates: { canonical: "/contact" },
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

  const techResume = resumes.find((r) => r.variant === "tech");
  const businessResume = resumes.find((r) => r.variant === "business");

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

        {resumes.length > 0 && (
          <section className="mb-10">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Resumes
            </h2>
            <div className="flex flex-wrap gap-4">
              {techResume && (
                <a
                  href={`/media/${techResume.file_key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm hover:bg-accent transition-colors"
                >
                  <span className="font-medium">Tech Resume</span>
                  <span className="text-muted-foreground">
                    {techResume.label}
                  </span>
                </a>
              )}
              {businessResume && (
                <a
                  href={`/media/${businessResume.file_key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm hover:bg-accent transition-colors"
                >
                  <span className="font-medium">Business Resume</span>
                  <span className="text-muted-foreground">
                    {businessResume.label}
                  </span>
                </a>
              )}
            </div>
          </section>
        )}

        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-4">Send a message</h2>
          <ContactForm siteKey={SITE_KEY} consentText="I consent to having my data stored for the purpose of this contact submission." />
        </section>
      </main>
    </>
  );
}
