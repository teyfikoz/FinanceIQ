# FundPortal UI Redesign Plan

## Verdict
Yes, the app needs a better design system. No, a visual redesign alone will not fix the current complaint.

The current complaint is speed first, design second.

That means the order should be:

1. Reduce first-load work.
2. Simplify the interaction model.
3. Apply a stronger visual system.
4. Optionally use Stitch for rapid exploration once the design language is defined.

## Why Stitch Is Useful
Google Stitch is useful for:

- rapid concept generation
- alternative landing-page directions
- quick dashboard layout exploration
- turning a design system into multiple UI variants

Recent Google Labs updates describe Stitch as an AI-native design canvas with support for design systems and `DESIGN.md` import/export. That makes it a good ideation tool for FundPortal, but not the source of truth for the product.

For FundPortal, the source of truth should be:

- `DESIGN.md` for the visual system
- the app code for performance-conscious implementation

## Why Stitch Is Not the First Fix
FundPortal was slow because too much work was happening in the UI at once:

- hidden views were still rendering
- heavy charting created frontend noise
- several data modules were expensive on first interaction

If we redesign the visuals without protecting render cost, we will end up with a prettier slow app.

## Recommended Design Direction
Name: `Editorial Market Desk`

Core traits:

- premium analyst workstation
- high signal density with calm visual hierarchy
- serious, credible, non-gimmicky
- light theme by default with deep-ink hero surfaces
- teal accent, not generic blue-purple SaaS styling

Primary user promise:

- "See what matters now in 10 seconds."

## Recommended Screen Structure
### 1. Landing / Morning Brief

Purpose:

- instant market orientation
- top TR fund signal
- top stock setup
- one recommended route

Should include:

- today’s setup
- top pick
- one mini trend chart
- one ranked list

Should not include:

- every chart
- deep configuration panels
- low-priority modules

### 2. Stock Research

Purpose:

- focused single-instrument work

Should include:

- one compact control bar
- one active view selector
- overview first
- technical, fundamentals, settlement and sector as separate active views

### 3. Turkish Markets

Purpose:

- TEFAS and BIST differentiation

Should include:

- peer board
- allocation drift
- investor momentum
- top pick and under-pressure summaries

### 4. Institutional / AI

Purpose:

- slower, deeper analysis

Should be clearly separated from the first-screen flow.

## Implementation Priorities
### P0

- keep one active analysis panel at a time
- reduce landing-page chart count
- lazy-load expensive data modules
- standardize metric cards and section hierarchy

### P1

- rebuild hero and control rail using the `DESIGN.md` system
- unify status chips, ranking cards and section headers
- replace inconsistent chart styling

### P2

- build a stronger premium landing narrative
- add sponsor-safe content slots
- add mobile-specific layout cleanup

## Stitch Prompt
Use this prompt inside Stitch if you want visual explorations:

```text
Design a premium financial intelligence web app called FundPortal.

The product is not a generic SaaS dashboard. It should feel like an editorial market desk for serious investors and analysts. The app needs to communicate trust, speed and signal clarity. Avoid purple gradients, crypto-casino aesthetics and playful startup visuals.

Visual direction:
- Light theme with a warm-cool off-white canvas
- Deep navy hero surfaces
- Teal as the primary accent
- Green, red and amber only for analytical states
- Typography with strong modern headlines and compact data-friendly body text
- Dense but readable layout
- Subtle borders, minimal shadows

Screens to design:
1. Morning Brief landing screen
2. Stock Research screen
3. Turkish Funds Intelligence screen

UX constraints:
- The first screen must answer “what matters now?” in under 10 seconds
- One main analytical surface at a time
- Show metric cards, ranked lists and one meaningful chart, not chart overload
- Make the design feel premium, credible and fast

Target user:
- founder-investor
- active public-market analyst
- Turkish market user who also tracks global context
```

## Codex / Claude Follow-Up Prompt

```text
Use the repository DESIGN.md as the design source of truth.

Refactor the Streamlit UI toward this system without increasing first-load cost.

Requirements:
- one active analysis view at a time
- landing page should render fast and show only highest-value blocks
- use metric cards, signal chips and editorial hierarchy from DESIGN.md
- avoid adding Plotly-heavy views to first paint
- preserve current business logic and data integrations
- improve mobile readability
```

## Security Note
Do not paste account passwords into prompts or chat again. If a password was shared, rotate it before using that account further.
