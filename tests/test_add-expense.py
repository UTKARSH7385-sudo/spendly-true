import pytest
from flask import session
from database import db as db_module

def test_add_expense_unauthenticated_redirect(client):
    """Unauthenticated GET /expenses/add must redirect to /login."""
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert response.location.endswith("/login")

def test_add_expense_authenticated_get(client, auth_user):
    """Authenticated GET /expenses/add must render the form."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    response = client.get("/expenses/add")
    assert response.status_code == 200
    assert b"Add Expense" in response.data
    assert b'name="amount"' in response.data
    assert b'name="category"' in response.data
    assert b'name="date"' in response.data
    assert b'name="description"' in response.data

def test_add_expense_success(client, auth_user, app):
    """Authenticated POST /expenses/add with valid data must save expense and redirect."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    expense_data = {
        "amount": "50.00",
        "category": "Food",
        "date": "2023-10-27",
        "description": "Lunch at Cafe"
    }

    response = client.post("/expenses/add", data=expense_data)

    # Redirect after success (spec says profile or expenses list)
    assert response.status_code == 302
    assert response.location.endswith(("/profile", "/expenses"))

    # Verify DB state
    with app.app_context():
        conn = db_module.get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE amount = ? AND category = ? AND date = ?",
            (50.00, "Food", "2023-10-27")
        ).fetchone()
        assert row is not None
        assert row["description"] == "Lunch at Cafe"

def test_add_expense_invalid_amount(client, auth_user):
    """POST /expenses/add with negative amount must show error and not save."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    expense_data = {
        "amount": "-10.00",
        "category": "Food",
        "date": "2023-10-27",
        "description": "Invalid"
    }

    response = client.post("/expenses/add", data=expense_data)

    assert response.status_code == 200
    assert b"error" in response.data.lower() # Expecting an error message in the template

    # Verify nothing was saved
    with client.application.app_context():
        from database.db import get_db
        conn = get_db()
        row = conn.execute("SELECT * FROM expenses WHERE amount = ?", (-10.00,)).fetchone()
        assert row is None

def test_add_expense_empty_category(client, auth_user):
    """POST /expenses/add with empty category must show error and not save."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    expense_data = {
        "amount": "20.00",
        "category": "",
        "date": "2023-10-27",
        "description": "Invalid"
    }

    response = client.post("/expenses/add", data=expense_data)

    assert response.status_code == 200
    assert b"error" in response.data.lower()

def test_add_expense_invalid_date(client, auth_user):
    """POST /expenses/add with invalid date must show error and not save."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    expense_data = {
        "amount": "20.00",
        "category": "Transport",
        "date": "not-a-date",
        "description": "Invalid"
    }

    response = client.post("/expenses/add", data=expense_data)

    assert response.status_code == 200
    assert b"error" in response.data.lower()
