def test_expenses_redirects_when_signed_out(client):
    """Unauthenticated GET /expenses must redirect to /login."""
    resp = client.get("/expenses")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_expenses_renders_for_signed_in_user(client, auth_user):
    """Signed-in user sees the list page with HTTP 200."""
    resp = client.get("/expenses")
    assert resp.status_code == 200


def test_expenses_empty_state_for_new_user(client, auth_user):
    """User with zero expenses sees the empty state, not a crash."""
    resp = client.get("/expenses")
    assert resp.status_code == 200
    assert b"You haven't logged any expenses yet" in resp.data
    assert b"0 recorded" in resp.data


def test_expenses_lists_seeded_demo_user_expenses(client):
    """Logging in as demo@spendly.com shows the 8 seeded expenses."""
    client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
    )
    resp = client.get("/expenses")
    assert resp.status_code == 200
    # A few well-known seeded values — not exhaustive.
    assert b"89.99" in resp.data  # Internet — June
    assert b"62.30" in resp.data  # New running shoes


def test_expenses_scoped_to_current_user(client):
    """The list only shows the signed-in user's rows, never another user's."""
    # Register two users; only one has expenses (the seeded demo user).
    client.post(
        "/register",
        data={"name": "Other", "email": "other@example.com", "password": "password123"},
    )
    resp = client.get("/expenses")
    assert resp.status_code == 200
    # The newly registered user has zero expenses, so the empty state
    # must show — not the demo user's seeded amounts.
    assert b"You haven't logged any expenses yet" in resp.data
    assert b"89.99" not in resp.data  # demo user's seeded value must NOT leak
