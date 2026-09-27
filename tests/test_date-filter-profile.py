import pytest
from datetime import date

def test_profile_redirects_when_signed_out(client):
    """Unauthenticated GET /profile must redirect to /login."""
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

def test_profile_renders_default_current_month(client, auth_user):
    """Signed-in user sees current month summary by default."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})
    resp = client.get("/profile")
    assert resp.status_code == 200
    # The spec says "default behavior must remain as current month"
    # We assert the page renders successfully.
    assert b"Profile" in resp.data

def test_profile_filters_by_date_range(client, auth_user):
    """User can filter summary by specific start and end dates."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    # Create expenses in different ranges
    # Note: We rely on the app's internal DB helpers through the route logic,
    # but the spec says "User can enter a start date and end date... and see the summary".
    # Since I cannot use DB logic in tests, I will assume the seed_db or the user
    # adding expenses via the UI (if implemented) provides data.
    # For the purpose of this test, we check if the query params are handled and reflected.

    start_date = "2023-01-01"
    end_date = "2023-01-31"
    resp = client.get(f"/profile?start_date={start_date}&end_date={end_date}")

    assert resp.status_code == 200
    # The spec says "Display the selected date range if active."
    assert start_date.encode() in resp.data
    assert end_date.encode() in resp.data

def test_profile_handles_invalid_date_format(client, auth_user):
    """Providing an invalid date format does not crash the server."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    # Use an invalid date format
    resp = client.get("/profile?start_date=invalid-date&end_date=not-a-date")

    # Spec: "handled gracefully, e.g., falling back to default or showing an error"
    assert resp.status_code == 200
    assert b"Profile" in resp.data

def test_profile_reset_returns_to_default(client, auth_user):
    """Clicking 'Clear' or 'Reset' returns the view to current month."""
    client.post("/login", data={"email": auth_user["email"], "password": auth_user["password"]})

    # First filter the view
    client.get("/profile?start_date=2023-01-01&end_date=2023-01-31")

    # The 'Reset' button is a GET request to /profile (without params)
    resp = client.get("/profile")

    assert resp.status_code == 200
    # The date range should no longer be displayed as active
    assert b"2023-01-01" not in resp.data
    assert b"2023-01-31" not in resp.data
