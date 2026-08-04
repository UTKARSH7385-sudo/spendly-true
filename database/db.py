import re
import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


# ------------------------------------------------------------------ #
# Exceptions                                                          #
# ------------------------------------------------------------------ #

class DuplicateEmailError(Exception):
    """Raised when an INSERT into users violates the email UNIQUE constraint."""


# Module-level regex — caller may import this from db.py or re-define locally.
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


# ------------------------------------------------------------------ #
# Connection management                                               #
# ------------------------------------------------------------------ #

def get_db() -> sqlite3.Connection:
    """Return a SQLite connection scoped to the current app context."""
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(exception=None) -> None:
    """Close the connection at the end of the request, if open."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ #
# Schema                                                              #
# ------------------------------------------------------------------ #

def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )
    db.commit()


# ------------------------------------------------------------------ #
# Demo data                                                           #
# ------------------------------------------------------------------ #

def create_user(name: str, email: str, password: str) -> int:
    """Insert a new user. Returns the new user's id.

    `name` and `email` must already be normalized by the caller (stripped;
    email lowercased). `password` is the plaintext — it is hashed before
    storage and never written to disk in cleartext.

    The `users.email` UNIQUE constraint is the authoritative guard against
    duplicates; a sqlite3.IntegrityError is translated into DuplicateEmailError
    so callers don't have to know about SQLite specifics (and so two
    near-simultaneous registrations with the same email don't 500).
    """
    db = get_db()
    password_hash = generate_password_hash(password)
    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError(email) from exc
    return cur.lastrowid


def find_user_by_email(email: str) -> sqlite3.Row | None:
    """Return the user row matching `email`, or None.

    Used as a friendly fast-path duplicate check in the registration flow.
    Not a substitute for the UNIQUE constraint in `create_user()`.
    `email` must already be normalized (lowercased, stripped).
    """
    db = get_db()
    return db.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ? LIMIT 1",
        (email,),
    ).fetchone()


def verify_password(email: str, password: str) -> sqlite3.Row | None:
    """Return the user row if email+password match, else None.

    `email` must already be normalised (lowercased, stripped).
    Returns None for both unknown email and wrong password so
    callers render a single generic error and don't leak which
    credential was wrong.
    """
    row = find_user_by_email(email)
    if row is None:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return row


# ------------------------------------------------------------------ #
# Profile helpers                                                     #
# ------------------------------------------------------------------ #

def find_user_by_id(user_id: int) -> sqlite3.Row | None:
    """Return the user row for `user_id`, or None if not found.

    Used by the /profile route to load the logged-in user's account info.
    Defensive: returns None rather than raising so a stale session
    referencing a deleted user does not 500.

    Note: deliberately does not select `password_hash` so that column
    cannot accidentally reach a template.
    """
    db = get_db()
    return db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ? LIMIT 1",
        (user_id,),
    ).fetchone()


def get_expense_summary(user_id: int) -> dict:
    """Return {total, count, top_category} for the current month for `user_id`.

    All three keys are always present. `total=0.0`, `count=0`, and
    `top_category=None` are returned when the user has no expenses in the
    period, so the template can render `₹0.00` / `0` / `—` without
    conditionals on the data shape.

    The "current month" boundary is computed in Python (not SQL) so the
    date logic is portable and easy to test. `expenses.date` is stored as
    an ISO `YYYY-MM-DD` string, so `date >= first_of_month` is a correct
    lexicographic comparison.
    """
    import datetime

    db = get_db()
    first_of_month = datetime.date.today().replace(day=1).isoformat()

    row = db.execute(
        "SELECT COALESCE(SUM(amount), 0.0) AS total, "
        "COUNT(*) AS count "
        "FROM expenses WHERE user_id = ? AND date >= ?",
        (user_id, first_of_month),
    ).fetchone()

    top = db.execute(
        "SELECT category FROM expenses "
        "WHERE user_id = ? AND date >= ? "
        "GROUP BY category "
        "ORDER BY SUM(amount) DESC, category ASC LIMIT 1",
        (user_id, first_of_month),
    ).fetchone()

    return {
        "total": float(row["total"]),
        "count": int(row["count"]),
        "top_category": top["category"] if top else None,
    }


def list_expenses_for_user(user_id: int, limit: int = 50) -> list[sqlite3.Row]:
    """Return the user's expenses, newest first, capped at `limit` rows.

    Scoped strictly to `user_id` — never returns rows belonging to other
    users. Returns an empty list (not None) when the user has no rows,
    so the template can iterate without a guard.

    Sort order is `date DESC, id DESC`: newest date first, with `id DESC`
    as a stable tie-break when two expenses share a date. Pagination is
    out of scope at this step; the `limit` keyword exists as a thin
    defence against runaway result sets for heavy users.
    """
    db = get_db()
    rows = db.execute(
        "SELECT id, amount, category, date, description "
        "FROM expenses WHERE user_id = ? "
        "ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return list(rows)


def seed_db() -> None:
    """Insert demo user + 8 sample expenses. No-op if users already has rows."""
    db = get_db()

    existing = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if existing["n"] > 0:
        return

    password_hash = generate_password_hash("demo123")

    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )

    user_id = db.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    sample_expenses = [
        (user_id,  4.75, "Food",          "2026-06-02", "Morning coffee + croissant"),
        (user_id, 12.00, "Transport",     "2026-06-04", "Metro pass top-up"),
        (user_id, 28.40, "Food",          "2026-06-09", "Weekly groceries"),
        (user_id, 35.00, "Health",        "2026-06-11", "Pharmacy restock"),
        (user_id, 89.99, "Bills",         "2026-06-15", "Internet — June"),
        (user_id, 62.30, "Shopping",      "2026-06-18", "New running shoes"),
        (user_id, 14.99, "Entertainment", "2026-06-22", "Streaming subscription"),
        (user_id,  7.50, "Other",         "2026-06-28", "Postage stamps"),
    ]

    db.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        sample_expenses,
    )
    db.commit()


# ------------------------------------------------------------------ #
# App registration                                                    #
# ------------------------------------------------------------------ #

def init_app(app) -> None:
    """Register teardown, ensure instance/ exists, set DATABASE config."""
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.setdefault("DATABASE", str(Path(app.instance_path) / "spendly.db"))
    app.teardown_appcontext(close_db)