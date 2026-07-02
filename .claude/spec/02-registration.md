# Spec: Registration (v2 — MVP scope)

## Overview
The Registration feature wires the existing `/register` form to a working POST handler so a new visitor can create a Spendly account. After submitting a name, email, and password, the user's record is persisted to the `users` table with a hashed password, the user is signed in immediately, and they are redirected to their profile page. This unblocks every later step that depends on knowing who the current user is (login/logout, profile, expenses).

**Scope note:** This is an MVP. Items explicitly marked *Out of scope* below are intentionally deferred — they are not oversights.

## Depends on
- **Step 0 (Landing)** — the public marketing page and base layout exist.
- **Step 1 (Database setup)** — `database/db.py` exposes `get_db()` with `PRAGMA foreign_keys = ON`, the `users` table is created by `init_db()`, and `instance/spendly.db` is the configured database.

## Routes
- `GET  /register` — render `register.html` — public. If the visitor is already logged in (`session["user_id"]` set), redirect straight to `/profile` instead of showing the form.
- `POST /register` — validate form, create user, log in, redirect to `/profile` — public

## Database changes
No database changes. The `users` table already has the required columns:

| Column         | Type    | Notes                                     |
|----------------|---------|-------------------------------------------|
| `id`           | INTEGER | PRIMARY KEY AUTOINCREMENT                 |
| `name`         | TEXT    | NOT NULL                                  |
| `email`        | TEXT    | UNIQUE NOT NULL                           |
| `password_hash`| TEXT    | NOT NULL                                  |
| `created_at`   | TEXT    | DEFAULT `datetime('now')`                 |

The existing `UNIQUE` constraint on `email` is the source of truth for duplicate detection (see Rules — race condition handling).

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — the form already posts to `/register`; verify the `{% if error %}` block renders the `error` string inline, styled with the existing `.auth-error` class. No new fields needed for MVP (no "confirm password" field required).

## Files to change
- `app.py` — change the `/register` route to accept both `GET` and `POST`. On `GET`, redirect to `/profile` if already logged in, otherwise render the form. On `POST`, validate input (see Validation order below), call `create_user()`, sign the user in via Flask session, and redirect to `url_for('profile')`. On any validation failure, re-render `register.html` with an `error` context variable and HTTP status `400`.
- `database/db.py` — add:
  - `create_user(name, email, password) -> int` — hashes the password with `werkzeug.security.generate_password_hash`, inserts the row, and returns the new user's `id`. Must catch `sqlite3.IntegrityError` from the `UNIQUE` constraint and re-raise it as a custom `DuplicateEmailError` (or similar) so `app.py` can catch it cleanly instead of a raw `sqlite3` exception.
  - `find_user_by_email(email) -> Row | None` — used only as a fast-path check before insert (UX: avoids a round trip in the common case). It is **not** the sole duplicate-detection mechanism — see race condition rule below.
- `templates/register.html` — no functional change required, but confirm the `error` block still renders correctly.
- `app.py` (config) — set `app.secret_key` from an environment variable with a hardcoded fallback string for local dev only (e.g. `os.environ.get("SECRET_KEY", "dev-only-do-not-use-in-prod")`). Required for `flask.session` to work at all.

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` is already used by `seed_db()` and is part of the existing `requirements.txt`.

## Validation order (deterministic — check top to bottom, stop at first failure)
1. **Missing fields** — `name`, `email`, or `password` empty/absent (after `.strip()`)
2. **Invalid email format**
3. **Password too short** (< 8 chars) or **too long** (> 128 chars)
4. **Duplicate email** (case-insensitive)

Only one error is ever shown at a time — the first one hit in this order.

## Error messages (exact strings — used in `error` context var, rendered by `register.html`)

| Condition                                      | Error message shown to user                                  |
|-------------------------------------------------|----------------------------------------------------------------|
| Missing `name`, `email`, or `password`           | `"All fields are required."`                                   |
| Invalid email format                             | `"Please enter a valid email address."`                        |
| Password shorter than 8 characters               | `"Password must be at least 8 characters long."`                |
| Password longer than 128 characters              | `"Password must be no more than 128 characters long."`          |
| Email already registered                         | `"An account with that email already exists."`                  |
| Unexpected server/DB error                       | Use `flask.abort(500)` — no custom inline error, let the default error page handle it. |

## Rules for implementation
- No SQLAlchemy or any ORM — use raw `sqlite3` via `get_db()`.
- All SQL must be parameterised (`?` placeholders). Never use f-strings or `%` formatting in queries.
- Passwords must be hashed with `werkzeug.security.generate_password_hash` before storage. Plain-text passwords are never written to the database or logs.
- `name` must be `.strip()`-ed before validation and storage; a name that is empty after stripping counts as "missing."
- Email must be normalized with `.lower().strip()` before any comparison, lookup, or insert.
- Email format check: use a simple regex, no external library —
  ```python
  import re
  EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
  ```
- **Race condition handling (required, not optional even for MVP):** `find_user_by_email()` is only a pre-check for a fast, friendly error in the common case. The `email` column's `UNIQUE` constraint is the real guard. `create_user()` must wrap its `INSERT` in `try/except sqlite3.IntegrityError` and translate that into the same "email already exists" error path — otherwise two near-simultaneous submissions with the same email can crash one request with an unhandled 500 instead of showing the proper message.
- Reuse the existing CSS variables from `static/css/style.css` (`--ink`, `--accent`, `--paper`, `.auth-section`, `.auth-error`, etc.) — never hardcode hex values in templates or inline styles.
- `register.html` must keep `{% extends "base.html" %}` and the existing `{% if error %}` block; the new POST handler passes the `error` string in.
- Route logic must stay in `app.py`; all DB writes/reads live in `database/db.py`.
- Use `flask.abort()` for unexpected HTTP errors, not raw string returns.
- After successful registration, the user must be signed in (set `session["user_id"]`) before redirecting to `/profile`.

## Out of scope (deliberately deferred — not bugs)
- CSRF protection on the form (no Flask-WTF / manual token in MVP).
- Rate limiting / bot protection on registration.
- Email verification (confirm the email address is real/reachable).
- "Confirm password" field / password strength meter.
- Password reset / forgot-password flow.
- These should be revisited before any real/public deployment beyond local dev or demo use.

## Definition of done
- [ ] `app.secret_key` is set (env var with a dev-only fallback) so `flask.session` works.
- [ ] `GET /register` renders the form when logged out, and redirects to `/profile` when already logged in.
- [ ] `POST /register` with valid `name`, `email`, `password` creates a row in `users` with a hashed password (not the plaintext) and redirects to `/profile`.
- [ ] After a successful registration, `flask.session["user_id"]` equals the new user's id.
- [ ] `POST /register` with an already-registered email re-renders `register.html` (HTTP 400) with `"An account with that email already exists."` and no row is inserted.
- [ ] Two near-simultaneous `POST /register` requests with the same new email — only one succeeds; the other gets the duplicate-email error, not a 500.
- [ ] `POST /register` with a missing `name`, `email`, or `password` re-renders with `"All fields are required."`
- [ ] `POST /register` with an invalid email format re-renders with `"Please enter a valid email address."`
- [ ] `POST /register` with a password shorter than 8 characters re-renders with `"Password must be at least 8 characters long."`
- [ ] `POST /register` with a password longer than 128 characters re-renders with `"Password must be no more than 128 characters long."`
- [ ] All SQL in the new code paths uses `?` placeholders (verify by reading the diff).
- [ ] `pytest` still passes (no existing tests broken).
- [ ] Manually register a new account via the browser, then verify the user appears in `users` with a `password_hash` that does not equal the submitted password.
