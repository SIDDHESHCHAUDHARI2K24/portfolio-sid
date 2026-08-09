# DESIGN.md — Portfolio Dark Theme

## Colour Tokens
```
--ink:            #0A0A0A  (page base)
--surface:        #16161A  (tile background)
--surface-raised: #1F1F24  (hover, elevated tile)
--line:           #2A2A31  (borders, dividers)
--text:           #F2F2F0  (primary text)
--text-muted:     #8A8A94  (metadata, captions)
--relevant:       #E8B34B  (warm amber — relevance signal ONLY, never decoration)
--relevant-dim:   #6B5423  (relevant border at rest)
```

## Typography

| Role | Face | Use |
|---|---|---|
| Display | Archivo Black or Space Grotesk Bold | Intro adjectives, page titles, tile headlines |
| Body | Inter | Prose, summaries, descriptions, forms |
| Utility | JetBrains Mono | Dates, percentages, tag slugs, counter |

## Type Scale
```
display-xl:  clamp(2.5rem, 8vw, 5rem)    900 weight, uppercase, -0.04em tracking
display-lg:  clamp(2rem, 5vw, 3.5rem)     900 weight, -0.03em tracking
title:       1.5rem                         700 weight, -0.02em tracking
body:        1rem / 1.6                     400 weight
small:       0.875rem / 1.5                 400 weight
mono-sm:     0.8125rem                      tabular-nums, 0.02em tracking
label:       0.6875rem                      uppercase, 0.2em tracking, muted
```

## Layout
```
radius:   tile 4px · control 3px · pill 999px
spacing:  4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96
grid:     12 columns, 24px gutter, max-width 1280px
```

## Elevation
Borders only — no drop shadows, no glows.
Normal: `--surface` against `--ink` with `--line` border.
Hover: rises to `--surface-raised`, brighter border.
Relevant tiles: `--relevant-dim` border at rest.

## Colour Semantics
Amber (`--relevant`) used EXCLUSIVELY for relevance signalling.
Never on general buttons, general headings, or as decoration.
Relevant entries: amber left rule + chromatic accents.
Neutral content: full legibility, no colour, NOT faded.

## Motion
- Intro sequence: ~3s, Framer Motion, once per session
- Category switch: instant, no animation
- Hover transitions: 150ms
- Scroll-triggered reveals: none
- Page transitions: none
