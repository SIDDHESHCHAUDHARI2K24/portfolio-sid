"use client";

import type { paths } from "@/src/api";
import CertViewer from "@/components/certifications/CertViewer";
import { ExternalLink } from "lucide-react";

type Cert = paths["/api/v1/certifications"]["get"]["responses"]["200"]["content"]["application/json"][number];

interface Props {
  technical: Cert[];
  business: Cert[];
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short" });
}

function CertCard({ cert }: { cert: Cert }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{cert.title}</h3>
          <p className="text-sm text-muted-foreground">{cert.issuer}</p>
        </div>
        {cert.credential_url && (
          <a
            href={cert.credential_url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
            title="Verify credential"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>

      <p className="text-sm text-muted-foreground">
        Issued {formatDate(cert.issued_date)}
        {cert.expires_date
          ? ` · Expires ${formatDate(cert.expires_date)}`
          : " · No expiration"}
      </p>

      <CertViewer
        fileKey={cert.file_key}
        fileType={cert.file_type}
        credentialUrl={cert.credential_url}
        title={cert.title}
      />
    </div>
  );
}

export default function CertsClient({ technical, business }: Props) {
  return (
    <div className="space-y-12">
      {technical.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Technical</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {technical.map((cert) => (
              <CertCard key={cert.id} cert={cert} />
            ))}
          </div>
        </section>
      )}

      {business.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Business</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {business.map((cert) => (
              <CertCard key={cert.id} cert={cert} />
            ))}
          </div>
        </section>
      )}

      {technical.length === 0 && business.length === 0 && (
        <div className="py-12 text-center text-muted-foreground">
          <p>No certifications yet.</p>
        </div>
      )}
    </div>
  );
}
