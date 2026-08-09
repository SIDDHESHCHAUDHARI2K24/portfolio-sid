"use client";

import type { Project, AttachmentRef } from "@/features/projects/lib/types";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { useEffect } from "react";

interface Props {
  project: Project;
}

export default function ProjectDetail({ project }: Props) {
  useEffect(() => {
    if (project.timeline_entry_id && window.location.hash) {
      const el = document.getElementById(window.location.hash.slice(1));
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("ring-2", "ring-primary", "rounded");
        setTimeout(() => {
          el.classList.remove("ring-2", "ring-primary", "rounded");
        }, 2000);
      }
    }
  }, [project.timeline_entry_id]);

  const videoId = project.video_url
    ? extractYouTubeId(project.video_url)
    : null;

  return (
    <div className="space-y-8 w-full max-w-3xl mx-auto">
      <Link
        href="/projects"
        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        &larr; All Projects
      </Link>

      <section>
        <h1 className="text-3xl font-semibold tracking-tight mb-2">
          {project.title}
        </h1>
        {project.summary && (
          <p className="text-muted-foreground">{project.summary}</p>
        )}
      </section>

      {project.description && (
        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <ReactMarkdown rehypePlugins={[rehypeSanitize]} remarkPlugins={[remarkGfm]}>
            {project.description}
          </ReactMarkdown>
        </div>
      )}

      {videoId && (
        <div className="aspect-video rounded-lg overflow-hidden border border-border">
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${videoId}`}
            title="Project video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            loading="lazy"
            className="w-full h-full"
          />
        </div>
      )}

      {project.attachments && project.attachments.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-3">Attachments</h2>
          <div className="flex flex-wrap gap-3">
            {project.attachments.map((att: AttachmentRef) => (
              <a
                key={att.id}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm hover:border-primary/50 transition-colors"
              >
                {att.kind === "pdf"
                  ? "PDF"
                  : att.kind === "ppt"
                    ? "PPT"
                    : "Image"}
                :{" "}
                {att.label}
              </a>
            ))}
          </div>
        </section>
      )}

      {project.timeline_entry_id && (
        <section className="pt-4 border-t border-border">
          <Link
            href={`/timeline#entry-${project.timeline_entry_id}`}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            View related experience &rarr;
          </Link>
        </section>
      )}

      {project.topic_tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {project.topic_tags.map((t: { slug: string; label: string }) => (
            <span
              key={t.slug}
              className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
            >
              {t.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function extractYouTubeId(url: string): string | null {
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtube.com")) {
      return u.searchParams.get("v");
    }
    if (u.hostname === "youtu.be") {
      return u.pathname.slice(1);
    }
  } catch {
    return null;
  }
  return null;
}
