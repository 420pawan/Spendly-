"""Create one dummy Spendly user from the command line."""

import argparse
from datetime import datetime
from pathlib import Path
import random
import sqlite3
import sys

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_db, init_db


INDIAN_NAMES = (
    ("Aarav", "Sharma"),
    ("Ananya", "Iyer"),
    ("Arjun", "Reddy"),
    ("Divya", "Nair"),
    ("Harpreet", "Singh"),
    ("Ishita", "Mukherjee"),
    ("Karthik", "Subramanian"),
    ("Kavya", "Patel"),
    ("Manish", "Gupta"),
    ("Meera", "Kulkarni"),
    ("Nikhil", "Bose"),
    ("Priya", "Desai"),
    ("Rahul", "Verma"),
    ("Sana", "Khan"),
    ("Vikram", "Das"),
)
MAX_EMAIL_ATTEMPTS = 100
DEFAULT_PASSWORD = "password123"


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create one dummy Spendly user.")
    parser.add_argument("--name", help="Full name for a controlled test user.")
    parser.add_argument("--email", help="Email for a controlled test user.")
    return parser.parse_args(arguments)


def is_valid_email(email: str) -> bool:
    """Perform the minimal email validation required by this utility."""
    local, separator, domain = email.partition("@")
    return bool(local and separator and domain and " " not in email)


def email_exists(connection: sqlite3.Connection, email: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM users WHERE email = ? LIMIT 1", (email,)
    ).fetchone() is not None


def generated_user_details(
    connection: sqlite3.Connection, rng: random.Random | random.SystemRandom
) -> tuple[str, str]:
    """Return a generated name and an email not already used in the database."""
    for _ in range(MAX_EMAIL_ATTEMPTS):
        first_name, last_name = rng.choice(INDIAN_NAMES)
        email = f"{first_name}.{last_name}{rng.randint(10, 999)}@gmail.com".lower()
        if not email_exists(connection, email):
            return f"{first_name} {last_name}", email
    raise RuntimeError("Could not generate a unique email after 100 attempts.")


def insert_user(connection: sqlite3.Connection, name: str, email: str) -> int:
    """Insert one user and return its database ID."""
    cursor = connection.execute(
        """
        INSERT INTO users (name, email, password_hash, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            email,
            generate_password_hash(DEFAULT_PASSWORD),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    return cursor.lastrowid


def main(arguments: list[str] | None = None) -> int:
    args = parse_args(arguments)
    has_name = args.name is not None
    has_email = args.email is not None

    if has_name != has_email:
        print("Error: --name and --email must be supplied together.", file=sys.stderr)
        return 2
    if has_name and (not args.name.strip() or not is_valid_email(args.email)):
        print("Error: provide a non-empty name and a valid email address.", file=sys.stderr)
        return 2

    connection = None
    try:
        init_db()
        connection = get_db()
        if has_name:
            name = args.name.strip()
            email = args.email.strip().lower()
            if email_exists(connection, email):
                print(f"Error: a user with email {email} already exists.", file=sys.stderr)
                return 1
        else:
            name, email = generated_user_details(connection, random.SystemRandom())

        user_id = insert_user(connection, name, email)
        connection.commit()
    except (RuntimeError, sqlite3.Error) as error:
        connection.rollback()
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()

    print("User created successfully:")
    print(f"id: {user_id}")
    print(f"name: {name}")
    print(f"email: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
