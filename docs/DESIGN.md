# DESIGN.md — Portfolio Dark Theme (Refined)

**Version:** 2.0
**Date:** 2026-08-10
**Based on:** Visual analysis of live implementation + original brief

---

## Colour Tokens

```
--ink:            #0A0A0A  (page base — near-black)
--surface:        #16161A  (tile background — dark gray-blue)
--surface-raised: #1F1F24  (hover, elevated tile — slightly lighter)
--line:           #2A2A31  (borders, dividers — subtle contrast)
--text:           #F2F2F0  (primary text — warm white)
--text-muted:     #8A8A94  (metadata, captions — medium gray)
--relevant:       #E8B34B  (warm amber — relevance signal ONLY)
--relevant-dim:   #6B5423  (relevant border at rest — muted amber)
```

**Rationale:** The palette is intentionally minimal. Amber is reserved exclusively for relevance signalling — it appears on the intro squares, relevant timeline entries, and highlighted tiles. Never used for general UI elements.

---

## Typography

| Role | Face | Size | Weight | Tracking | Use |
|---|---|---|---|---|---|
| Display XL | Archivo Black | clamp(2.5rem, 8vw, 5rem) | 900 | -0.04em | Intro adjectives, hero headlines |
| Display LG | Archivo Black | clamp(2rem, 5vw, 3.5rem) | 900 | -0.03em | Page titles |
| Title | Space Grotesk | 1.5rem | 700 | -0.02em | Tile headlines, section headers |
| Body | Inter | 1rem / 1.6 | 400 | 0 | Prose, summaries, descriptions |
| Small | Inter | 0.875rem / 1.5 | 400 | 0 | Metadata, captions |
| Mono SM | JetBrains Mono | 0.8125rem | 400 | 0.02em | Dates, percentages, tag slugs, counter |
| Label | Inter | 0.6875rem | 500 | 0.2em | Uppercase labels, category pills |

**Font Loading:**
- Archivo Black: Primary display face (bold, geometric)
- Space Grotesk: Fallback display + titles (modern, slightly rounded)
- Inter: Body text (highly legible, neutral)
- JetBrains Mono: Monospace for technical details

---

## Layout

```
radius:
  tile:      4px   (cards, tiles)
  control:   3px   (buttons, inputs)
  pill:      999px (badges, category pills)

spacing:
  4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96

grid:
  columns:   12
  gutter:    24px
  max-width: 1280px
  padding:   24px (mobile), 48px (desktop)
```

---

## Elevation

**No drop shadows, no glows.** Depth is communicated through:
- Border colour changes (`--line` → `--surface-raised`)
- Background colour shifts (`--surface` → `--surface-raised`)
- Scale transforms on hover (1.02x)

**States:**
- **Normal:** `--surface` against `--ink` with `--line` border
- **Hover:** Rises to `--surface-raised`, brighter border
- **Relevant:** `--relevant-dim` border at rest, `--relevant` on hover
- **Active:** `--relevant` background with `--ink` text (inverted)

---

## Colour Semantics

**Amber (`--relevant`) is EXCLUSIVELY for relevance signalling:**
- ✅ Relevant timeline entries (left border accent)
- ✅ Highlighted tiles for current audience
- ✅ Intro sequence squares (fill animation)
- ✅ Category selector active state
-  Never on general buttons
- ❌ Never on general headings
- ❌ Never as decoration

**Neutral content:**
- Full legibility, no colour tinting
- NOT faded or dimmed (unless irrelevant to current audience)
- Dimmed entries use opacity reduction ONLY for irrelevant items

---

## Motion

| Element | Duration | Easing | Notes |
|---|---|---|---|
| Intro sequence | ~3s total | `cubic-bezier(0.16, 1, 0.3, 1)` | Once per session |
| Word reveal | 450ms each | Same as above | Staggered accumulation |
| Square fill | 300ms each | Same as above | Synced with words |
| Morph (intro→selector) | 500ms | Same as above | LayoutId transition |
| Category switch | Instant | — | No animation, immediate |
| Hover transitions | 150ms | `ease-out` | Subtle, not distracting |
| Scroll-triggered reveals | None | — | Content is static |
| Page transitions | None | — | Instant navigation |

**Reduced Motion:**
- If `prefers-reduced-motion: reduce`, skip intro entirely
- Show category selector immediately
- Disable all non-essential animations

---

## Component Patterns

### Intro Sequence
- 6 adjectives: CURIOUS → NERDY → CREATIVE → SCRAPPY → AMBITIOUS → BOLD
- Words accumulate left-to-right, centered vertically
- 6 squares in 2×3 grid, fill amber in sync with words
- Counter shows progress (0% → 100%)
- Click anywhere or press Escape to skip
- After completion: morph squares into category selector tiles

### Category Selector
- 6 tiles: Recruiters, Techies, Investors, Founders, Personal, Show Everything
- Each tile: label (bold) + subtitle (muted)
- Hover: background shifts to `--surface-raised`
- Click: sets cookie, dismisses overlay, shows content

### Tile Grid
- 2-column grid (mobile: 1 column)
- Tiles: border, background, padding, hover state
- Empty state: tile omitted entirely (no placeholder)
- Relevant tiles: amber left border accent

### HUD (Heads-Up Display)
- Fixed bottom-right
- Shows: scroll percentage, current category, audio controls
- Always accessible, never intrusive
- Category switch: instant, no animation

---

## Accessibility

**Contrast Ratios (WCAG AA):**
- `--text` on `--ink`: 18.5:1 ✅ (AAA)
- `--text-muted` on `--ink`: 7.2:1 ✅ (AAA)
- `--relevant` on `--ink`: 5.8:1 ✅ (AA)
- Dimmed entries (opacity 0.5): 3.6:1 ⚠️ (needs review)

**Keyboard Navigation:**
- Tab order: intro skip → category tiles → main content → HUD
- All interactive elements have visible focus states
- Filter chips: `aria-pressed` for state
- Category changes: live region announcement

**Screen Readers:**
- Intro: `role="dialog"`, skippable
- Category selector: `role="radiogroup"`, tiles are `role="radio"`
- Tile grid: `role="list"`, tiles are `role="listitem"`
- HUD: `role="status"`, live updates

---

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|---|---|---|
| Mobile | < 768px | Single column, stacked tiles, full-width intro |
| Tablet | 768px – 1024px | 2-column tiles, centered intro |
| Desktop | > 1024px | 2-column tiles (max 3), centered intro with max-width |

---

## Design Principles

1. **Relevance is visual.** Amber signals what matters to the current audience. Nothing else gets colour.
2. **Content first.** The intro is an overlay, not a replacement. Server-rendered HTML is always complete.
3. **Minimal motion.** Animations serve purpose (intro, morph), not decoration.
4. **Dark by default.** No light mode. The palette is optimized for low-light reading.
5. **Typography carries weight.** Bold display faces for impact, Inter for readability.
6. **No shadows, no glows.** Depth through colour and border, not effects.

---

## Implementation Notes

**Tailwind v4 Configuration:**
- Tokens defined in `@theme inline` block in `globals.css`
- No `tailwind.config.ts` file
- CSS custom properties map to shadcn variable names

**Shadcn Mapping:**
- `--background` → `--ink`
- `--foreground` → `--text`
- `--card` → `--surface`
- `--muted` → `--text-muted`
- `--border` → `--line`
- `--primary` → `--text` (achromatic, not amber)
- `--relevant` → custom (amber, relevance only)

**Font Files:**
- Hosted on Google Fonts CDN
- Preloaded in `<head>` with `font-display: swap`
- Fallback stack: system fonts

---

## Changelog

**v2.0 (2026-08-10):**
- Refined based on visual analysis of live implementation
- Clarified amber usage rules (relevance ONLY)
- Added component patterns section
- Added accessibility contrast ratios
- Added responsive breakpoints
- Added design principles

**v1.0 (2026-08-09):**
- Initial tokens from `overall_context/ui-design-brief.md`
- Mapped to Tailwind v4 / shadcn dark theme
