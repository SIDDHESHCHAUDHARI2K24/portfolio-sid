"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

interface Props {
  fileUrl: string | null;
  fileType: string | null;
  credentialUrl: string | null;
  title: string;
}

export default function CertViewer({ fileUrl, fileType, credentialUrl, title }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [pdfInlineFailed, setPdfInlineFailed] = useState(false);
  const objectRef = useRef<HTMLObjectElement>(null);

  const hasPdf = fileType === "pdf" && !!fileUrl;
  const hasImage = fileType === "image" && !!fileUrl;
  const hasLink = !!credentialUrl;

  useEffect(() => {
    if (!hasPdf || !expanded) return;

    const timer = setTimeout(() => {
      const obj = objectRef.current;
      if (obj) {
        try {
          const doc = obj.contentDocument;
          if (!doc || doc.body.innerHTML.trim() === "") {
            setPdfInlineFailed(true);
          }
        } catch {
          setPdfInlineFailed(true);
        }
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [hasPdf, expanded]);

  if (!hasPdf && !hasImage && !hasLink) return null;

  const handleToggle = () => {
    setExpanded(!expanded);
    if (!expanded && hasPdf) setPdfInlineFailed(false);
  };

  return (
    <div>
      <button
        onClick={handleToggle}
        className="text-sm font-medium text-primary hover:underline"
      >
        {expanded ? "Collapse" : "View credential"}
      </button>

      {expanded && (
        <div className="mt-3 rounded-lg border border-border overflow-hidden">
          {hasPdf && !pdfInlineFailed && (
            <object
              ref={objectRef}
              data={fileUrl ?? undefined}
              type="application/pdf"
              className="w-full"
              style={{ minHeight: 500 }}
            >
              <p className="p-4 text-sm text-muted-foreground">
                Unable to display PDF inline.
              </p>
            </object>
          )}

          {hasPdf && pdfInlineFailed && (
            <div className="p-6 text-center space-y-3">
              <p className="text-sm text-muted-foreground">
                This device does not support inline PDF viewing.
              </p>
              <a
                href={fileUrl ?? undefined}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block text-sm font-medium text-primary hover:underline"
              >
                Open PDF
              </a>
            </div>
          )}

          {hasImage && (
            <div className="relative w-full" style={{ minHeight: 300 }}>
              <Image
                src={fileUrl ?? ""}
                alt={title}
                fill
                className="object-contain"
                sizes="(max-width: 768px) 100vw, 700px"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
