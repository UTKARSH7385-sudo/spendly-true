# Spec: Login and Logout

## Overview
This feature implements authentication sessions for Spendly: a real
`/login` POST handler that verifies a user's email and password and
signs them in, plus a working `/logout` endpoint that clears the
session and redirects back to the public landing page. It builds on
the existing registration flow (Step 2), which already writes hashed
credentials to the `users` table and sets `session["user_id"]`. After
this step, registered users can sign in from any device, sign out
cleanly, and have their session state persist across pages until
explicit logout.

## Depends on
- **Step 2 — Registration**: the `users` table, the `create_user` /
  `find_user_by_email` helpers in `database/db.py`, the
  `werkzeug.security` hashing used at registration, and the
  `session["user_id"]` convention set after a successful registration.
- **Step 1 / Database Setup**: the SQLite connection helpers
  (`get_db`, `PRAGMA foreign_keys = ON`) used by `find_user_by_email`.

## Routes
- `POST /login` — verify email + password, sign the user in by
  setting `session["user_id"]`, redirect to `/profile`. Re-render
  `login.html` with an inline error on failure. Access level: public.
- `GET /login` — already exists; keep rendering `login.html`. If the
  visitor is already signed in, redirect to `/profile` (matches the
  `/register` guard). Access level: public.
- `GET /logout` — clear the session (`session.clear()`), redirect to
  the landing page (`url_for("landing")`). Access level: public
  (logged-in or not, the result is "you are signed out").

## Database changes
No database changes. The `users` table already has `email` (UNIQUE)
and `password_hash` (werkzeug-hashed) — both are sufficient to verify
a login.

## Templates
- **Modify: `templates/base.html`** — when `session.get("user_id")`
  is set, the navbar's right-hand links should switch from
  `Sign in` / `Get started` to `Profile` / `Sign out`. Use a single
  `{% if %}` block inside `.nav-links`. `Sign out` is a plain link
  (not a button) pointing at `url_for("logout")`.
- **Modify: `templates/login.html`** — the form already POSTs to
  `/login` and already renders `{{ error }}` if present. No HTML
  changes are required; only the route handler that backs the form
  changes.
- No new templates.

## Files to change
- `app.py` — convert `/login` to a `GET, POST` handler; replace the
  `/logout` stub with a real implementation that clears the session
  and redirects to the landing page.
- `database/db.py` — add a single new helper,
  `verify_password(email, password) -> sqlite3.Row | None`, that
  looks up the user by email and returns the row only if
  `check_password_hash` confirms the password. Returns `None` for
  unknown email OR wrong password (do not leak which one failed).
- `templates/base.html` — swap the navbar links based on session
  state.

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` (`check_password_hash`) is
already used in `database/db.py` for password hashing and is part of
`werkzeug`, which is already pinned in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs — keep using raw `sqlite3` with `?`
  placeholders.
- All SQL must use parameterised queries — never f-strings in SQL.
- Password verification must use
  `werkzeug.security.check_password_hash(row["password_hash"],
  password)`. Never compare hashes or passwords with `==`.
- Do not leak which credential was wrong: a missing email and a
  wrong password must both render the same generic
  "Invalid email or password." error.
- The `email` field must be normalised before lookup
  (`.strip().lower()`), exactly like `/register` does.
- `/login` GET: if the visitor is already signed in
  (`session.get("user_id") is not None`), redirect to
  `url_for("profile")` — mirrors the `/register` guard.
- `/logout`: call `session.clear()` and `return redirect(url_for("landing"))`.
  Do not return a string from `/logout` once implemented — always
  redirect.
- All templates must `{% extends "base.html" %}` and override
  `{% block content %}`. No raw HTML pages.
- All internal links use `url_for(...)` — never hardcode `/login`,
  `/logout`, `/profile`, etc.
- All styling must use the existing CSS variables in
  `static/css/style.css`. Do not introduce new hex values; if a new
  visual state is needed (e.g. a "signed in" navbar style), reuse an
  existing utility class or extend the design system in
  `style.css` using the same `--*` variables.
- Route functions stay one-responsibility: fetch via a `db.py`
  helper, set/clear the session, redirect or render. No SQL inside
  `app.py` route bodies.
- Failed logins should return `200` (re-render the form with the
  error) so the form is interactive — not `400` like `/register`,
  which uses `400` to surface a validation error. The page is
  semantically the same URL and the browser should not warn.

## Definition of done
- [ ] `GET /login` while **not** signed in renders `login.html` with
      no error.
- [ ] `GET /login` while **already** signed in redirects to
      `/profile`.
- [ ] `POST /login` with a known email and the correct password
      sets `session["user_id"]` and redirects to `/profile`.
- [ ] `POST /login` with a known email and the **wrong** password
      re-renders `login.html` with "Invalid email or password." and
      does **not** set `session["user_id"]`.
- [ ] `POST /login` with an **unknown** email re-renders
      `login.html` with the same generic error and does **not** set
      `session["user_id"]`.
- [ ] `POST /login` with empty fields re-renders `login.html` with
      an error and does **not** set `session["user_id"]`.
- [ ] `GET /logout` clears the session (subsequent requests behave
      as a signed-out visitor) and redirects to `/`.
- [ ] After signing in, the navbar shows `Profile` and `Sign out`
      instead of `Sign in` and `Get started`.
- [ ] After signing out, the navbar reverts to `Sign in` and
      `Get started`.
- [ ] The dev server still runs on port `5001` (not 5000).
- [ ] `pytest` runs the existing test suite without import or
      collection errors (no tests are required to be added by this
      step, but the suite must remain runnable).
