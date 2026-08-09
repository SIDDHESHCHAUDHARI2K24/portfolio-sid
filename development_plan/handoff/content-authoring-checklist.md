# Content Authoring Checklist (TD-36 / P3.T6.S6)

Authoring is where the design meets reality — it will surface content-model gaps (field too short, section that doesn't fit, tag vocabulary that doesn't carve content the way you think about it). **Budget time to fix gaps, not just to type content.**

Precondition: domain cutover done (TD-36.S1); admin portal live at `admin.siddhesh-chaudhari.com`.

## OverviewIntro — six rows (admin → Overview)

One row per audience plus default; `default` is what crawlers and first-time visitors see — write it first.

- [ ] `default` — headline, body (markdown), hero image, CTA label + URL
- [ ] `recruiters`
- [ ] `techies`
- [ ] `investors`
- [ ] `founders`
- [ ] `personal`

Each row: headline, body, `hero_image` (uploaded to R2), `cta_label` + `cta_url` (optional).

## Timeline (full history)

- [ ] Every education entry (`kind=EDUCATION`) and experience entry (`kind=EXPERIENCE`)
- [ ] Per entry: title, organisation, location, start/end dates (blank end = current), markdown summary, highlights, external URL where relevant
- [ ] Topic tags attached; audience overrides only where tags don't express it
- [ ] At least one entry per tag used in the audience-tag matrix (so highlighting is demonstrable)

## Projects (with attachments)

- [ ] Each project: title, slug, summary, markdown description, topic tags, audience override
- [ ] Experience cross-link (`timeline_entry_id`) where the project came from a role
- [ ] Attachments uploaded (PDF/PPT/IMAGE) — verify content-hashed URLs load
- [ ] Video URLs where present (YouTube; embeds use `youtube-nocookie.com`)
- [ ] Choose one project to **pin** (`is_pinned`) for its tile if latest-by-date isn't representative

## Skills (with icons)

- [ ] All sections: Languages, Tools, Frameworks, AI, Business
- [ ] Business subsections (e.g. "Product Management & Operations", "Consulting & Venture Capital") get one icon at subsection head; tech skills get per-skill icons
- [ ] `icon_slug` = Simple Icons slug where one exists (brands only); otherwise upload fallback icon (`icon_key`); verify admin preview shows no broken icons
- [ ] Ordering via `sort_order`. No topic tags on skills — everyone sees everything

## Certifications

- [ ] Technical and business entries: title, issuer, kind, issued/expiry dates
- [ ] `credential_url` where available; otherwise upload PDF/image (`file_key`)
- [ ] Verify expand-to-view on **a real mobile browser** — PDF inline fails on Mobile Safari; the "Open PDF" fallback must work

## Resumes — both PDFs

- [ ] `TECH` variant PDF uploaded and active
- [ ] `BUSINESS` variant PDF uploaded and active
- [ ] Both labelled clearly in the default view; verify links crawlable from `/` and PDFs open from R2

## Audience-tag matrix (admin → Tag Map)

Configure with **real** tags replacing the seed defaults:

| Audience | Example real tags to map |
|---|---|
| Recruiters | engineering, consulting |
| Techies | engineering, ai, tools |
| Investors | startup, fundraising, investing |
| Founders | startup, consulting, vc |
| Personal | personal, hobbies |

- [ ] Every topic tag in use is placed sensibly; delete unused seed tags (delete is blocked while in use)
- [ ] Spot-check highlight/dim on Timeline and Projects per audience after saving

## Posts — at least a few per collection (3 collections)

- [ ] `TECH_RABBITHOLE` — a few posts
- [ ] `HOW_I_USE_AI` — a few posts
- [ ] `VC_FOR_FOUNDERS` — a few posts
- [ ] Each post: title, summary, external URL, platform, published date
- [ ] Collection membership and topic tags set **independently** (collections route pages; topic tags drive highlighting)

## Prose pages

- [ ] Hobbies (`group=HOBBIES`)
- [ ] Work Views (`group=WORK_VIEWS`) — private content lives only in the database; never in git
- [ ] Investor Intro (`group=INVESTOR_INTRO`) — what you offer + deck-analysis teaser, `cta_url` → your Google Form
- [ ] CTA appears only when both label and URL set

## Collections — books / anime / manhwa

- [ ] Books with sections (Tech / Business / Personal Development), status, note
- [ ] Anime and Manhwa entries with status and note
- [ ] Cover lookup on save; expect **manual upload often for manhwa** (Jikan coverage thin) — not an error state
- [ ] Verify all covers serve from R2 (no third-party image requests at render)

## Contact details

- [ ] Email as **plain text** (also in Person JSON-LD — no obfuscation)
- [ ] LinkedIn URL
- [ ] Cal.com booking link
- [ ] Consent wording finalised for dealflow form (a snapshot is stored per submission)

## Done criteria

- [ ] Every page has real content; no tile empty for its intended audience
- [ ] Default view complete for crawlers
- [ ] Run Playwright critical journeys after authoring (TD-36.S5)
