"""
seed_expenses.py

Seeds realistic expense records into spendly.db for a given user.

Usage:
    python scripts/seed_expenses.py <user_id> <count> <months>

Example:
    python scripts/seed_expenses.py 1 50 6
"""

import sys
import random
from datetime import datetime, timedelta

# Uses the existing db connection helper — do not hardcode the db filename.
from database.db import get_db


CATEGORY_RANGES = {
    "Food": (50, 800),
    "Transport": (20, 500),
    "Bills": (200, 3000),
    "Health": (100, 2000),
    "Entertainment": (100, 1500),
    "Shopping": (200, 5000),
    "Other": (50, 1000),
}

CATEGORY_WEIGHTS = {
    "Food": 30,
    "Transport": 20,
    "Bills": 15,
    "Shopping": 15,
    "Other": 10,
    "Entertainment": 5,
    "Health": 5,
}

DESCRIPTIONS = {
    "Food": [
        "Swiggy order", "Zomato delivery", "Grocery run - Big Bazaar",
        "Local kirana store", "Lunch at office cafeteria", "Dominos pizza",
        "Vegetable vendor", "Milk and dairy - local dairy", "Chai and snacks",
        "Dinner with friends",
    ],
    "Transport": [
        "Ola ride", "Uber ride", "Metro card recharge", "Auto rickshaw fare",
        "Petrol - Indian Oil", "Bus pass", "Railway ticket booking",
        "Parking fee",
    ],
    "Bills": [
        "Electricity bill - BSES", "Mobile recharge - Jio", "Broadband bill - Airtel",
        "Water bill", "DTH recharge", "Gas cylinder booking", "Rent payment",
    ],
    "Health": [
        "Pharmacy - Apollo", "Doctor consultation", "Health checkup",
        "Gym membership fee", "Medicines", "Dental checkup",
    ],
    "Entertainment": [
        "Movie tickets - PVR", "Netflix subscription", "Spotify premium",
        "Concert tickets", "Gaming purchase", "Bowling with friends",
    ],
    "Shopping": [
        "Amazon order", "Flipkart purchase", "Clothing - Myntra",
        "Electronics purchase", "Footwear", "Home decor items",
    ],
    "Other": [
        "Miscellaneous expense", "Gift purchase", "Donation", "ATM withdrawal fee",
        "Stationery", "Repair service",
    ],
}


def parse_args(argv):
    if len(argv) != 3:
        print(
            "Usage: /seed-expenses <user_id> <count> <months>\n"
            "Example: /seed-expenses 1 50 6"
        )
        sys.exit(1)
    try:
        user_id = int(argv[0])
        count = int(argv[1])
        months = int(argv[2])
    except ValueError:
        print(
            "Usage: /seed-expenses <user_id> <count> <months>\n"
            "Example: /seed-expenses 1 50 6"
        )
        sys.exit(1)
    return user_id, count, months


def verify_user_exists(connection, user_id):
    row = connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    return row is not None


def weighted_category():
    categories = list(CATEGORY_WEIGHTS.keys())
    weights = list(CATEGORY_WEIGHTS.values())
    return random.choices(categories, weights=weights, k=1)[0]


def random_date_within_months(months):
    now = datetime.now()
    start = now - timedelta(days=months * 30)
    delta_days = (now - start).days
    random_offset = random.randint(0, max(delta_days, 0))
    return start + timedelta(days=random_offset)


def generate_expenses(user_id, count, months):
    expenses = []
    for _ in range(count):
        category = weighted_category()
        low, high = CATEGORY_RANGES[category]
        amount = round(random.uniform(low, high), 2)
        description = random.choice(DESCRIPTIONS[category])
        expense_date = random_date_within_months(months).strftime("%Y-%m-%d")
        # Matches expenses table column order: user_id, amount, category, date, description
        expenses.append((user_id, amount, category, expense_date, description))
    return expenses


def insert_expenses(connection, expenses):
    """Insert all expenses in a single transaction; roll back on any failure."""
    try:
        connection.execute("BEGIN")
        connection.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            expenses,
        )
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Insert failed, rolled back transaction: {e}")
        sys.exit(1)


def main():
    user_id, count, months = parse_args(sys.argv[1:])

    connection = get_db()

    if not verify_user_exists(connection, user_id):
        print(f"No user found with id {user_id}.")
        connection.close()
        sys.exit(1)

    expenses = generate_expenses(user_id, count, months)
    insert_expenses(connection, expenses)

    dates = sorted(e[3] for e in expenses)
    print(f"Inserted {len(expenses)} expenses for user_id={user_id}.")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print("Sample of 5 inserted records:")
    for row in random.sample(expenses, min(5, len(expenses))):
        uid, amount, category, expense_date, description = row
        print(f"  [{expense_date}] {category} - ₹{amount} - {description}")

    connection.close()


if __name__ == "__main__":
    main()