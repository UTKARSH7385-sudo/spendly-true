# Spec: List Expenses For Logged In User

## Overview
This feature replaces the placeholder phase between Step 4 (profile page) and Step 7 (add expense) with a real, logged-in-only `/expenses` page that lists every expense the current user has recorded. The profile page already shows a *summary* (total, count, top category) but offers no way to see the individual rows behind those numbers — once a user has more than a handful of expenses, the profile page is no longer enough on its own. This step gives the user a real drill-down: a chronological list of their own expenses, with an empty state and a call-to-action that points at the Step 7 stub. Read-only at this stage — editing and deleting are deferred to Steps 8 and 9.

## Depends on
- **Step 4 — Profile Page** — the `get_expense_summary(user_id)` helper establishes the conventions this page reuses (queries scoped to `session["user_id"]`, queries that handle "no rows" without raising), and the "Add expense" button on `profile.html` becomes a real link target here.
- **Step 2 — Registration** — the `users` table and the `session["user_id"]` convention.
- **Step 1 — Database Setup** — the `expenses` table (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`), `get_db()` with `PRAGMA foreign_keys = ON`.
- **Step 3 — Login and Logout** — the navbar layout that toggles `Profile` / `Sign out` when signed in (this page reuses that pattern).

## Routes
- `GET /expenses` — list every expense belonging to the current user, newest first, paginated or capped at a sensible default — access level: **logged-in only**. If the visitor is not signed in, redirect to `/login`. If the user has zero expenses, render an empty state with a call-to-action linking to `/expenses/add` (the Step 7 stub). This is a **new** route — it does not collide with any existing `/expenses/<id>/edit` or `/expenses/<id>/delete` URL.

  No POST handler is required at this step — the page is read-only. Steps 7–9 will add the `POST` handlers for create/update/delete.

## Database changes
No database changes. The `expenses` table already exists from Step 1 with all columns this page needs.

| Column | Source | Used for |
|---|---|---|
| `expenses.id` | `expenses` table | primary key (foundation for Steps 8/9 edit links) |
| `expenses.amount` | `expenses` table | "Amount" column on the list |
| `expenses.category` | `expenses` table | "Category" column on the list |
| `expenses.date` | `expenses` table | "Date" column on the list |
| `expenses.description` | `expenses` table | "Note" column on the list (may be empty) |
| `expenses.user_id` | `expenses` table | `WHERE` clause to scope rows to the logged-in user |

The `password_hash` column on `users` is **never** queried here — this page does not load the user row at all, only the session's `user_id`.

## Templates
- **Create:** `templates/expenses.html` — new template, extends `base.html`, overrides `{% block content %}` and `{% block title %}`. Sections:
  1. **Header** — a single H1 like "Your expenses" and a one-line subtitle ("{count} recorded · ₹{total} total"). When the user has zero expenses, the header is unchanged but the subtitle shows "0 recorded · ₹0.00 total".
  2. **List** — a `<table>` (or stacked card layout on narrow screens) with columns: `Date`, `Category`, `Note`, `Amount`. Sorted by `date DESC, id DESC` (newest first; `id` tie-break keeps the order stable when two expenses share a date). Amount is right-aligned and rendered with the `₹` prefix and two decimals, matching the profile page.
  3. **Empty state** — when the user has zero expenses, render a friendly message ("You haven't logged any expenses yet.") and a primary button linking to `url_for("add_expense")`. The button text and target match the existing `profile.html` "Add expense" CTA so the two pages feel consistent.
  4. **Footer action** — a single primary button at the bottom of the list "Add expense" pointing at `url_for("add_expense")`. Only shown when the list is non-empty (the empty state already has its own CTA).

- **Modify: `templates/base.html`** — no change. The session-aware navbar already shows `Profile` / `Sign out` to signed-in users, which is exactly what this page needs.

- **Modify: `templates/profile.html`** — add a small "See all expenses" link below the existing "Add expense" / "Sign out" actions, pointing at `url_for("expenses")`. This is a one-line addition so the profile page has a real link to the new page. The primary "Add expense" CTA stays unchanged.

- **Modify: `static/css/style.css`** — only if a layout class for the list is genuinely missing. The page should reuse `.profile-section` / `.profile-container` / `.profile-card` where it makes sense, plus existing `.btn-primary` / `.btn-ghost` / `.btn-pill` for actions. If a new class is unavoidable (e.g. `.expenses-table`, `.expense-row`, `.expense-empty`), define it in `style.css` using existing CSS variables (`--ink`, `--accent`, `--paper`, `--accent-2`, `--line`, etc.) — never hardcode hex values.

## Files to change
- `app.py` — add a new `/expenses` route. The handler:
  1. Reads `session.get("user_id")`. If it is `None`, redirect to `url_for("login")` and return.
  2. Calls a new `database/db.py` helper to load the user's expenses (newest first).
  3. Calls `get_expense_summary(user_id)` (already exists from Step 4) to populate the header subtitle.
  4. Renders `expenses.html` with both, returning HTTP 200.
  Register the new route **above** the placeholder `/expenses/...` routes so the static `/expenses` path is matched first by Flask's routing (Flask matches by exact path before falling through to converters, so the order is for human readability more than correctness, but keep the dedicated route grouped near the auth routes).
- `database/db.py` — add one new helper:
  - `list_expenses_for_user(user_id, limit=50) -> list[sqlite3.Row]` — returns the user's expenses, sorted by `date DESC, id DESC`, capped at `limit` rows (default 50). Returns an empty list (not `None`) when the user has no rows, so the template can iterate without a guard. The `limit` parameter is a thin defence against a runaway result set for a heavy user; pagination is **out of scope** at this step — if a user has more than 50 expenses, the page still shows the most recent 50, and a TODO note about pagination is acceptable in the route docstring.
- `templates/profile.html` — add a "See all expenses" link below the existing action buttons.
- `static/css/style.css` — only if a new class is needed; default is "no change".

## Files to create
- `templates/expenses.html` — new template.

No other new files.

## New dependencies
No new dependencies. All needed modules (`sqlite3`, `datetime`, `flask.session`, `flask.redirect`, `flask.render_template`, `flask.url_for`) are already in use or in the standard library.

## Rules for implementation
- No SQLAlchemy or any ORM — use raw `sqlite3` via `get_db()`.
- All SQL must use parameterised queries (`?` placeholders). Never use f-strings or `%` formatting in queries.
- Route functions stay one-responsibility: load via a `db.py` helper, hand the data to the template, done. **No SQL in `app.py` route bodies.**
- The `/expenses` handler must check `session.get("user_id")` first thing and redirect to `/login` if it is `None` — there must be no code path that can render the page for an unauthenticated user.
- The `list_expenses_for_user` helper must scope rows to `user_id` via `WHERE user_id = ?` — never return rows belonging to other users. This is the most important security rule on the page; an unparameterised query or a missing `WHERE` clause would silently leak another user's expenses.
- `list_expenses_for_user` must never raise when the user has zero expenses — return an empty list. Do not let the template iterate `None`.
- Sort by `date DESC, id DESC` so the most recent expense appears first. The `id DESC` tie-break keeps the order stable when two expenses share a date.
- Default `limit` is 50. The function signature must accept `limit` as a keyword argument so tests can override it.
- The handler must not load the full `users` row — only the session's `user_id` is needed. If you find yourself reaching for `find_user_by_id` here, stop and re-read the Rules — the page does not need the user's name or email.
- Reuse CSS variables (`--ink`, `--accent`, `--paper`, `--accent-2`, `--line`) and existing utility classes. Never hardcode hex values in templates or inline styles.
- `expenses.html` must `{% extends "base.html" %}` and override `{% block content %}`. It must set `{% block title %}` to something like `Your expenses — Spendly`.
- All internal links must use `url_for(...)` — never hardcode `/expenses`, `/expenses/add`, `/login`, `/logout`, etc.
- Currency formatting on this page: reuse the same `₹` prefix and `%.2f` formatting as the profile page (`₹18,240.00`). The header subtitle may use the same format.
- Dates displayed in the template must be formatted in the template (e.g. `{{ row["date"] }}` renders the raw `YYYY-MM-DD`; for a human-friendly form, use a small `[:10]` slice or a Jinja filter) — do not pre-format in the route.
- The empty state must render even when the user is logged in but has zero expenses — `list_expenses_for_user` returning `[]` is the trigger, not `session` being unset.
- The handler must `return render_template(...)` (HTTP 200) for the happy path. Never return raw strings from a route that has been implemented.

## Out of scope (deliberately deferred — not bugs)
- Editing or deleting an expense (Steps 8 and 9).
- Creating an expense (Step 7 — the link target still renders the stub "Add expense — coming in Step 7" page, which is acceptable).
- Pagination — the page caps at 50 rows for now; a "next page" / page-number control is a later step.
- Filtering by category or date range.
- Sorting controls (e.g. "sort by amount") — the order is fixed at `date DESC, id DESC`.
- Searching expenses by description text.
- A per-month or per-category breakdown — the profile page already shows the current-month summary.
- Exporting to CSV.
- These should be revisited before any real/public deployment beyond local dev or demo use.

## Definition of done
- [ ] `GET /expenses` while **not** signed in redirects to `/login` and never queries the `expenses` table.
- [ ] `GET /expenses` while signed in renders `expenses.html` with HTTP 200.
- [ ] For a user with N expenses (N ≤ 50), the page shows N rows in `date DESC, id DESC` order with columns `Date`, `Category`, `Note`, `Amount`.
- [ ] For a user with N expenses where N > 50, the page shows the most recent 50 rows in the same order — no template crash, no infinite loop.
- [ ] For a user with **zero** expenses, the page renders the empty state with the "Add expense" CTA pointing at `url_for("add_expense")` and the header subtitle shows `0 recorded · ₹0.00 total`.
- [ ] The header subtitle shows the user's correct count and total (e.g. `8 recorded · ₹254.93 total` for the seeded demo user).
- [ ] The amounts column is right-aligned and uses the `₹` prefix with two decimals, matching the profile page.
- [ ] The "Add expense" footer button (list-non-empty case) and the empty-state CTA both link to `url_for("add_expense")` — never hardcode `/expenses/add`.
- [ ] `list_expenses_for_user(session["user_id"])` returns only that user's rows — never another user's. Verify by SQL inspection of the `WHERE` clause.
- [ ] `list_expenses_for_user(user_id)` returns an empty list (not `None`) when the user has no rows, so the template can `{% for row in expenses %}` without a guard.
- [ ] All SQL in the new code paths uses `?` placeholders (verify by reading the diff).
- [ ] No SQL appears in `app.py` — the `/expenses` route only calls `db.py` helpers, then renders the template.
- [ ] `password_hash` does not appear anywhere in the rendered HTML, the Jinja context dict, or any logged response.
- [ ] All templates use `{% extends "base.html" %}` and `{% block content %}`; the new template sets `{% block title %}`.
- [ ] All internal links use `url_for(...)` (verify by grepping the new template for `/login`, `/profile`, `/logout`, `/expenses`, `/expenses/add`, etc.).
- [ ] No new hex values were introduced in `templates/expenses.html` or `static/css/style.css`; new classes (if any) reuse `--*` variables.
- [ ] No new pip packages were added.
- [ ] `pytest` runs the existing test suite without import or collection errors (no tests are required to be added by this step, but the suite must remain runnable).
- [ ] The dev server still runs on port `5001` (not 5000).
- [ ] Manually: log in as the seeded demo user, visit `/expenses`, confirm the 8 seeded expenses appear in newest-first order with the right amounts and categories; visit `/expenses` as a freshly registered user with zero expenses, confirm the empty state renders; log out and visit `/expenses`, confirm a redirect to `/login`.
