import json
import os
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# ── Load customer data from JSON file once at startup ──────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.json")

with open(DATA_PATH, "r") as f:
    CUSTOMERS = json.load(f)   # list of dicts


# ── Helper ─────────────────────────────────────────────────────────────────────
def find_customer(customer_id: str):
    """Return a customer dict by customer_id, or None if not found."""
    for c in CUSTOMERS:
        if c["customer_id"] == customer_id:
            return c
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Simple health-check endpoint."""
    return jsonify({"status": "ok", "service": "mock-server"})


@app.route("/api/customers", methods=["GET"])
def get_customers():
    """
    Return a paginated list of customers.

    Query params:
        page  (int, default 1)  – which page to return
        limit (int, default 10) – how many records per page
    """
    # Read & validate query params
    try:
        page  = int(request.args.get("page",  1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be positive integers"}), 400

    total = len(CUSTOMERS)

    # Slice the list for the requested page
    start = (page - 1) * limit          # e.g. page=2, limit=5 → start=5
    end   = start + limit               #                         end=10
    page_data = CUSTOMERS[start:end]

    return jsonify({
        "data":  page_data,
        "total": total,
        "page":  page,
        "limit": limit,
    })


@app.route("/api/customers/<string:customer_id>", methods=["GET"])
def get_customer(customer_id: str):
    """Return a single customer by ID, or 404 if not found."""
    customer = find_customer(customer_id)
    if customer is None:
        abort(404, description=f"Customer '{customer_id}' not found.")
    return jsonify(customer)


# ── 404 error handler ──────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e)}), 404


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # host="0.0.0.0" makes Flask reachable from outside the container
    app.run(host="0.0.0.0", port=5000, debug=False)
