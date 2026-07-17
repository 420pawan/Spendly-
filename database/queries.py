"""Profile-page queries for Spendly."""

from datetime import datetime

from database.db import get_db


def _format_amount(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _date_clause(date_from: str | None, date_to: str | None) -> tuple[str, list[object]]:
    if date_from and date_to:
        return " AND date BETWEEN ? AND ?", [date_from, date_to]
    return "", []


def get_summary_stats(user_id: int, date_from: str | None = None, date_to: str | None = None) -> dict[str, object]:
    """Return aggregate spending values for one user and optional date range."""
    date_sql, date_params = _date_clause(date_from, date_to)
    connection = get_db()
    try:
        totals = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count FROM expenses WHERE user_id = ?" + date_sql,
            [user_id, *date_params],
        ).fetchone()
        top_category = connection.execute(
            "SELECT category FROM expenses WHERE user_id = ?" + date_sql + " GROUP BY category ORDER BY SUM(amount) DESC, category ASC LIMIT 1",
            [user_id, *date_params],
        ).fetchone()
    finally:
        connection.close()
    return {
        "total_spent": _format_amount(totals["total_spent"]),
        "transaction_count": totals["transaction_count"],
        "top_category": top_category["category"] if top_category else "—",
    }


def get_recent_transactions(user_id: int, limit: int = 10, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, str]]:
    """Return the latest expenses for one user and optional date range."""
    date_sql, date_params = _date_clause(date_from, date_to)
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ?" + date_sql + " ORDER BY date DESC, id DESC LIMIT ?",
            [user_id, *date_params, limit],
        ).fetchall()
    finally:
        connection.close()
    return [{
        "date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y"),
        "description": row["description"] or "—",
        "category": row["category"],
        "amount": _format_amount(row["amount"]),
    } for row in rows]


def get_category_breakdown(user_id: int, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, object]]:
    """Return per-category spending totals and percentages for one user."""
    date_sql, date_params = _date_clause(date_from, date_to)
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ?" + date_sql + " GROUP BY category ORDER BY total DESC, category ASC",
            [user_id, *date_params],
        ).fetchall()
    finally:
        connection.close()
    overall_total = sum(row["total"] for row in rows)
    return [{
        "name": row["category"],
        "amount": _format_amount(row["total"]),
        "percentage": round((row["total"] / overall_total) * 100) if overall_total else 0,
        "class_name": row["category"].lower().replace(" ", "-"),
    } for row in rows]


def insert_expense(
    user_id: int,
    amount: float,
    category: str,
    expense_date: str,
    description: str | None,
) -> int:
    """Create an expense and return its database ID."""
    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, expense_date, description),
        )
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
