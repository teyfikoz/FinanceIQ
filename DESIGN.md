---
version: "alpha"
name: FundPortal
description: Editorial market intelligence design system for a fast, credibility-first financial analysis workspace.
colors:
  ink: "#0F172A"
  slate: "#475569"
  border: "#CBD5E1"
  canvas: "#F8FAFC"
  panel: "#FFFFFF"
  accent: "#0F766E"
  accent-strong: "#115E59"
  signal-positive: "#15803D"
  signal-negative: "#B91C1C"
  signal-watch: "#B45309"
  signal-info: "#1D4ED8"
  gold: "#B8891F"
  on-dark: "#F8FAFC"
  on-light: "#0F172A"
typography:
  h1:
    fontFamily: "Space Grotesk"
    fontSize: 2.9rem
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: -0.03em
  h2:
    fontFamily: "Space Grotesk"
    fontSize: 2.1rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em
  h3:
    fontFamily: "Space Grotesk"
    fontSize: 1.35rem
    fontWeight: 600
    lineHeight: 1.2
  body-lg:
    fontFamily: "IBM Plex Sans"
    fontSize: 1.05rem
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: "IBM Plex Sans"
    fontSize: 0.96rem
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "IBM Plex Sans"
    fontSize: 0.84rem
    fontWeight: 400
    lineHeight: 1.45
  metric-lg:
    fontFamily: "IBM Plex Sans"
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1
  label-caps:
    fontFamily: "IBM Plex Sans"
    fontSize: 0.72rem
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0.08em
rounded:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
spacing:
  xs: 6px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
components:
  app-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-light}"
    padding: 24px
  hero-panel:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.lg}"
    padding: 24px
  surface-panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.on-light}"
    rounded: "{rounded.md}"
    padding: 16px
  metric-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.on-light}"
    rounded: "{rounded.md}"
    padding: 16px
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.accent-strong}"
  chip-positive:
    backgroundColor: "{colors.signal-positive}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.xs}"
    padding: 8px
  chip-negative:
    backgroundColor: "{colors.signal-negative}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.xs}"
    padding: 8px
  chip-watch:
    backgroundColor: "{colors.signal-watch}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.xs}"
    padding: 8px
  data-table:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.on-light}"
    rounded: "{rounded.sm}"
  chart-frame:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.on-light}"
    rounded: "{rounded.md}"
    padding: 12px
---

## Overview
FundPortal should feel like a premium market desk, not a generic dashboard. The product sits between editorial intelligence and terminal-grade signal scanning. The interface should communicate speed, trust and clarity before it communicates feature depth.

The visual identity is built around three ideas:

1. Editorial credibility: dense but readable information blocks, restrained color, strong hierarchy.
2. Signal urgency: green, red and amber only appear where the user should act or pay attention.
3. Fast orientation: the first screen should answer "what matters now?" in under 10 seconds.

## Colors
The palette is mostly cool neutrals with one confident teal accent.

- `ink` is the foundation for headers, hero backgrounds and serious analytical surfaces.
- `canvas` should replace flat white as the page base, reducing glare and giving tables more structure.
- `accent` is reserved for primary actions, selected states and important navigation.
- `signal-positive`, `signal-negative` and `signal-watch` must never be used decoratively. They carry analytical meaning only.
- `gold` is reserved for ranked highlights, premium-seeming badges and "top pick" emphasis.

## Typography
Use `Space Grotesk` for headlines and section titles. It gives the app a distinctive, modern analyst-desk voice.

Use `IBM Plex Sans` for body, metrics and tables. It is compact, readable and appropriate for data-heavy UIs.

Typography rules:

- Headlines should be short, assertive and information-bearing.
- Metric text should feel sharp and compact, never oversized for decoration.
- Labels and captions should be uppercase or tightly spaced only when they add scannability.

## Layout
The app should move away from one long, endlessly scrolling control panel.

Preferred structure:

1. A hero strip that explains current setup, top signal and recommended route.
2. A compact control rail for market, timeframe and instrument selection.
3. One active analysis surface at a time.
4. Secondary detail modules below or behind expanders, not all visible at once.

Performance-aware layout rules:

- Render one major analysis view at a time.
- Defer heavy charts until the relevant view is opened.
- Prefer summary cards over large chart grids on the landing screen.
- Keep first paint focused on overview, top signal and one chart at most.

## Elevation & Depth
Depth should be subtle. Use borders, not dramatic shadows.

- Cards rely on border contrast and spacing, not floating glassmorphism.
- Hero areas can use gradients, but analytic panels should remain calm and flat.
- Tables and charts should feel embedded in a serious workspace rather than promotional marketing blocks.

## Shapes
Rounded corners should be present but controlled.

- Core cards: `16px`
- Buttons and chips: `10px`
- Small tags: `6px`

Avoid overly soft, bubbly geometry. This is a finance tool, not a consumer social app.

## Components
### Hero Panel
Use for the first screen only. It should contain:

- Current market setup
- One top local signal
- One recommended next action

### Metric Card
A metric card should contain:

- One short label
- One strong value
- One delta or interpretation

Metric cards should never become mini articles.

### Signal Chip
Signal chips communicate analytical state:

- Positive
- Negative
- Watch
- Informational

They should be used consistently across TR funds, stock research and macro dashboards.

### Data Table
Tables should prioritize:

- sortable comparisons
- visible hierarchy
- compact row height
- stable alignment for numbers

Avoid decorative zebra striping that lowers legibility.

### Chart Frame
Charts must be purposeful. Every chart should answer one question.

Preferred default charts:

- line chart for trend
- bar chart for ranking
- area chart for cumulative flow

Avoid multi-axis novelty charts on the first screen.

## Do's and Don'ts
### Do

- Design for fast morning market orientation.
- Make the first screen useful before any API-heavy modules load.
- Use color to communicate state, not decoration.
- Keep the UI feeling like a professional intelligence tool.
- Preserve enough whitespace to prevent financial data from collapsing into noise.

### Don't

- Don’t render every tab, chart and module at once.
- Don’t use bright gradients inside data tables or deep analysis panels.
- Don’t mix too many accent colors.
- Don’t make the landing page feel like a generic SaaS homepage.
- Don’t hide the strongest signal below the fold.
