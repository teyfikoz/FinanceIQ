# FundPortal Frontend Migration Plan

## Short Answer
FundPortal does not need a React or Java rewrite right now.

The current highest-value path is:

1. keep the data and logic core in Python
2. improve Streamlit rendering discipline
3. reduce hidden UI work
4. standardize the design system

Only after that should a custom frontend be considered.

## When a React Frontend Becomes Worth It
Move to React or Next.js when at least two of these become true:

- you need truly instant client-side transitions
- you need public marketing pages plus authenticated product pages
- you need better mobile interaction than Streamlit can comfortably provide
- you need component-level analytics, consent flows or ad inventory control
- you need a stronger long-term SaaS frontend shell

## Recommended Future Stack
If FundPortal outgrows Streamlit, the most practical architecture is:

- frontend: Next.js
- design system: Tailwind + Radix UI or shadcn/ui
- charts: lightweight-charts, Recharts, ECharts or selective Plotly
- backend API: FastAPI
- async jobs: Celery or Dramatiq
- data cache: Redis
- auth/billing later: Clerk or Auth.js + Stripe

## Migration Shape
### Phase 1

- keep current Python analytics
- expose selected views through FastAPI endpoints
- build a lightweight React shell for landing, navigation and fast page transitions

### Phase 2

- move the most used screens first:
  - Dashboard
  - Stock Research
  - Turkish Markets

### Phase 3

- keep niche research and experimental modules in Streamlit behind an internal or lab route
- keep the public product on the React frontend

## Why Not Java
Java is not the right acceleration path for this product.

It would add engineering weight without solving the immediate UX problem. The bottleneck is interaction architecture and rendering behavior, not language runtime choice.

## Current Recommendation
Stay with Python + Streamlit for now, but structure the UI as if a React migration may happen later.

That means:

- clear page boundaries
- isolated rendering blocks
- reusable UI sections
- API-friendly data functions
- stable design tokens in `DESIGN.md`
