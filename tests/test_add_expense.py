import pytest

from app import app
from database import db
from database.queries import insert_expense


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


def login(client):
    user_id = db.create_user("Ananya Iyer", "ananya@example.com", "password123")
    response = client.post(
        "/login", data={"email": "ananya@example.com", "password": "password123"}
    )
    return user_id, response


def expense_count():
    connection = db.get_db()
    try:
        return connection.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    finally:
        connection.close()


def test_insert_expense_persists_a_valid_row(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = db.create_user("Ananya Iyer", "ananya@example.com", "password123")

    expense_id = insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")

    connection = db.get_db()
    try:
        row = connection.execute(
            "SELECT id, user_id, amount, category, date, description FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        connection.close()
    assert tuple(row) == (expense_id, user_id, 50.0, "Food", "2026-03-20", "Lunch")


def test_insert_expense_stores_none_description_as_null(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = db.create_user("Ananya Iyer", "ananya@example.com", "password123")

    expense_id = insert_expense(user_id, 50.0, "Food", "2026-03-20", None)

    connection = db.get_db()
    try:
        description = connection.execute(
            "SELECT description FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()["description"]
    finally:
        connection.close()
    assert description is None


def test_add_expense_redirects_guests_to_login(client):
    assert client.get("/expenses/add").status_code == 302
    assert client.post("/expenses/add", data={}).headers["Location"].endswith("/login")


def test_authenticated_get_renders_add_expense_form(client):
    login(client)

    response = client.get("/expenses/add")

    assert response.status_code == 200
    assert b'<form method="post"' in response.data
    for category in ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"):
        assert f'<option value="{category}"'.encode() in response.data


def test_valid_expense_redirects_to_profile_and_is_stored(client):
    user_id, _ = login(client)

    response = client.post(
        "/expenses/add",
        data={"amount": "50.0", "category": "Food", "date": "2026-03-20", "description": "Lunch"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    connection = db.get_db()
    try:
        row = connection.execute(
            "SELECT user_id, amount, category, date, description FROM expenses"
        ).fetchone()
    finally:
        connection.close()
    assert tuple(row) == (user_id, 50.0, "Food", "2026-03-20", "Lunch")


@pytest.mark.parametrize(
    ("data", "error"),
    [
        ({"amount": "", "category": "Food", "date": "2026-03-20"}, b"Amount must be a positive number."),
        ({"amount": "0", "category": "Food", "date": "2026-03-20"}, b"Amount must be greater than zero."),
        ({"amount": "many", "category": "Food", "date": "2026-03-20"}, b"Amount must be a positive number."),
        ({"amount": "50", "category": "Invalid", "date": "2026-03-20"}, b"Select a valid category."),
        ({"amount": "50", "category": "Food", "date": "not-a-date"}, b"Enter a valid date."),
    ],
)
def test_invalid_expenses_rerender_form_without_inserting(client, data, error):
    login(client)

    response = client.post("/expenses/add", data=data)

    assert response.status_code == 200
    assert error in response.data
    assert expense_count() == 0


def test_blank_description_is_stored_as_null(client):
    login(client)

    response = client.post(
        "/expenses/add",
        data={"amount": "50", "category": "Food", "date": "2026-03-20", "description": "   "},
    )

    assert response.status_code == 302
    connection = db.get_db()
    try:
        description = connection.execute("SELECT description FROM expenses").fetchone()["description"]
    finally:
        connection.close()
    assert description is None


def test_authenticated_navigation_contains_add_expense_link(client):
    login(client)

    assert b"Add Expense" in client.get("/profile").data