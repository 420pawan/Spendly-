import pytest

from app import app
from database import db


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


def create_test_user():
    return db.create_user("Ananya Iyer", "ananya@example.com", "password123")


def test_login_get_renders_credentials_fields(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_valid_login_sets_user_session_and_redirects_to_landing(client):
    user_id = create_test_user()

    response = client.post(
        "/login", data={"email": "ananya@example.com", "password": "password123"}
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert session["user_id"] == user_id


@pytest.mark.parametrize(
    "data",
    [
        {"email": "ananya@example.com", "password": "wrong-password"},
        {"email": "unknown@example.com", "password": "password123"},
        {"email": "", "password": ""},
    ],
)
def test_invalid_login_shows_generic_error_without_authenticating(client, data):
    create_test_user()

    response = client.post("/login", data=data)

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_logout_clears_session_and_redirects_to_landing(client):
    with client.session_transaction() as session:
        session["user_id"] = 42

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_logout_is_safe_without_an_existing_session(client):
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

def test_navigation_reflects_authenticated_session(client):
    guest_page = client.get("/")
    assert b"Sign in" in guest_page.data
    assert b"Get started" in guest_page.data
    assert b"Sign out" not in guest_page.data

    create_test_user()
    client.post(
        "/login", data={"email": "ananya@example.com", "password": "password123"}
    )

    signed_in_page = client.get("/")
    assert b"Welcome back" in signed_in_page.data
    assert b"Sign out" in signed_in_page.data
    assert b"Get started" not in signed_in_page.data

def test_authenticated_user_is_redirected_away_from_login_and_register(client):
    create_test_user()
    client.post(
        "/login", data={"email": "ananya@example.com", "password": "password123"}
    )

    for route in ("/login", "/register"):
        response = client.get(route)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    client.get("/logout")
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200