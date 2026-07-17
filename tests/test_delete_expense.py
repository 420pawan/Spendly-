import pytest

from app import app
from database import db
from database.queries import delete_expense, insert_expense


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


def create_user(name: str, email: str) -> int:
    return db.create_user(name, email, "password123")


def login(client, email: str):
    return client.post(
        "/login",
        data={"email": email, "password": "password123"},
    )


def create_expense(user_id: int) -> int:
    return insert_expense(
        user_id,
        50.0,
        "Food",
        "2026-03-20",
        "Lunch",
    )


def expense_exists(expense_id: int) -> bool:
    connection = db.get_db()
    try:
        return connection.execute(
            "SELECT 1 FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone() is not None
    finally:
        connection.close()


def test_delete_expense_removes_owned_row(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)

    delete_expense(expense_id, user_id)

    assert not expense_exists(expense_id)


def test_delete_expense_does_not_remove_another_users_row(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    owner_id = create_user("Owner", "owner@example.com")
    other_id = create_user("Other", "other@example.com")
    expense_id = create_expense(owner_id)

    delete_expense(expense_id, other_id)

    assert expense_exists(expense_id)


def test_delete_expense_ignores_missing_expense(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = create_user("Owner", "owner@example.com")

    delete_expense(9999, user_id)


def test_delete_route_redirects_guests_to_login(client):
    response = client.post("/expenses/1/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_delete_route_removes_owned_expense(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.post(f"/expenses/{expense_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert not expense_exists(expense_id)


def test_delete_route_returns_404_for_another_users_expense(client):
    owner_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(owner_id)
    create_user("Other", "other@example.com")
    login(client, "other@example.com")

    response = client.post(f"/expenses/{expense_id}/delete")

    assert response.status_code == 404
    assert expense_exists(expense_id)


def test_delete_route_returns_404_for_missing_expense(client):
    create_user("Owner", "owner@example.com")
    login(client, "owner@example.com")

    response = client.post("/expenses/9999/delete")

    assert response.status_code == 404


def test_delete_route_rejects_get_requests(client):
    response = client.get("/expenses/1/delete")

    assert response.status_code == 405


def test_profile_shows_delete_action(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.get("/profile")

    assert f'/expenses/{expense_id}/delete'.encode() in response.data
    assert b"Delete this expense?" in response.data
    assert b">Delete</button>" in response.data