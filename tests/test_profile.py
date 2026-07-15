import re

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


def login(client):
    db.create_user("Ananya Iyer", "ananya@example.com", "password123")
    return client.post(
        "/login", data={"email": "ananya@example.com", "password": "password123"}
    )


def test_profile_redirects_guests_to_login(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_authenticated_profile_renders_static_sections_and_navigation(client):
    login_response = login(client)
    response = client.get("/profile")

    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/profile")
    assert response.status_code == 200
    for text in (
        b"Pawan Kumar",
        b"pawan@example.com",
        "₹4,029".encode(),
        b"Transactions",
        b"Bills",
        b"Recent transactions",
        b"Category breakdown",
        b"Airport cab",
        b"Pharmacy",
        b"Lunch with friends",
        b"Profile",
        b"Sign out",
    ):
        assert text in response.data


def test_login_sets_session_identity_and_logout_clears_it(client):
    login(client)

    with client.session_transaction() as session:
        assert isinstance(session["user_id"], int)
        assert session["user_name"] == "Ananya Iyer"

    client.get("/logout")
    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "user_name" not in session


def test_profile_template_has_no_inline_styles_or_hex_colours():
    with open("templates/profile.html", encoding="utf-8") as profile_template:
        content = profile_template.read()

    assert "style=" not in content
    assert re.search(r"#[0-9a-fA-F]{3,8}", content) is None

def test_landing_redirects_authenticated_users_to_profile(client):
    login(client)

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")