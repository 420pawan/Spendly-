import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import create_user, get_user_by_email, init_db, seed_db
from werkzeug.security import check_password_hash

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

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

    profile_user = {
        "initials": "PK",
        "name": "Pawan Kumar",
        "email": "pawan@example.com",
        "member_since": "January 2025",
    }
    summary = {
        "total_spent": "₹4,029",
        "transaction_count": 8,
        "top_category": "Bills",
    }
    transactions = [
        {"date": "27 Jun 2025", "description": "Airport cab", "category": "Transport", "amount": "₹180"},
        {"date": "23 Jun 2025", "description": "Pharmacy", "category": "Health", "amount": "₹650"},
        {"date": "19 Jun 2025", "description": "Lunch with friends", "category": "Food", "amount": "₹280"},
        {"date": "15 Jun 2025", "description": "Movie tickets", "category": "Entertainment", "amount": "₹350"},
    ]
    categories = [
        {"name": "Bills", "amount": "₹1,200", "class_name": "bills"},
        {"name": "Shopping", "amount": "₹899", "class_name": "shopping"},
        {"name": "Health", "amount": "₹650", "class_name": "health"},
        {"name": "Food", "amount": "₹280", "class_name": "food"},
    ]
    return render_template(
        "profile.html",
        profile_user=profile_user,
        summary=summary,
        transactions=transactions,
        categories=categories,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)