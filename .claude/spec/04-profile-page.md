# Spec: Profile Page

## Overview
The Profile Page feature replaces the `/profile` stub with a real, logged-in-only dashboard that shows the current user's account details (name, email, account creation date) and a small summary of their expense activity. It builds on the auth work from Steps 2 and 3 — by the time this step runs, the user is identifiable via `session["user_id"]`. The page is the destination for both successful registration and successful login, so it has to be ready the moment either of those flows redirects to it. It also serves as the home base from which a user can reach the upcoming expense CRUD (Steps 7–9).

**Scope note:** This is an MVP. Editing the profile (name, email, password) is explicitly deferred to a later step — Step 4 is **read-only**. Items marked *Out of scope* below are deliberate deferrals, not oversights.

## Depends on
- **Step 2 — Registration** — the `users` table, the `create_user` / `find_user_by_email` helpers in `database/db.py`, and the `session["user_id"]` convention.
- **Step 3 — Login and Logout** — the working `verify_password` helper (for any future "delete account" flow, even if deferred), the navbar pattern that toggles `Profile` / `Sign out` based on session, and the session-clearing logout.
- **Step 1 — Database setup** — `get_db()` with `PRAGMA foreign_keys = ON`, the `expenses` table.

## Routes
- `GET /profile` — render `profile.html` with the current user's account info and a small expense summary — access level: **logged-in only**. If the visitor is not signed in, redirect to `/login` (with a hint that they were sent there because they need to sign in). This replaces the existing Step 4 stub.

No new routes beyond replacing the stub.

## Database changes
No database changes. The `users` table already has the required columns (`id`, `name`, `email`, `created_at`) and the `expenses` table is already present from Step 1.

| Column (read-only) | Source            | Used for                          |
|--------------------|-------------------|-----------------------------------|
| `users.id`         | `users` table     | match against `session["user_id"]` |
| `users.name`       | `users` table     | greeting on the profile page      |
| `users.email`      | `users` table     | display in the account details    |
| `users.created_at` | `users` table     | "Member since" line               |
| `expenses` (count, sum) | `expenses` table | summary tiles (total spent, transaction count, top category) |

The `password_hash` column is **never** sent to the template — it must not appear anywhere in the rendered HTML, the context dict, or the response body.

## Templates
- **Create:** `templates/profile.html` — new template, extends `base.html`, overrides `{% block content %}` and `{% block title %}`. Sections:
  1. **Header / greeting** — "Hi, {name}." in a large display heading, plus a one-line subtitle ("Here's a snapshot of your spending.").
  2. **Account details card** — a small card showing email and "Member since {month year}" pulled from `users.created_at` (formatted in the template, not the route).
  3. **Expense summary tiles** — three or four KPI tiles reusing the existing `.kpi-tile` / `.kpi-label` / `.kpi-value` classes from `static/css/style.css` (already used on `landing.html`):
     - **Total spent** — sum of `expenses.amount` for this user (all time, or current month — pick one and document it; recommendation: current month, matching the landing-page demo).
     - **Transactions** — `COUNT(*)` of expenses for this user (same period as Total spent).
     - **Top category** — the category with the highest total spend in the same period, or "—" if the user has no expenses yet.
     - (Optional, if a 4th tile helps layout) **This month vs last** — same period comparison, like the landing demo. Skip if the data is awkward without backfill.
  4. **Quick actions** — a primary button linking to `url_for("add_expense")` (Step 7 stub — link will 404 until Step 7 ships; that's acceptable) and a secondary "Sign out" link to `url_for("logout")`.

- **Modify: `templates/base.html`** — no change. The `{% if session.get("user_id") %}` block already shows `Profile` / `Sign out` when signed in, which is exactly what we need. Step 4 does **not** add new navbar items.

- **Modify: `static/css/style.css`** — only if a layout class for the profile page is genuinely missing. Strongly prefer reusing the existing `.auth-section`, `.auth-card`, `.kpi-tile`, `.btn-primary`, `.btn-ghost`, `.btn-pill` classes. If a new class is unavoidable, define it in `style.css` using existing CSS variables (`--ink`, `--accent`, `--paper`, `--accent-2`, etc.) — never hardcode hex values.

## Files to change
- `app.py` — replace the `/profile` stub with a real `GET` handler that:
  1. Reads `session.get("user_id")`. If it is `None`, redirect to `url_for("login")` and return.
  2. Calls a new `database/db.py` helper to load the user row by id.
  3. Calls a new `database/db.py` helper to load the expense summary (count, sum, top category) for the current month (or all time — see recommendation above).
  4. Renders `profile.html` with the data, returning HTTP 200.
- `database/db.py` — add two helpers:
  - `find_user_by_id(user_id) -> sqlite3.Row | None` — looks up a user by primary key. Returns `None` if the row does not exist (defensive — the session could in theory reference a deleted user). This is **not** the duplicate-detection helper from Step 2; that one is `find_user_by_email`.
  - `get_expense_summary(user_id) -> dict` — returns a dict with at least:
    - `"total": float` (sum of `amount` for the user's expenses in the current month — 0.0 if none)
    - `"count": int` (`COUNT(*)` for the same period — 0 if none)
    - `"top_category": str | None` (the category with the highest total spend in the same period, or `None` if no expenses)
    - The keys must be present even when the user has no expenses, so the template can render "₹0" / "0" / "—" without conditionals on the data shape.
- `templates/profile.html` — new file (see Templates above).
- `static/css/style.css` — only if a genuinely new class is required (see Templates above). The default is "no change".

## Files to create
- `templates/profile.html` — new profile page template.

No other new files.

## New dependencies
No new dependencies. All needed modules (`sqlite3`, `werkzeug.security`, `flask.session`, `flask.redirect`, `flask.render_template`, `flask.url_for`) are already in use or in the standard library.

## Rules for implementation
- No SQLAlchemy or any ORM — use raw `sqlite3` via `get_db()`.
- All SQL must use parameterised queries (`?` placeholders). Never use f-strings or `%` formatting in queries.
- Route functions stay one-responsibility: load via a `db.py` helper, hand the data to the template, done. **No SQL in `app.py` route bodies.**
- The `/profile` handler must check `session.get("user_id")` first thing and redirect to `/login` if it is `None` — there must be no code path that can render the page for an unauthenticated user.
- **Never** pass `password_hash` (or any column not strictly needed for display) to the template. Build the context dict with only the fields the template uses.
- The "current month" boundary for the expense summary must be computed in Python (e.g. `datetime.date.today().replace(day=1)`), not in SQL, so the SQL stays portable and the date logic is easy to test.
- Top-category query: order by `SUM(amount) DESC LIMIT 1` over a `GROUP BY category`. If two categories tie, either is fine — pick deterministically with a secondary `ORDER BY category ASC` so the result is stable across runs.
- Dates displayed in the template must be formatted in the template (e.g. `{{ user.created_at[:10] }}` for the raw YYYY-MM-DD, or use a small filter) — do not pre-format in the route. `created_at` from `sqlite3` is a string by default; the simplest approach is slicing.
- Currency formatting on the profile page: reuse the same `₹` prefix and formatting as the landing-page demo (`₹18,240`). If a small helper is needed, define a Jinja filter in `app.py` — but a plain `₹{{ "%.2f"|format(total) }}` is fine for MVP.
- Reuse CSS variables (`--ink`, `--accent`, `--paper`, `--accent-2`) and existing utility classes. Never hardcode hex values in templates or inline styles.
- `profile.html` must `{% extends "base.html" %}` and override `{% block content %}`. It must set `{% block title %}` to something like `Your profile — Spendly`.
- All internal links must use `url_for(...)` — never hardcode `/login`, `/logout`, `/profile`, `/expenses/add`, etc.
- If the `find_user_by_id` helper returns `None` (defensive case: the user was deleted but a stale session still has the id), clear the session and redirect to `/login`. Do not crash with a 500.

## Out of scope (deliberately deferred — not bugs)
- Editing the profile (change name, change email, change password, delete account).
- A profile photo / avatar.
- "Last sign in" timestamp.
- Email verification status / "confirm your email" banner.
- Per-month trend chart (the landing page already shows a static mock — a real chart belongs in a later step).
- These should be revisited before any real/public deployment beyond local dev or demo use.

## Definition of done
- [ ] `GET /profile` while **not** signed in redirects to `/login` (no profile data is rendered, no DB query is made for the expense summary).
- [ ] `GET /profile` while signed in renders `profile.html` with HTTP 200, showing:
  - the user's name in the greeting,
  - the user's email in the account details card,
  - a "Member since" line using `users.created_at`,
  - three summary tiles (Total spent, Transactions, Top category) sourced from `get_expense_summary()`.
- [ ] A user with **zero** expenses sees `₹0.00`, `0`, and `—` for the three tiles (no template crash, no `NoneType` errors).
- [ ] `password_hash` does not appear anywhere in the rendered HTML, the Jinja context dict, or any logged response.
- [ ] All SQL in the new code paths uses `?` placeholders (verify by reading the diff).
- [ ] No SQL appears in `app.py` — the `/profile` route only calls `db.py` helpers, then renders the template.
- [ ] `find_user_by_id(user_id)` returns a `sqlite3.Row` for an existing user and `None` for a missing one.
- [ ] `get_expense_summary(user_id)` returns a dict with the keys `total`, `count`, `top_category` even when there are no expenses.
- [ ] The "current month" boundary is computed in Python, not in SQL.
- [ ] All templates use `{% extends "base.html" %}` and `{% block content %}`; the new template sets `{% block title %}`.
- [ ] All internal links use `url_for(...)` (verify by grepping the new template for `/login`, `/profile`, `/logout`, etc.).
- [ ] No new hex values were introduced in `templates/profile.html` or `static/css/style.css`; new classes (if any) reuse `--*` variables.
- [ ] No new pip packages were added.
- [ ] `pytest` runs the existing test suite without import or collection errors (no tests are required to be added by this step, but the suite must remain runnable).
- [ ] The dev server still runs on port `5001` (not 5000).
- [ ] Manually: register a new user, log in, land on `/profile`, confirm the name/email/created-at are correct, log out, confirm `/profile` redirects to `/login`.
