# Spec: Add Expense

## Overview
This feature allows authenticated users to record new expenses. It provides a dedicated form page to input the amount, category, date, and an optional description. This is the core "Write" functionality of the app, moving beyond the previous read-only profile and expense list views.

## Depends on
- Step 02: Registration
- Step 03: Login and Logout
- Step 01: Database Setup (via `init_db` and `expenses` table)

## Routes
- `GET /expenses/add` — Renders the "Add Expense" form. Access: Logged-in.
- `POST /expenses/add` — Processes the form submission, validates input, inserts the expense into the database, and redirects the user. Access: Logged-in.

## Database changes
No database changes. The `expenses` table already exists with the required columns: `user_id`, `amount`, `category`, `date`, and `description`.

## Templates
- **Create:** `templates/add_expense.html` — A form page following the app's design system.
- **Modify:** No modifications to existing templates.

## Files to change
- `app.py` — Implement the GET and POST handlers for `/expenses/add`.
- `database/db.py` — Add a helper function `add_expense(user_id, amount, category, date, description)` to handle the database insertion.

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not applicable here, but a general project rule)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- **Validation**: 
    - `amount` must be a positive number.
    - `category` must not be empty.
    - `date` must be a valid ISO date.
    - If validation fails, re-render the form with an `error` context variable.

## Definition of done
- [ ] Signed-out users are redirected to `/login` when visiting `/expenses/add`.
- [ ] Logged-in users can successfully submit an expense.
- [ ] The expense is correctly stored in the database with the current user's `user_id`.
- [ ] Form submission with invalid data (e.g., negative amount, empty category) shows an error message and does not save the data.
- [ ] After successful submission, the user is redirected to the profile or expenses list page.
