import sqlite3

import pytest
from werkzeug.security import check_password_hash

from app import app
from database import db


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


def user_count():
    connection = db.get_db()
    try:
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        connection.close()


def registration_data(**overrides):
    data = {
        "name": "Ananya Iyer",
        "email": "ananya@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    data.update(overrides)
    return data


def test_register_get_renders_all_required_fields(client):
    response = client.get("/register")

    assert response.status_code == 200
    for field in ("name", "email", "password", "confirm_password"):
        assert f'name="{field}"'.encode() in response.data


def test_valid_registration_creates_hashed_user_and_redirects_to_login(client):
    response = client.post("/register", data=registration_data())

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert user_count() == 1

    connection = db.get_db()
    try:
        user = connection.execute(
            "SELECT name, email, password_hash FROM users WHERE email = ?",
            ("ananya@example.com",),
        ).fetchone()
    finally:
        connection.close()

    assert (user["name"], user["email"]) == ("Ananya Iyer", "ananya@example.com")
    assert user["password_hash"] != "password123"
    assert check_password_hash(user["password_hash"], "password123")


def test_successful_registration_message_is_shown_on_login(client):
    response = client.post("/register", data=registration_data(), follow_redirects=True)

    assert response.status_code == 200
    assert b"Registration successful. Please sign in." in response.data


@pytest.mark.parametrize(
    "data",
    [
        registration_data(name=""),
        registration_data(email="   "),
        registration_data(password=""),
        registration_data(confirm_password=""),
    ],
)
def test_blank_registration_fields_do_not_create_a_user(client, data):
    response = client.post("/register", data=data)

    assert response.status_code == 200
    assert b"All fields are required." in response.data
    assert user_count() == 0


def test_mismatched_passwords_do_not_create_a_user(client):
    response = client.post(
        "/register", data=registration_data(confirm_password="different-password")
    )

    assert response.status_code == 200
    assert b"Passwords do not match." in response.data
    assert user_count() == 0


def test_duplicate_email_is_rejected_without_a_second_user(client):
    first_response = client.post("/register", data=registration_data())
    second_response = client.post(
        "/register", data=registration_data(name="Other Name")
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 200
    assert b"Email already registered." in second_response.data
    assert user_count() == 1


def test_create_user_reraises_integrity_errors(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    db.create_user("Ananya Iyer", "ananya@example.com", "password123")

    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("Other Name", "ananya@example.com", "password123")
