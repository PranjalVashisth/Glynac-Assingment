# Customer Data Pipeline

A 3-service Docker application that demonstrates a real-world data pipeline pattern.

## Architecture

```
Flask Mock Server (port 5000)
        │  GET /api/customers (paginated JSON)
        ▼
FastAPI Pipeline (port 8000)
        │  POST /api/ingest  →  reads Flask, upserts into DB
        ▼
PostgreSQL (port 5432)
        │
        ▼
FastAPI GET /api/customers  →  reads from DB and returns to client
```

## Project Structure

```
project-root/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py                  ← Flask application
│   ├── data/customers.json     ← 22 customer records
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py                 ← FastAPI application (all endpoints)
    ├── database.py             ← SQLAlchemy engine + session setup
    ├── models/
    │   └── customer.py         ← ORM model (maps to DB table)
    ├── services/
    │   └── ingestion.py        ← Fetch from Flask + upsert to Postgres
    ├── Dockerfile
    └── requirements.txt
```

## Quick Start

```bash
# Clone / unzip the project, then:
cd project-root

# Build and start all 3 services
docker-compose up --build -d

# Check logs
docker-compose logs -f
```

## Testing the API

### Flask Mock Server (port 5000)

```bash
# Health check
curl http://localhost:5000/api/health

# All customers (default page=1, limit=10)
curl http://localhost:5000/api/customers

# Page 2, 5 per page
curl "http://localhost:5000/api/customers?page=2&limit=5"

# Single customer
curl http://localhost:5000/api/customers/CUST001

# Non-existent customer → 404
curl http://localhost:5000/api/customers/CUST999
```

### FastAPI Pipeline Service (port 8000)

```bash
# Trigger ingestion (pulls from Flask, saves to PostgreSQL)
curl -X POST http://localhost:8000/api/ingest

# List customers from the database
curl "http://localhost:8000/api/customers?page=1&limit=5"

# Single customer from the database
curl http://localhost:8000/api/customers/CUST001

# Interactive API docs (open in browser)
# http://localhost:8000/docs
```

## Stopping the services

```bash
docker-compose down          # stop containers
docker-compose down -v       # also delete the database volume
```

## Key Concepts

| Concept | Where used |
|---|---|
| REST pagination | Flask `/api/customers?page=&limit=` |
| Docker multi-service | `docker-compose.yml` with 3 services |
| SQLAlchemy ORM | `models/customer.py` + `database.py` |
| PostgreSQL UPSERT | `services/ingestion.py` |
| FastAPI dependency injection | `Depends(database.get_db)` in `main.py` |
| Auto table creation | `create_all()` on FastAPI startup |
