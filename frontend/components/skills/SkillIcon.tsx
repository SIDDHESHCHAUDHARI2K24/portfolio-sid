"use client";

import { useState } from "react";

interface Props {
  slug: string | null;
  iconUrl: string | null;
  label: string;
  size?: number;
}

function slugToUrl(slug: string): string {
  return `https://cdn.jsdelivr.net/npm/simple-icons@14/icons/${encodeURIComponent(slug)}.svg`;
}

export default function SkillIcon({ slug, iconUrl, label, size = 24 }: Props) {
  const [failedCdn, setFailedCdn] = useState(false);
  const [failedIcon, setFailedIcon] = useState(false);

  const cdnUrl = slug ? slugToUrl(slug) : null;
  const mediaUrl = iconUrl ? iconUrl : null;

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

  if (mediaUrl && !failedIcon) {
    return (
      <img
        src={mediaUrl}
        alt={label}
        width={size}
        height={size}
        className="inline-block object-contain"
        onError={() => setFailedIcon(true)}
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
