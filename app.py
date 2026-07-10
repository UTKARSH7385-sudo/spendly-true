import os
import re

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.db import (
    DuplicateEmailError,
    create_user,
    find_user_by_email,
    init_app as init_db_app,
    init_db,
    seed_db,
    verify_password,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-do-not-use-in-prod"
)

# Email format check — simple regex, no external library.
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Logged-in visitors skip the form entirely.
    if session.get("user_id") is not None:
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    # POST — validate in this exact order, stop at the first failure.
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not name or not email or not password:
        error = "All fields are required."
    elif not EMAIL_RE.match(email):
        error = "Please enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters long."
    elif len(password) > 128:
        error = "Password must be no more than 128 characters long."
    elif find_user_by_email(email) is not None:
        error = "An account with that email already exists."
    else:
        error = None

    if error is not None:
        return render_template("register.html", error=error), 400

    # Race-condition guard: two requests can both pass the pre-check above
    # before either INSERTs; the UNIQUE constraint catches the loser.
    try:
        user_id = create_user(name, email, password)
    except DuplicateEmailError:
        return render_template(
            "register.html",
            error="An account with that email already exists.",
        ), 400

    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Logged-in visitors skip the form entirely.
    if session.get("user_id") is not None:
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    # POST — verify credentials. Normalise email exactly like /register.
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        return render_template(
            "login.html",
            error="Please enter both your email and password.",
        )

    user = verify_password(email, password)
    if user is None:
        # Same error for unknown email and wrong password — don't leak
        # which one was wrong.
        return render_template(
            "login.html",
            error="Invalid email or password.",
        )

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


# ------------------------------------------------------------------ #
# Database initialization                                             #
# ------------------------------------------------------------------ #

init_db_app(app)

with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
