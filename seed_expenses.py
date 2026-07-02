"""Seed random expenses for a specific user.

Usage (from inside the app folder):
    python seed_expenses.py <user_id> <count> <months>
"""

import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from flask import Flask

from database.db import init_app as init_db_app, init_db


# Indian-realistic descriptions and (min, max) rupee ranges per category.
CATEGORIES = {
    "Food": {
        "weight": 30,
        "range": (50, 800),
        "descriptions": [
            "Chai and samosa at local stall",
            "Lunch — thali at mess",
            "Zomato order — biryani",
            "Swiggy dinner — paneer roll",
            "Weekly groceries — BigBasket",
            "Filter coffee and idli",
            "Street food — pav bhaji",
            "Subway meal deal",
            "Dinner at restaurant with friends",
            "Milk and bread from neighbourhood store",
        ],
    },
    "Transport": {
        "weight": 20,
        "range": (20, 500),
        "descriptions": [
            "Auto rickshaw to office",
            "Ola ride to airport",
            "Rapido bike taxi",
            "Metro card recharge",
            "Petrol refill",
            "Uber to friend's place",
            "Monthly bus pass",
            "Cab to railway station",
            "Two-wheeler service",
            "Diesel top-up",
        ],
    },
    "Bills": {
        "weight": 10,
        "range": (200, 3000),
        "descriptions": [
            "Electricity bill — BSES",
            "Jio postpaid mobile bill",
            "Broadband — Airtel Xstream",
            "DTH recharge — Tata Play",
            "Water tanker",
            "Gas cylinder refill",
            "Apartment maintenance",
            "Credit card bill payment",
            "Piped gas bill",
            "WiFi router rental",
        ],
    },
    "Health": {
        "weight": 8,
        "range": (100, 2000),
        "descriptions": [
            "Pharmacy — paracetamol and vitamins",
            "Doctor consultation fee",
            "Dental checkup",
            "Lab tests — thyroid panel",
            "Gym monthly membership",
            "Yoga class drop-in",
            "Health supplement — ashwagandha",
            "Eye checkup and new lenses",
            "Physiotherapy session",
            "First aid kit restock",
        ],
    },
    "Entertainment": {
        "weight": 10,
        "range": (100, 1500),
        "descriptions": [
            "Movie tickets — PVR",
            "Netflix monthly subscription",
            "Spotify Premium",
            "BookMyEvent — standup comedy show",
            "Bowling with friends",
            "Disney+ Hotstar renewal",
            "Concert tickets",
            "Board game café visit",
            "OTT bundle annual plan",
            "Amusement park entry",
        ],
    },
    "Shopping": {
        "weight": 14,
        "range": (200, 5000),
        "descriptions": [
            "Amazon — phone charger",
            "Flipkart — new t-shirt",
            "Myntra — ethnic wear sale",
            "Lifestyle — running shoes",
            "Decathlon — yoga mat",
            "Local tailor — kurta",
            "Nykaa — skincare restock",
            "Croma — bluetooth earphones",
            "IKEA — desk organiser",
            "D-Mart — household supplies",
        ],
    },
    "Other": {
        "weight": 8,
        "range": (50, 1000),
        "descriptions": [
            "Postage and courier",
            "Birthday gift for friend",
            "Donation to temple",
            "Newspaper subscription",
            "Haircut at salon",
            "Laundry — dry cleaning",
            "Plant saplings for balcony",
            "Tailoring alterations",
            "Banking charges",
            "Parking fee at mall",
        ],
    },
}


def _weighted_category() -> str:
    """Pick a category with weights roughly proportional to commonality."""
    labels = list(CATEGORIES.keys())
    weights = [CATEGORIES[c]["weight"] for c in labels]
    return random.choices(labels, weights=weights, k=1)[0]


def _random_date(start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def _random_amount(category: str) -> float:
    lo, hi = CATEGORIES[category]["range"]
    # Two-decimal precision, rupee-friendly.
    return round(random.uniform(lo, hi), 2)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: /seed-expenses <user_id> <count> <months>\n"
            "Example: /seed-expenses 1 50 6"
        )
        return 1

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print(
            "Usage: /seed-expenses <user_id> <count> <months>\n"
            "Example: /seed-expenses 1 50 6"
        )
        return 1

    # Bring up the Flask app context so init_db_app() configures DATABASE.
    app = Flask(__name__)
    init_db_app(app)
    with app.app_context():
        init_db()

        from flask import current_app
        db_path = current_app.config["DATABASE"]

    # Use a direct connection (not the request-scoped `g` connection) so we
    # can run this as a stand-alone script outside a request.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            print(f"No user found with id {user_id}.")
            return 1

        today = date.today()
        # Anchor the end of the window to the *last day of the previous month*
        # so we never accidentally seed a future expense.
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date - timedelta(days=months * 30)

        rows = []
        for _ in range(count):
            category = _weighted_category()
            description = random.choice(CATEGORIES[category]["descriptions"])
            amount = _random_amount(category)
            d = _random_date(start_date, end_date)
            rows.append((user_id, amount, category, d.isoformat(), description))

        try:
            conn.executemany(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"Insert failed, transaction rolled back: {exc}")
            return 1

        inserted = conn.execute(
            """
            SELECT id, amount, category, date, description
            FROM expenses
            WHERE user_id = ?
              AND date BETWEEN ? AND ?
            ORDER BY date DESC
            """,
            (user_id, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

        sample = inserted[:5]

        # Reconfigure stdout for the rupee glyph on legacy Windows consoles.
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

        print(f"Inserted {len(inserted)} expenses for user_id={user_id}.")
        print(f"Date range: {start_date.isoformat()}  to  {end_date.isoformat()}")
        print("Sample (up to 5 most recent):")
        for row in sample:
            print(
                f"  #{row['id']:>4}  {row['date']}  Rs.{row['amount']:>8.2f}  "
                f"{row['category']:<14} {row['description']}"
            )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
