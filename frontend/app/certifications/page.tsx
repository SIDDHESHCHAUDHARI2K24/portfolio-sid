import { apiFetch } from "@/lib/api";
import { CACHE_TAGS } from "@/lib/cacheTags";
import type { paths } from "@/src/api";
import type { Metadata } from "next";
import CertsClient from "@/components/certifications/CertsClient";

type Cert = paths["/api/v1/certifications"]["get"]["responses"]["200"]["content"]["application/json"][number];

export const metadata: Metadata = {
  title: "Certifications — Siddhesh Chaudhari",
  alternates: { canonical: "/certifications" },
};

export default async function CertificationsPage() {
  const certs: Cert[] = await apiFetch<Cert[]>("/certifications", {
    tags: [CACHE_TAGS.certifications],
    revalidate: 3600,
  });

  const technical = certs.filter((c) => c.kind === "technical");
  const business = certs.filter((c) => c.kind === "business");

  return (
    <main className="flex flex-1 flex-col px-6 py-12">
      <div className="w-full max-w-3xl mx-auto space-y-12">
        <h1 className="text-3xl font-semibold tracking-tight">
          Certifications
        </h1>
        <CertsClient technical={technical} business={business} />
      </div>
    </main>
  );
}
