# UI Design Brief — Audience-Segmented Portfolio

**Supporting document** · Companions: `tech-stack-analysis.md`, `dependency-map.md`, `development-plan-P0..P3.md`
**Status:** Draft for approval
**Audience:** coding agents (as build context) and Google Stitch (as generation input)

---

## 1. How to use this document

**Coding agents** treat §3–§10 as binding. Where this brief and a phase plan disagree, the phase plan wins on behaviour and this brief wins on appearance.

**Google Stitch** consumes §11 — screen-by-screen prompts written to be pasted directly. §12 lists what Stitch must not do, because its defaults conflict with decisions already made.

Stitch output quality is mostly a function of prompt specificity. Vague prompts return the same dark dashboard everyone else gets.

---

## 2. Design thesis

The site's single argument is that **the same content means different things to different readers.** Everyone sees everything; what changes is emphasis.

That is unusual, and it should be the thing the design is *about* — not a feature buried in an opacity value. Every visual decision below serves it.

The site's job, stated plainly: convince a specific reader, within about eight seconds of arriving, that the relevant parts of this person's work were assembled for them.

---

## 3. Fixed constraints

Non-negotiable. These came out of architectural decisions, not aesthetic preference.

| Constraint | Reason |
|---|---|
| Dark theme only, single palette | Light mode doubles token surface for no benefit |
| No hexagons anywhere | Retired in favour of a tile grid; only the intro's six squares survive as motif |
| Tile grid for the category selector on **all** breakpoints | One responsive component, no mobile fork |
| Irrelevant *tiles* are omitted; irrelevant *entries* are dimmed | Two distinct mechanics — never conflate |
| Intro is an overlay above rendered content, never a replacement | Crawlers must receive content, not an animation |
| Every colour comes from a token | The re-skin is a token swap; hardcoded values become manual edits |
| Dimmed text still meets WCAG AA | Dimmed content is content people may want to read |

---

## 4. Colour

### The one real risk in this brief

The obvious move is near-black plus a bright accent used decoratively. That is also the most common AI-generated dark-site look, and it would spend the design's boldness on nothing.

**Proposal: colour means relevance.** The entire interface is achromatic — ink, greys, white. The only saturated element on any page is content relevant to the *current reader*. Switching audience visibly recolours the page. The accent stops being decoration and becomes the product's core mechanic made visible.

This also solves the dimming problem elegantly: relevant content isn't brighter, it's *chromatic*, while everything else stays neutral at full legibility. No contrast is sacrificed to signal emphasis.

```
--ink            #0A0A0A   page base (carried from your intro code)
--surface        #16161A   tile background
--surface-raised #1F1F24   hover, elevated tile
--line           #2A2A31   borders, dividers
--text           #F2F2F0   primary text
--text-muted     #8A8A94   metadata, captions
--relevant       #E8B34B   warm amber — relevance signal ONLY
--relevant-dim   #6B5423   relevant border at rest
```

**Why amber rather than the reference's teal:** warm-against-cool reads as "this one is for you" more immediately than one cool hue among others, and cyan-on-charcoal is the most defaulted pairing in this space. If you prefer continuity with the GRIDZ reference, substitute teal `#14B8A6` — the *semantics* matter more than the hue, and nothing else in the system changes.

**Discipline this requires:** amber never appears as decoration. Not on buttons-in-general, not on headings, not as a gradient. If it appears where relevance isn't being communicated, the signal is dead.

---

## 5. Typography

Three roles, each doing a distinct job.

| Role | Face | Use |
|---|---|---|
| **Display** | Archivo Black, or Space Grotesk Bold | Intro adjectives, page titles, tile headlines |
| **Body** | Inter | Prose, summaries, descriptions, forms |
| **Utility** | JetBrains Mono | Dates, percentages, tag slugs, the loader counter, timeline ranges |

The mono face isn't stylistic — this is a portfolio built on dated records, tag vocabularies and a percentage indicator. Tabular figures in date ranges genuinely read better, and the tag slugs *are* identifiers.

Your intro code uses Inter Black, uppercase, `tracking-tighter`. Keep the treatment; swap the face for the display family. Inter Black is competent and anonymous; the adjectives are the most personal moment on the site and deserve a face with a point of view.

```
display-xl   clamp(2.5rem, 8vw, 5rem)   weight 900, uppercase, tracking -0.04em
display-lg   clamp(2rem, 5vw, 3.5rem)   weight 900, tracking -0.03em
title        1.5rem                      weight 700, tracking -0.02em
body         1rem / 1.6                  weight 400
small        0.875rem / 1.5              weight 400
mono-sm      0.8125rem                   tabular-nums, tracking 0.02em
label        0.6875rem                   uppercase, tracking 0.2em, muted
```

---

## 6. Layout, spacing, elevation

```
radius:   tile 4px · control 3px · pill 999px
spacing:  4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96
grid:     12 columns, 24px gutter, max-width 1280px
```

**Near-square corners are deliberate.** The tile grid derives from the six-square loader; rounded corners would weaken that lineage.

**Elevation is borders, not shadows.** On a near-black base, shadows are invisible and reach for a glow that reads as generic. Tiles separate through `--surface` against `--ink` plus a `--line` border. Hover raises to `--surface-raised` and brightens the border. Relevant tiles carry a `--relevant-dim` border at rest.

Tiles vary in size — the GRIDZ reference is right about this. A uniform grid reads as a template; mixed spans read as edited. Use 1×1, 2×1 and 2×2 spans, with the main intro tile full-width.

---

## 7. Signature element

**The six-square loader that becomes the navigation.**

Six adjectives accumulate while six squares fill. At completion the squares form a 2×3 grid — which then expands outward into the category selector. The loader *is* the navigation, before expansion.

Nothing else in the interface should compete with this. It carries the whole first impression, and it earns it by being structurally true: one object, seen at two scales, which is exactly the site's argument.

---

## 8. Motion

Framer Motion only. Motion is used in three places and nowhere else — scattered micro-animations are the clearest tell of a generated design.

### The intro sequence (~3s, once per session)

```
0.00s  ink field, nothing
0.20s  "CURIOUS"     square 1 fills
0.65s  "NERDY"       square 2 fills
1.10s  "CREATIVE"    square 3
1.55s  "SCRAPPY"     square 4
2.00s  "AMBITIOUS"   square 5
2.45s  "BOLD"        square 6 — all six words visible, 2×3 grid complete
2.70s  squares expand outward into the category tiles; words fade
3.00s  selector interactive
```

Words **accumulate**, never replace — all six on screen at the final frame is the payoff. Each enters with a short upward translate and fade, easing `cubic-bezier(0.16, 1, 0.3, 1)` (carried from your original).

Squares morph to tiles via shared `layoutId`. Both states stay mounted through the transition; animate layout and opacity rather than mounting and unmounting.

A counter sits bottom-right in mono, ticking 0–100%. **Decorative** — it measures nothing today and becomes a real connection indicator when the voice agent lands. Label it something that isn't a claim; "Status" overstates it.

**Escapes:** `sessionStorage` bypass for returning visitors, `prefers-reduced-motion` skips entirely, click and Escape skip.

### Category switch — no motion

Instant. No transition, no fade, no re-play of the intro. Content re-colours in one frame. Switching is meant to feel like nothing happened except the page now knows who you are.

### Everything else

Hover transitions at 150ms. Scroll-triggered reveals: none. Page transitions: none.

---

## 9. Screens

### Overview — the primary surface

```
┌──────────────────────────────────────────────────────┐
│  INTRO TILE (full width)                             │
│  Headline · "how I can help you" · optional hero     │
│  Optional CTA                                        │
├─────────────────┬────────────────────────────────────┤
│  CONTACT        │  Email (plain text) · LinkedIn     │
├─────────┬───────┴────────┬───────────────────────────┤
│ TIMELINE│  PROJECTS      │  SKILLS                   │
│  2×1    │  2×2           │  1×1                      │
├─────────┼────────────────┼───────────────────────────┤
│ CERTS   │  RABBITHOLE    │  HOW I USE AI             │
└─────────┴────────────────┴───────────────────────────┘
```

Intro tile full-width at top; Contact directly beneath for every audience; audience tiles below in configured order. **Irrelevant tiles are absent, not dimmed.** Empty tiles are absent. Grid reflows without gaps.

### Timeline

Vertical chronological, education and experience interleaved by date and distinguished by kind — a mono label rather than a colour, since colour is reserved. Date ranges in mono. Filter chips above, multi-select, visually distinct from the relevance mechanic. Relevant entries carry an amber left rule and chromatic accents; others stay neutral at full legibility.

### Projects

Grid of cards → detail page with markdown description, attachments, video. Cross-link to the linked experience navigates to the timeline entry, scrolls to it and briefly outlines it.

### Skills

Static sectioned lists. Tech sections show per-skill icons; Business sections show one icon at the sub-section head. **No relevance treatment** — everyone sees the same thing.

### Certifications

Two sections (Technical, Business). Card with an expand control revealing the PDF or image inline. On mobile, expand becomes "Open PDF" — inline rendering is unavailable there.

### Posts, Thesis

Link cards: title, summary, platform in mono, date. External-link affordance. Thesis follows the same pattern, linking to Drive.

### Books, Anime & Manhwa

Cover-image tile grids in sections. Covers carry the visual weight; titles sit beneath in body.

### Prose pages

Single readable column, max 68ch. Markdown. Optional CTA button at the end.

### Contact

Email as **plain selectable text** — never obfuscated, never an image, never assembled in JavaScript. Agents read the DOM. LinkedIn, Cal.com booking, contact form, both resume PDFs.

### HUD

Fixed bottom-right, persistent everywhere. Compact category selector, scroll percentage in mono, audio control. Collapsed by default to a small marker; expands on hover or tap. Includes a "Show everything" reset.

---

## 10. States and quality floor

| State | Treatment |
|---|---|
| Relevant | Amber border and accents; chromatic against neutral |
| Neutral | Full legibility, no colour — *not* faded |
| Tile empty | Absent from the grid entirely |
| Loading | Skeleton at `--surface`, no spinner, no shimmer |
| Error | Plain text stating what failed and what to do. No apology, no illustration |
| Empty page | One line and a link. An empty screen is an invitation, not a dead end |

Responsive down to 360px. Visible keyboard focus using a `--text` outline, never a colour that implies relevance. Reduced motion respected throughout. Touch targets ≥44px.

**Copy voice:** active, sentence case, plain verbs. Buttons name what happens — "Send message," not "Submit." An action keeps one name through the flow.

---

## 11. Stitch prompt pack

Paste these individually. Each restates the constraints because Stitch does not carry context between generations.

> **Shared preamble — prepend to every prompt:**
> Dark interface only, base `#0A0A0A`, tiles `#16161A`, borders `#2A2A31`, primary text `#F2F2F0`, muted text `#8A8A94`. One accent, amber `#E8B34B`, used **exclusively** to mark content relevant to the current viewer — never for decoration, general buttons, headings or gradients. Corner radius 4px maximum. Elevation via borders only — no drop shadows, no glows. Display type is a heavy grotesque, uppercase, tight tracking; body is Inter; dates, percentages and tags are monospace. No hexagons.

**Screen 1 — Intro sequence, final frame.** Six single words stacked centred and all visible at once — CURIOUS, NERDY, CREATIVE, SCRAPPY, AMBITIOUS, BOLD — in very large heavy uppercase display type, tight tracking, white on near-black. Bottom-right: a 2×3 grid of six small filled squares beside a large monospace percentage reading 100%, with a small uppercase letter-spaced label beneath. Nothing else on screen.

**Screen 2 — Category selector.** Five large tiles in a responsive grid: "Recruiters & Hiring Managers", "Techies", "Investors", "Founders", "Stalkers & Others". Each tile has a heavy uppercase display title and one line of muted supporting text. Near-square corners, thin borders, no icons, no imagery. Hover state lifts the tile background one step and brightens its border. Same grid pattern on desktop and mobile, only column count changes.

**Screen 3 — Overview page.** A tile-based dashboard. Full-width tile at top with a large display headline and a short paragraph. Directly beneath, a wide contact tile showing an email address as plain text and a LinkedIn link. Below, a mixed-size tile grid — some 1×1, some 2×1, one 2×2 — each with a small uppercase monospace label, a title, and a one-line summary. Two tiles carry a thin amber border indicating relevance; the rest are neutral and equally legible. Bottom-right corner: a small fixed control showing a compact selector and a monospace scroll percentage.

**Screen 4 — Timeline.** A single vertical chronological column merging education and career entries. Each entry shows a monospace date range on the left, then a heavy title, an organisation name in muted text, and a short paragraph. Small uppercase monospace labels distinguish education from experience. Above the list, a row of pill-shaped filter chips with clear selected and unselected states. Two entries carry a thin amber left rule marking relevance; the others are neutral at full legibility, not faded.

**Screen 5 — Projects grid and detail.** Card grid with project title, one-line summary, and small monospace tags. Detail view: large display title, a body-width prose column, an attachment list with file-type labels, an embedded video placeholder, and a link back to a related career entry.

**Screen 6 — Skills.** Sectioned lists under headings: Coding Languages, Tools, Frameworks, AI, Business & Competencies. Technical sections show a small monochrome icon beside each skill; the Business section shows one icon per sub-section heading instead. Entirely neutral — no accent colour anywhere on this screen.

**Screen 7 — Certifications.** Two sections, Technical and Business. Each card shows title, issuer, monospace issue date, and an expand control. One card is shown expanded, revealing an embedded document preview panel inside the card.

**Screen 8 — Contact.** A page with an email address rendered as large plain selectable text, a LinkedIn link, a booking-link button, two labelled resume download links, and a short form with name, email, message and a bot-check widget placeholder.

**Screen 9 — Admin dashboard.** A dense, plain content-management interface, same dark palette but utilitarian. Left sidebar listing content types. Main area: a data table with title, status badges reading Draft / Scheduled / Published, dates in monospace, and row actions. Top-right primary action button. No decorative elements — this screen is for one person and optimises for speed.

---

## 12. What Stitch must not produce

Reject and regenerate if output contains any of these:

- Hexagonal shapes or honeycomb layouts
- Gradient backgrounds, glow effects, or drop shadows
- The accent colour used decoratively — on general buttons, headings, or dividers
- Rounded corners above 4px, or pill-shaped cards
- A separate mobile navigation pattern; the tile grid is responsive, not forked
- Light mode variants
- Stock illustrations, 3D renders, or abstract blob shapes
- Faded or low-contrast "de-emphasised" content — neutral means full legibility
- An obfuscated or image-based email address
- Emoji as interface iconography

**Take the tokens, not the markup.** Stitch emits HTML and Tailwind; the build has working React components. Import `DESIGN.md` values into `tailwind.config.ts` and leave the generated markup alone.
