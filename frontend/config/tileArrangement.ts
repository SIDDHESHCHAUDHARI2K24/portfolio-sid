/**
 * Audience → tile-order map.
 * `default` is intentionally retained even though no UI exposes a catch-all.
 * It serves crawler/first-visit SSR (conventions.md #1: overlay, never replacement) —
 * the server renders the full grid with `default` before hydration picks an audience.
 * `default` is **not** user-selectable (IntroOverlay/HUD no longer offer it).
 */
export const tileArrangement: Record<string, string[]> = {
  recruiters: ["contact", "timeline", "projects", "skills", "certifications", "tech_rabbithole", "how_i_use_ai", "work_views"],
  techies: ["contact", "timeline", "projects", "skills", "certifications", "how_i_use_ai", "tech_rabbithole", "work_views"],
  investors: ["contact", "timeline", "thesis", "dealflow", "tech_rabbithole", "how_i_use_ai", "certifications"],
  founders: ["contact", "timeline", "investor_intro", "vc_for_founders", "how_i_use_ai", "tech_rabbithole", "certifications"],
  personal: ["contact", "timeline", "books", "anime_manga", "hobbies"],
  default: ["contact", "timeline", "projects", "skills", "certifications", "tech_rabbithole", "how_i_use_ai", "vc_for_founders", "thesis", "books", "anime_manga", "hobbies", "work_views", "investor_intro", "dealflow"],
};
