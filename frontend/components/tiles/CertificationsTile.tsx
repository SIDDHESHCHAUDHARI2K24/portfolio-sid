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

  const latest = certs
    .slice()
    .sort((a, b) => new Date(b.issued_date).getTime() - new Date(a.issued_date).getTime())[0];

  return {
    id: "certifications",
    title: "Certifications",
    summary: latest
      ? `${latest.title} from ${latest.issuer}`
      : `${certs.length} certifications`,
    href: "/certifications",
    audiences: ["recruiters", "techies", "investors", "founders"],
    priority: 14,
    isEmpty: false,
  };
}
