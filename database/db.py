import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


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