---
name: frontend-design-spendly
description: Generates modern, production-ready UI (Jinja2 templates, CSS, minimal JS) for Spendly, a personal expense tracker app (Flask + Jinja2 + vanilla CSS/JS, repo: github.com/UTKARSH7385-sudo/spendly-true). Use this skill whenever the user asks to design, create, build, redesign, or improve any page or component for Spendly, even if they don't say "UI" explicitly — e.g. "design the dashboard page", "create UI for adding an expense", "build a component for the budget summary", "redesign the profile page", "improve the login form". Always trigger for any Spendly-related page/screen/component request, mockup, or layout question.
---

# Frontend Design for Spendly

Generates clean, production-ready UI for Spendly — a personal expense tracker built with **Flask + Jinja2 templates + vanilla CSS/JS** (no React, no Tailwind, no build step). Repo: https://github.com/UTKARSH7385-sudo/spendly-true

## When to trigger

Automatically use this skill when the user says things like:
- "Design the ___ page"
- "Create UI for ___"
- "Build component for ___"
- "Redesign / improve ___"

...especially when ___ relates to Spendly (dashboard, expenses list, add-expense form, budget, categories, profile, reports, etc).

## Inputs to expect

- Page/component name (required)
- Optional: constraints, sample data, reference screenshots, which existing page it sits alongside

If the request is vague ("make it look better"), ask which page and what's currently wrong with it before generating a full rewrite.

## The existing design system (match this — don't invent a new one)

Spendly has a deliberate **warm, editorial "ledger" aesthetic** — not a generic blue/purple SaaS dashboard look. New UI must look like it belongs in the same app as `templates/landing.html` / `templates/base.html` / `static/css/style.css`.

**CSS variables already defined in `:root` (style.css) — reuse these, don't hardcode colors:**

```css
--ink: #0f0f0f;          --paper: #f7f6f3;
--ink-soft: #2d2d2d;     --paper-warm: #f0ede6;
--ink-muted: #6b6b6b;    --paper-card: #ffffff;
--ink-faint: #a0a0a0;    --border: #e4e1da;
--accent: #1a472a;       --border-soft: #eeebe4;
--accent-light: #e8f0eb; --danger: #c0392b;
--accent-2: #c17f24;     --danger-light: #fdecea;
--accent-2-light: #fdf3e3;

--font-display: 'DM Serif Display', Georgia, serif;   /* headings */
--font-body: 'DM Sans', system-ui, sans-serif;        /* everything else */

--radius-sm: 6px;  --radius-md: 12px;  --radius-lg: 20px;
--max-width: 1200px;  --auth-width: 440px;
```

**Existing reusable classes — reach for these before writing new CSS:**
- `.btn-primary` / `.btn-ghost` / `.btn-submit` / `.btn-pill` — buttons
- `.auth-card` / `.paper-card` — card containers (white card on warm paper bg)
- `.form-group`, `.form-input`, `label` inside `.form-group` — form fields
- `.auth-error` — inline error banner (danger colors)
- `.auth-switch` — small helper links under a form
- `.navbar` / `.nav-inner` / `.nav-brand` / `.nav-links` — nav, already in `base.html`, don't recreate it

**Visual character:**
- Serif (`DM Serif Display`) for page titles / section headings, sans (`DM Sans`) for body and UI chrome
- Warm paper background (`--paper`), white cards (`--paper-card`) with a thin `--border`, soft radii — not stark white, not heavy shadows
- Deep green (`--accent`) as primary accent, mustard (`--accent-2`) as secondary accent, used sparingly
- Generous whitespace, calm hierarchy — this is a "ledger," not a busy dashboard

## Icons: use Lucide

The repo has no icon library installed yet. For all new UI, add Lucide via CDN in the page's `{% block scripts %}` (or `{% block head %}` if needed before render):

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<script>lucide.createIcons();</script>
```

Use `<i data-lucide="icon-name"></i>` inline. Pick icons that fit a finance app (e.g. `wallet`, `receipt`, `pie-chart`, `trending-up`, `plus-circle`, `credit-card`) — don't use decorative/unrelated icons. Keep the existing `◈` glyph as the Spendly brand mark; Lucide is for new functional icons only, not a brand-icon replacement.

## Output format

Structure every response as:

1. **UI structure (brief)** — layout, key sections, and the important UX decisions in a few bullet points. Not a wall of text.
2. **Code** — a Jinja2 template (extending `base.html` via `{% block content %}`), any new CSS appended to `static/css/style.css` conventions (or noted as a new block within it), and JS only if the page needs interactivity (add to `static/js/main.js` patterns, kept minimal).
3. **Design quality notes** — 1-2 lines on spacing/hierarchy/card usage if there's anything non-obvious to flag.

Code should be clean and modular: small, named CSS classes (not utility-class soup, since there's no Tailwind here), minimal boilerplate, no inline styles except for truly one-off tweaks.

## Design rules

- Minimal, clean, editorial-fintech feel — not generic/dated, not a stock admin-dashboard template
- Rounded corners via the existing radius variables, soft borders over heavy drop-shadows
- Consistent spacing on an 8px-ish rhythm
- Avoid clutter, random one-off colors, or styles that don't use the CSS variables above

## Consistency rule

Always match the existing project design system above. If a request implies a page type that doesn't map cleanly onto the existing patterns (e.g. something highly data-dense like a charts-heavy analytics view), say so and ask for a reference/screenshot rather than guessing a new visual language.

## Avoid

- Generic/dated UI, default browser form styling, unstyled tables
- Introducing a new framework, utility-CSS system, or build step (this is a no-build Flask project)
- Unstructured code dumps without the UI-structure summary up front
- Inventing new colors/fonts instead of using the CSS variables already defined