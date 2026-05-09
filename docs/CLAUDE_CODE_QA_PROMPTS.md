# Claude Code QA Prompts

These prompts are designed for detailed FundPilot validation after the current redesign and performance refactor.

## 1. Full Product Audit

```text
You are auditing the FundPilot codebase end to end.

Project goals:
- fast first-load Streamlit experience
- premium editorial market-desk UI
- strong Turkish market differentiation
- no obvious broken data flows

Critical context:
- repository contains DESIGN.md; treat it as the visual source of truth
- main application entrypoint is main.py
- app runs as a Streamlit app
- current public product name is FundPilot
- key routes/features are Dashboard, Stock Research, Turkish Markets, Whale Intelligence, AI Tools, Portfolio, Watchlist, Alerts, Privacy

Your job:
1. inspect code for broken imports, dead flows, duplicated logic, hidden performance traps and UI inconsistencies
2. identify the highest-risk runtime failures
3. identify all places where Streamlit renders too much hidden content
4. identify data integrations likely to fail or fallback silently
5. identify mismatches between DESIGN.md and current implementation
6. propose concrete file-level fixes in priority order

Output format:
- Findings first, ordered by severity
- Each finding must include file path and exact reason
- Then give a prioritized fix plan
- Then list residual risks

Use ultrathink. Stay compact but precise.
```

## 2. Performance Regression Audit

```text
Audit FundPilot specifically for Streamlit performance regressions.

Focus only on:
- hidden tabs rendering unnecessarily
- expensive charts on first paint
- duplicate data fetches
- missing cache opportunities
- APIs called during landing load that should be deferred
- large Plotly usage that could be reduced or replaced
- session-state misuse causing reruns

Requirements:
- inspect main.py and all directly imported UI modules
- identify the biggest 10 performance issues
- estimate user-visible impact for each issue
- propose exact code changes

Output:
- top 10 issues
- recommended order of fixes
- quick wins vs deep refactors

Use planmode and ultrathink.
```

## 3. Turkish Markets Validation

```text
Validate FundPilot's Turkish market experience in depth.

Focus on:
- BIST stock symbol normalization
- TRY currency display correctness
- TEFAS summary reliability
- Turkish Markets landing blocks
- TR fund peer board logic
- fallback behavior when TEFAS or Yahoo data is missing

Check for:
- wrong symbol assumptions such as missing .IS suffix
- USD formatting leaking into BIST screens
- empty or misleading synthetic fallback data
- misleading summary cards
- charts that render without meaningful data

Deliver:
- bugs found
- likely user-facing symptoms
- exact files and functions involved
- suggested fixes

Be strict. If something is fragile, call it out.
```

## 4. UI Consistency Review

```text
Review FundPilot UI consistency against DESIGN.md.

You are not redesigning from scratch. You are checking adherence.

Inspect for:
- typography mismatch
- color misuse
- excessive gradients
- inconsistent card styles
- mixed interaction patterns
- sections that still feel like generic dashboard SaaS
- places where the strongest signal is hidden below the fold

Output:
- exact mismatches with DESIGN.md
- highest-value polish improvements
- components that should be standardized

Use compact mode but do not miss details.
```

## 5. Safe Refactor Prompt

```text
Refactor FundPilot toward a faster and cleaner Streamlit architecture.

Constraints:
- preserve existing business logic
- do not remove key features
- prefer one active analytical surface at a time
- prefer lighter native charts where possible
- keep Turkish market differentiation strong
- keep branding aligned with DESIGN.md

Tasks:
1. reduce hidden rendering
2. reduce first-load work
3. standardize navigation
4. standardize metric cards and section wrappers
5. keep changes incremental and reviewable

Before editing:
- inspect current structure
- state the highest-risk files

After editing:
- run relevant static checks
- summarize changed files
- list remaining risks

Use opus, planmode, ultrathink.
```

## 6. Deployment Smoke Test Prompt

```text
Run a deployment-oriented smoke review for FundPilot.

Checklist:
- app boots without import errors
- main.py compiles
- no obvious missing module path issues
- environment variables have sane fallbacks
- public URL and host configuration are coherent
- authentication mode does not break open access
- key pages can render without requiring unavailable secrets

Return:
- pass/fail by category
- exact blockers
- suggested production checks

Use compact mode and be concrete.
```

## 7. Final Release Gate Prompt

```text
You are the final release gate reviewer for FundPilot.

Evaluate whether the app is ready for a serious public-facing beta.

Judge it on:
- perceived speed
- correctness of core finance flows
- credibility of UI
- consistency of branding
- resilience of fallbacks
- clarity of navigation
- production readiness

Output:
- Ship now / Ship with caveats / Do not ship
- strongest reasons
- minimum blocking fixes before launch
- post-launch monitoring recommendations

Be decisive. No vague wording.
```
