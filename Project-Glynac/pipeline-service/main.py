from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import database
from models.customer import Customer
from services.ingestion import fetch_all_customers, upsert_customers

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Customer Pipeline Service", version="1.0.0")


@app.on_event("startup")
def create_tables():
    """
    Called once when FastAPI starts.
    Creates the 'customers' table if it doesn't already exist in PostgreSQL.
    """
    database.Base.metadata.create_all(bind=database.engine)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "pipeline-service"}


# ── Ingest endpoint ────────────────────────────────────────────────────────────
@app.post("/api/ingest")
def ingest(db: Session = Depends(database.get_db)):
    """
    1. Fetch all customers from the Flask mock server (auto-paginated).
    2. Upsert them into PostgreSQL.
    3. Return how many records were processed.
    """
    try:
        raw_customers = fetch_all_customers()           # Step 1: pull data
        count = upsert_customers(db, raw_customers)     # Step 2: save to DB
        return {"status": "success", "records_processed": count}   # Step 3
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── List customers (paginated) ─────────────────────────────────────────────────
@app.get("/api/customers")
def list_customers(
    page:  int = Query(default=1,  ge=1, description="Page number (starts at 1)"),
    limit: int = Query(default=10, ge=1, description="Records per page"),
    db: Session = Depends(database.get_db),
):
    """
    Return a paginated list of customers stored in PostgreSQL.
    Query params: page, limit
    """
    total  = db.query(Customer).count()
    offset = (page - 1) * limit           # e.g. page=2, limit=5 → skip first 5
    rows   = db.query(Customer).offset(offset).limit(limit).all()

    # Convert ORM objects to plain dicts for JSON serialisation
    data = [
        {
            "customer_id":     r.customer_id,
            "first_name":      r.first_name,
            "last_name":       r.last_name,
            "email":           r.email,
            "phone":           r.phone,
            "address":         r.address,
            "date_of_birth":   str(r.date_of_birth)   if r.date_of_birth   else None,
            "account_balance": float(r.account_balance) if r.account_balance else None,
            "created_at":      str(r.created_at)      if r.created_at      else None,
        }
        for r in rows
    ]

    return {"data": data, "total": total, "page": page, "limit": limit}


# ── Single customer ────────────────────────────────────────────────────────────
@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(database.get_db)):
    """Return a single customer by ID; 404 if not found."""
    r = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if r is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return {
        "customer_id":     r.customer_id,
        "first_name":      r.first_name,
        "last_name":       r.last_name,
        "email":           r.email,
        "phone":           r.phone,
        "address":         r.address,
        "date_of_birth":   str(r.date_of_birth)    if r.date_of_birth   else None,
        "account_balance": float(r.account_balance) if r.account_balance else None,
        "created_at":      str(r.created_at)       if r.created_at      else None,
    }
