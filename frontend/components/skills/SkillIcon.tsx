"use client";

import { useState } from "react";

interface Props {
  slug: string | null;
  r2Key: string | null;
  label: string;
  size?: number;
}

const R2_DOMAIN = "https://media.siddhesh-chaudhari.com";

function slugToUrl(slug: string): string {
  return `https://cdn.jsdelivr.net/npm/simple-icons@14/icons/${encodeURIComponent(slug)}.svg`;
}

export default function SkillIcon({ slug, r2Key, label, size = 24 }: Props) {
  const [failedCdn, setFailedCdn] = useState(false);
  const [failedR2, setFailedR2] = useState(false);

  const cdnUrl = slug ? slugToUrl(slug) : null;
  const r2Url = r2Key ? `${R2_DOMAIN}/${r2Key}` : null;

  if (cdnUrl && !failedCdn) {
    return (
      <img
        src={cdnUrl}
        alt={label}
        width={size}
        height={size}
        className="inline-block object-contain"
        onError={() => setFailedCdn(true)}
      />
    );
  }

  if (r2Url && !failedR2) {
    return (
      <img
        src={r2Url}
        alt={label}
        width={size}
        height={size}
        className="inline-block object-contain"
        onError={() => setFailedR2(true)}
      />
    );
  }

  return (
    <span
      className="inline-flex items-center justify-center rounded bg-muted text-muted-foreground text-xs font-medium"
      style={{ width: size, height: size }}
      title={label}
    >
      {label.charAt(0).toUpperCase()}
    </span>
  );
}
