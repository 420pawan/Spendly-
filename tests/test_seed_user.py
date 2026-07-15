import random

from werkzeug.security import check_password_hash

from database import db
from scripts import seed_user


def configure_test_database(monkeypatch, tmp_path):
    database_path = tmp_path / "spendly.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db()


def user_count():
    connection = db.get_db()
    try:
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        connection.close()


def test_generated_user_is_created_with_a_hashed_password(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)

    assert seed_user.main([]) == 0

    connection = db.get_db()
    try:
        user = connection.execute("SELECT * FROM users").fetchone()
        assert check_password_hash(user["password_hash"], "password123")
        assert user["created_at"].count(":") == 2
    finally:
        connection.close()


def test_custom_name_and_email_are_inserted(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)

    assert seed_user.main(["--name", "Ananya Iyer", "--email", "ananya@example.com"]) == 0

    connection = db.get_db()
    try:
        user = connection.execute(
            "SELECT name, email FROM users WHERE email = ?", ("ananya@example.com",)
        ).fetchone()
        assert tuple(user) == ("Ananya Iyer", "ananya@example.com")
    finally:
        connection.close()


def test_partial_custom_input_is_rejected_without_writing(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)

    assert seed_user.main(["--name", "Ananya Iyer"]) == 2
    assert user_count() == 0


def test_duplicate_custom_email_is_rejected_without_writing(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    assert seed_user.main(["--name", "Ananya Iyer", "--email", "ananya@example.com"]) == 0

    assert seed_user.main(["--name", "Other Name", "--email", "ananya@example.com"]) == 1
    assert user_count() == 1


def test_generated_email_retries_after_a_collision(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    connection = db.get_db()
    try:
        connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Rahul Sharma", "rahul.sharma91@gmail.com", "hash"),
        )
        connection.commit()
        rng = random.Random(1)
        monkeypatch.setattr(rng, "choice", lambda values: ("Rahul", "Sharma"))
        suffixes = iter((91, 92))
        monkeypatch.setattr(rng, "randint", lambda start, end: next(suffixes))
        assert seed_user.generated_user_details(connection, rng) == (
            "Rahul Sharma",
            "rahul.sharma92@gmail.com",
        )
    finally:
        connection.close()


def test_generated_email_stops_after_maximum_collisions(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    connection = db.get_db()
    try:
        connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Rahul Sharma", "rahul.sharma91@gmail.com", "hash"),
        )
        connection.commit()
        rng = random.Random(1)
        monkeypatch.setattr(rng, "choice", lambda values: ("Rahul", "Sharma"))
        monkeypatch.setattr(rng, "randint", lambda start, end: 91)
        try:
            seed_user.generated_user_details(connection, rng)
        except RuntimeError as error:
            assert str(error) == "Could not generate a unique email after 100 attempts."
        else:
            raise AssertionError("Expected generated email collisions to stop safely.")
    finally:
        connection.close()


def test_database_error_rolls_back_the_insert(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)

    def failing_insert(connection, name, email):
        connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, "hash"),
        )
        raise db.sqlite3.OperationalError("forced failure")

    monkeypatch.setattr(seed_user, "insert_user", failing_insert)
    assert seed_user.main(["--name", "Ananya Iyer", "--email", "ananya@example.com"]) == 1
    assert user_count() == 0
