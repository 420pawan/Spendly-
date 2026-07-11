from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        print(name, email, password)

        return "Registration successful!"

    return render_template("register.html")


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