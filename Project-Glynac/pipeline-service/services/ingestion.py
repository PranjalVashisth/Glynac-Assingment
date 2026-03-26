import os
import requests
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert   # PostgreSQL-specific upsert

from models.customer import Customer

# URL of the Flask mock server (set via env or default for local dev)
FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://mock-server:5000")


def fetch_all_customers() -> list[dict]:
    """
    Fetch every customer from the Flask API by walking through all pages.

    The Flask API returns:
        { "data": [...], "total": N, "page": P, "limit": L }

    We keep requesting the next page until we have collected all records.
    """
    all_customers = []
    page  = 1
    limit = 10    # fetch 10 per page

    while True:
        url = f"{FLASK_BASE_URL}/api/customers?page={page}&limit={limit}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()           # raises HTTPError for 4xx/5xx
        body = response.json()

        batch = body.get("data", [])
        all_customers.extend(batch)

        # Stop when we have fetched everything
        total = body.get("total", 0)
        if len(all_customers) >= total or len(batch) == 0:
            break

        page += 1   # move to the next page

    return all_customers


def _parse_customer(raw: dict) -> dict:
    """
    Convert raw JSON dict values to Python types that SQLAlchemy expects.
    e.g. date strings → date objects, numeric strings → Decimal.
    """
    dob = raw.get("date_of_birth")
    created = raw.get("created_at")

    return {
        "customer_id":     raw["customer_id"],
        "first_name":      raw["first_name"],
        "last_name":       raw["last_name"],
        "email":           raw["email"],
        "phone":           raw.get("phone"),
        "address":         raw.get("address"),
        "date_of_birth":   date.fromisoformat(dob)      if dob     else None,
        "account_balance": Decimal(str(raw["account_balance"])) if raw.get("account_balance") is not None else None,
        "created_at":      datetime.fromisoformat(created) if created else None,
    }


def upsert_customers(db: Session, customers: list[dict]) -> int:
    """
    Insert customers into PostgreSQL.
    If a customer with the same customer_id already exists, UPDATE their fields.
    This is called an UPSERT (UPDATE + INSERT).

    Returns the number of records processed.
    """
    if not customers:
        return 0

    parsed = [_parse_customer(c) for c in customers]

    # Build a PostgreSQL INSERT … ON CONFLICT (customer_id) DO UPDATE statement
    stmt = insert(Customer).values(parsed)
    stmt = stmt.on_conflict_do_update(
        index_elements=["customer_id"],   # conflict on this primary key
        set_={                            # columns to update on conflict
            "first_name":      stmt.excluded.first_name,
            "last_name":       stmt.excluded.last_name,
            "email":           stmt.excluded.email,
            "phone":           stmt.excluded.phone,
            "address":         stmt.excluded.address,
            "date_of_birth":   stmt.excluded.date_of_birth,
            "account_balance": stmt.excluded.account_balance,
            "created_at":      stmt.excluded.created_at,
        },
    )

    db.execute(stmt)
    db.commit()
    return len(parsed)
