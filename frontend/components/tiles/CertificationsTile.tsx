import type { Tile } from "@/lib/tiles";
import type { paths } from "@/src/api";

type Cert = paths["/api/v1/certifications"]["get"]["responses"]["200"]["content"]["application/json"][number];

export function buildCertificationsTile(certs: Cert[]): Tile {
  if (certs.length === 0) {
    return {
      id: "certifications",
      title: "",
      summary: "",
      href: "/certifications",
      audiences: [],
      priority: 14,
      isEmpty: true,
    };
  }

  const pinned = certs.find((c) => c.is_pinned);
  const sorted = certs
    .slice()
    .sort((a, b) => new Date(b.issued_date).getTime() - new Date(a.issued_date).getTime());
  const display = pinned ?? sorted[0];

  return {
    id: "certifications",
    title: "Certifications",
    summary: display
      ? `${display.title} from ${display.issuer}`
      : `${certs.length} certifications`,
    href: "/certifications",
    audiences: ["recruiters", "techies", "investors", "founders"],
    priority: 14,
    isEmpty: false,
  };
}
