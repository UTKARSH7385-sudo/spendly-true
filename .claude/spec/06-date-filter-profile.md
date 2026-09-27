# Spec: Date and Filter for Profile Page

## Overview
Currently, the profile page shows an expense summary for the current month only. This feature extends that functionality by allowing users to filter their expense summary by a specific date range (Start Date and End Date). This provides users with a more flexible way to analyze their spending patterns over custom periods rather than being locked into the current calendar month.

## Depends on
- Step 04: Profile Page (Implemented)
- Step 05: List Expenses for Logged-in User (Implemented)

## Routes
- `GET /profile` — Modify to handle optional `start_date` and `end_date` query parameters. If provided, use them to filter the summary; otherwise, default to the current month. — access level (logged-in)

## Database changes
No database changes. Existing `expenses` table has the `date` column required for filtering.

## Templates
- **Modify:** `templates/profile.html` — Add a filter form (GET) with `start_date` and `end_date` inputs and a "Filter" button. Display the selected date range if active.

## Files to change
- `app.py` — Update `/profile` route to extract query parameters and pass them to the DB helper.
- `database/db.py` — Update `get_expense_summary` to accept optional date boundaries.
- `templates/profile.html` — Add the filter UI.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `datetime.date.fromisoformat()` or similar to validate that provided dates are valid ISO strings before passing them to SQL.
- Default behavior (when no dates are provided) must remain as "current month".

## Definition of done
- [ ] User can navigate to `/profile` and see the current month's summary by default.
- [ ] User can enter a start date and end date, click "Filter", and see the summary for that specific range.
- [ ] The URL updates to include `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`.
- [ ] Providing an invalid date format does not crash the server (handled gracefully, e.g., falling back to default or showing an error).
- [ ] Clicking a "Clear" or "Reset" button returns the view to the current month's summary.
