"""SQLite database helpers for Spendly."""

from datetime import date
from pathlib import Path
import sqlite3

from werkzeug.security import generate_password_hash


DATABASE_PATH = Path(__file__).resolve().parent.parent / "spendly.db"


def get_db() -> sqlite3.Connection:
    """Return a configured connection to the application database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_user(name: str, email: str, password: str) -> int:
    """Create a user with a securely hashed password and return its ID."""
    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        connection.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_user_by_email(email: str) -> sqlite3.Row | None:
    """Return the user with the supplied email, if one exists."""
    connection = get_db()
    try:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        connection.close()


def init_db() -> None:
    """Create the application tables if they do not already exist."""
    connection = get_db()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def seed_db() -> None:
    """Add one demo account and its sample expenses to an empty database."""
    connection = get_db()
    try:
        if connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None:
            return

        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid
        month_prefix = date.today().strftime("%Y-%m")
        expenses = [
            (450.0, "Food", f"{month_prefix}-02", "Groceries"),
            (120.0, "Transport", f"{month_prefix}-05", "Metro"),
            (899.0, "Shopping", f"{month_prefix}-08", "T-shirt"),
            (1200.0, "Bills", f"{month_prefix}-11", "Electricity"),
            (350.0, "Entertainment", f"{month_prefix}-15", "Movie"),
            (280.0, "Food", f"{month_prefix}-19", "Lunch"),
            (650.0, "Health", f"{month_prefix}-23", "Pharmacy"),
            (180.0, "Transport", f"{month_prefix}-27", "Cab"),
        ]
        connection.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [(user_id, *expense) for expense in expenses],
        )
        connection.commit()
    finally:
        connection.close()
