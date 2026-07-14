# Database Setup Implementation Plan

## Goal

Implement the SQLite data layer for Spendly and initialize it when the Flask application starts, without changing the existing route behavior.

## Current State

- `database/db.py` is a documented stub with no database code.
- `app.py` defines only placeholder landing, registration, login, and logout routes.
- No database file or application startup initialization is currently configured.

## Implementation Steps

1. Implement connection creation in `database/db.py`.
   - Define a project-root database path for `spendly.db` (or the approved alternative name).
   - Add `get_db()` using the standard-library `sqlite3` module.
   - Configure each connection with `sqlite3.Row` as its row factory and enable `PRAGMA foreign_keys = ON` before returning it.

2. Add idempotent schema initialization in `database/db.py`.
   - Implement `init_db()` to open a connection and execute `CREATE TABLE IF NOT EXISTS` statements for `users` and `expenses`.
   - Create `users` with an auto-incrementing primary key, required name/email/password hash fields, a unique email constraint, and a default creation timestamp.
   - Create `expenses` with an auto-incrementing primary key, required user/amount/category/date fields, an optional description, a default creation timestamp, and a foreign key to `users(id)`.
   - Commit the schema changes and close the connection reliably.

3. Add safe, repeatable development seed data in `database/db.py`.
   - Implement `seed_db()` to return immediately when at least one user already exists.
   - Insert the Demo User with `demo@spendly.com` and a password hash generated from `demo123` via `werkzeug.security.generate_password_hash`.
   - Insert exactly eight parameterized sample expense records for that user, using the required category names, floating-point amounts, and ISO `YYYY-MM-DD` dates spread through the current month.
   - Commit inserts and close the connection; avoid duplicate seed data on subsequent runs.

4. Initialize the data layer from `app.py`.
   - Import `get_db`, `init_db`, and `seed_db` from `database.db`.
   - On application startup, enter `app.app_context()` and call `init_db()` followed by `seed_db()` before routes are served.
   - Preserve all current routes and their placeholder responses for this database-only step.

5. Verify the implementation.
   - Start the application and confirm the SQLite database file is created without startup errors.
   - Inspect the schema to confirm all columns, constraints, defaults, and the foreign key are present.
   - Confirm the demo user has a non-plaintext password hash and exactly eight linked sample expenses.
   - Run initialization and seeding more than once and confirm record counts do not increase.
   - Attempt a duplicate email insert and an expense insert for a nonexistent user; confirm SQLite raises the expected integrity errors.

## Constraints

- Use `sqlite3` only; do not add an ORM or new dependencies.
- Use parameterized SQL for every query; do not interpolate values into SQL strings.
- Enable foreign-key enforcement on every connection.
- Store expense amounts as `REAL`/floating-point values and dates consistently as `YYYY-MM-DD` text.
