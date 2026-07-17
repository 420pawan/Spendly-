import pytest

from app import app
from database import db
from database.queries import get_expense_by_id, insert_expense, update_expense


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


def get_expense_row(expense_id: int):
    connection = db.get_db()
    try:
        return connection.execute(
            "SELECT id, user_id, amount, category, date, description "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        connection.close()


def test_get_expense_by_id_returns_matching_owned_expense(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    owner_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(owner_id)

    expense = get_expense_by_id(expense_id, owner_id)

    assert expense is not None
    assert expense["id"] == expense_id
    assert expense["user_id"] == owner_id
    assert expense["amount"] == 50.0
    assert expense["category"] == "Food"


def test_get_expense_by_id_returns_none_for_wrong_user(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    owner_id = create_user("Owner", "owner@example.com")
    other_id = create_user("Other", "other@example.com")
    expense_id = create_expense(owner_id)

    assert get_expense_by_id(expense_id, other_id) is None


def test_get_expense_by_id_returns_none_for_missing_expense(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = create_user("Owner", "owner@example.com")

    assert get_expense_by_id(9999, user_id) is None


def test_update_expense_updates_owned_row(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)

    update_expense(
        expense_id,
        user_id,
        99.0,
        "Bills",
        "2026-03-21",
        "Electricity",
    )

    row = get_expense_row(expense_id)
    assert tuple(row) == (
        expense_id,
        user_id,
        99.0,
        "Bills",
        "2026-03-21",
        "Electricity",
    )


def test_update_expense_does_not_change_another_users_row(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "spendly.db")
    db.init_db()
    owner_id = create_user("Owner", "owner@example.com")
    other_id = create_user("Other", "other@example.com")
    expense_id = create_expense(owner_id)

    update_expense(
        expense_id,
        other_id,
        99.0,
        "Bills",
        "2026-03-21",
        "Changed",
    )

    row = get_expense_row(expense_id)
    assert tuple(row) == (
        expense_id,
        owner_id,
        50.0,
        "Food",
        "2026-03-20",
        "Lunch",
    )


def test_edit_expense_get_redirects_guests_to_login(client):
    response = client.get("/expenses/1/edit")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_edit_expense_post_redirects_guests_to_login(client):
    response = client.post("/expenses/1/edit", data={})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_edit_expense_get_renders_prepopulated_owned_expense(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.get(f"/expenses/{expense_id}/edit")

    assert response.status_code == 200
    assert b'action="/expenses/' in response.data
    assert b'value="50.0"' in response.data
    assert b'<option value="Food" selected>' in response.data
    assert b'value="2026-03-20"' in response.data
    assert b'value="Lunch"' in response.data


def test_edit_expense_get_returns_404_for_other_users_expense(client):
    owner_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(owner_id)
    create_user("Other", "other@example.com")
    login(client, "other@example.com")

    response = client.get(f"/expenses/{expense_id}/edit")

    assert response.status_code == 404


def test_edit_expense_get_returns_404_for_missing_expense(client):
    create_user("Owner", "owner@example.com")
    login(client, "owner@example.com")

    response = client.get("/expenses/9999/edit")

    assert response.status_code == 404


def test_valid_edit_redirects_and_updates_the_expense(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "99.0",
            "category": "Bills",
            "date": "2026-03-21",
            "description": "Electricity",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    row = get_expense_row(expense_id)
    assert (
        row["amount"],
        row["category"],
        row["date"],
        row["description"],
    ) == (99.0, "Bills", "2026-03-21", "Electricity")


def test_edit_expense_post_returns_404_for_other_users_expense(client):
    owner_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(owner_id)
    create_user("Other", "other@example.com")
    login(client, "other@example.com")

    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "99.0",
            "category": "Bills",
            "date": "2026-03-21",
            "description": "Changed",
        },
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (
            {
                "amount": "",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Submitted description",
            },
            b"Amount must be a positive number.",
        ),
        (
            {
                "amount": "0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Submitted description",
            },
            b"Amount must be greater than zero.",
        ),
        (
            {
                "amount": "many",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Submitted description",
            },
            b"Amount must be a positive number.",
        ),
        (
            {
                "amount": "50",
                "category": "Invalid",
                "date": "2026-03-20",
                "description": "Submitted description",
            },
            b"Select a valid category.",
        ),
        (
            {
                "amount": "50",
                "category": "Food",
                "date": "not-a-date",
                "description": "Submitted description",
            },
            b"Enter a valid date.",
        ),
    ],
)
def test_invalid_edits_rerender_form_with_submitted_values(client, data, error):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.post(f"/expenses/{expense_id}/edit", data=data)

    assert response.status_code == 200
    assert error in response.data
    assert b'value="Submitted description"' in response.data
    assert get_expense_row(expense_id)["amount"] == 50.0


def test_edit_without_description_stores_null(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "99.0",
            "category": "Bills",
            "date": "2026-03-21",
            "description": "   ",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert get_expense_row(expense_id)["description"] is None


def test_profile_includes_an_edit_link_for_each_transaction(client):
    user_id = create_user("Owner", "owner@example.com")
    expense_id = create_expense(user_id)
    login(client, "owner@example.com")

    response = client.get("/profile")

    assert response.status_code == 200
    assert b"<th>Actions</th>" in response.data
    assert f'/expenses/{expense_id}/edit'.encode() in response.data
    assert b">Edit</a>" in response.data