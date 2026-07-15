import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from database.db import create_user, get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-development-secret"

with app.app_context():
    init_db()
    seed_db()


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
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

    if request.method == "GET":
        return render_template("register.html")

    abort(405)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        print(email, password)

        return "Login successful!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    return "Logout - Coming Soon"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
