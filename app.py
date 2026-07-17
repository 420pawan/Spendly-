import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import create_user, get_user_by_email, init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_expense_by_id,
    get_recent_transactions,
    get_summary_stats,
    insert_expense,
    update_expense,
)

app = Flask(__name__)
app.secret_key = "spendly-development-secret"

with app.app_context():
    init_db()
    seed_db()


@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not all((name, email, password, confirm_password)):
            flash("All fields are required.")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")
        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return render_template("register.html")
        flash("Registration successful. Please sign in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_email(email) if email and password else None
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    for value_name, value in (("date_from", date_from), ("date_to", date_to)):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                if value_name == "date_from":
                    date_from = None
                else:
                    date_to = None
    if not (date_from and date_to):
        date_from = None
        date_to = None
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = None
        date_to = None

    today = date.today()
    presets = [
        {
            "key": "this_month",
            "label": "This Month",
            "date_from": today.replace(day=1).isoformat(),
            "date_to": today.isoformat(),
        },
        {
            "key": "last_3_months",
            "label": "Last 3 Months",
            "date_from": (today - timedelta(days=90)).isoformat(),
            "date_to": today.isoformat(),
        },
        {
            "key": "last_6_months",
            "label": "Last 6 Months",
            "date_from": (today - timedelta(days=180)).isoformat(),
            "date_to": today.isoformat(),
        },
        {
            "key": "all_time",
            "label": "All Time",
            "date_from": None,
            "date_to": None,
        },
    ]
    active_preset = next(
        (
            preset["key"]
            for preset in presets
            if preset["date_from"] == date_from and preset["date_to"] == date_to
        ),
        None,
    )
    custom_range_active = bool(
        date_from and date_to and active_preset is None
    )

    profile_user = {
        "initials": "PK",
        "name": "Pawan Kumar",
        "email": "pawan@example.com",
        "member_since": "January 2025",
    }
    user_id = session["user_id"]
    summary = get_summary_stats(user_id, date_from, date_to)
    transactions = get_recent_transactions(
        user_id, date_from=date_from, date_to=date_to
    )
    categories = get_category_breakdown(user_id, date_from, date_to)
    return render_template(
        "profile.html",
        profile_user=profile_user,
        summary=summary,
        transactions=transactions,
        categories=categories,
        presets=presets,
        active_preset=active_preset,
        custom_range_active=custom_range_active,
        active_date_from=date_from,
        active_date_to=date_to,
    )


EXPENSE_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    values = {
        "amount": "",
        "category": "",
        "date": date.today().isoformat(),
        "description": "",
    }
    if request.method == "POST":
        values = {
            "amount": request.form.get("amount", "").strip(),
            "category": request.form.get("category", "").strip(),
            "date": request.form.get("date", "").strip(),
            "description": request.form.get("description", "").strip(),
        }
        try:
            amount = float(values["amount"])
        except ValueError:
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Amount must be a positive number.",
            )
        if amount <= 0:
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Amount must be greater than zero.",
            )
        if values["category"] not in EXPENSE_CATEGORIES:
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Select a valid category.",
            )
        try:
            datetime.strptime(values["date"], "%Y-%m-%d")
        except ValueError:
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Enter a valid date.",
            )
        if len(values["description"]) > 200:
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Description must be 200 characters or fewer.",
            )

        insert_expense(
            session["user_id"],
            amount,
            values["category"],
            values["date"],
            values["description"] or None,
        )
        return redirect(url_for("profile"))

    return render_template(
        "add_expense.html",
        categories=EXPENSE_CATEGORIES,
        values=values,
        error=None,
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    values = {
        "amount": expense["amount"],
        "category": expense["category"],
        "date": expense["date"],
        "description": expense["description"] or "",
    }

    if request.method == "POST":
        values = {
            "amount": request.form.get("amount", "").strip(),
            "category": request.form.get("category", "").strip(),
            "date": request.form.get("date", "").strip(),
            "description": request.form.get("description", "").strip(),
        }
        try:
            amount = float(values["amount"])
        except ValueError:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Amount must be a positive number.",
            )
        if amount <= 0:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Amount must be greater than zero.",
            )
        if values["category"] not in EXPENSE_CATEGORIES:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Select a valid category.",
            )
        try:
            datetime.strptime(values["date"], "%Y-%m-%d")
        except ValueError:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Enter a valid date.",
            )
        if len(values["description"]) > 200:
            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=EXPENSE_CATEGORIES,
                values=values,
                error="Description must be 200 characters or fewer.",
            )

        update_expense(
            id,
            session["user_id"],
            amount,
            values["category"],
            values["date"],
            values["description"] or None,
        )
        return redirect(url_for("profile"))

    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=EXPENSE_CATEGORIES,
        values=values,
        error=None,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)