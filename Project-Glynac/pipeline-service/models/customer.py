from sqlalchemy import Column, String, Text, Date, DECIMAL, TIMESTAMP
from database import Base


class Customer(Base):
    """
    SQLAlchemy ORM model that maps to the 'customers' table in PostgreSQL.
    Each attribute corresponds to one column.
    """
    __tablename__ = "customers"

    customer_id     = Column(String(50),  primary_key=True)          # unique ID
    first_name      = Column(String(100), nullable=False)
    last_name       = Column(String(100), nullable=False)
    email           = Column(String(255), nullable=False)
    phone           = Column(String(20))
    address         = Column(Text)
    date_of_birth   = Column(Date)
    account_balance = Column(DECIMAL(15, 2))
    created_at      = Column(TIMESTAMP)
