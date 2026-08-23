import DealflowForm from "@/features/forms/DealflowForm";
import type { Metadata } from "next";

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "1x00000000000000000000AA";

export const metadata: Metadata = {
  title: "Dealflow — Siddhesh Chaudhari",
  description: "Investor introductions — share your firm and focus area for direct review.",
  alternates: { canonical: "/dealflow" },
  openGraph: {
    title: "Dealflow — Siddhesh Chaudhari",
    description: "Investor introductions — share your firm and focus area for direct review.",
    type: "website",
  },
  twitter: {
    card: "summary",
  },
};

export default function DealflowPage() {
  return (
    <main className="flex flex-1 flex-col px-6 py-12 max-w-2xl mx-auto w-full">
      <h1 className="text-3xl font-semibold mb-4">Dealflow</h1>
      <p className="text-muted-foreground mb-8">
        Investors: introduce your firm and focus area. Submissions are
        reviewed directly.
      </p>

      <DealflowForm siteKey={SITE_KEY} consentText="I consent to having my data stored for the purpose of this dealflow submission. My information will not be shared with third parties." />
    </main>
  );
}
