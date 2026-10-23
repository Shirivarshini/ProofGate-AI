import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, OrderModel, CustomerModel

SQLALCHEMY_DATABASE_URL = "sqlite:///./proofgate.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Seed Customers if empty
    if db.query(CustomerModel).count() == 0:
        cust_path = "../data/customers.json"
        if os.path.exists(cust_path):
            with open(cust_path, "r") as f:
                customers = json.load(f)
                for c in customers:
                    db.add(CustomerModel(
                        customer_id=c.get("customer_id") or c.get("id"),
                        name=c.get("name"),
                        email=c.get("email")
                    ))
            db.commit()
            print("👥 Seeded customers into SQLite database.")

    # Seed Orders if empty
    if db.query(OrderModel).count() == 0:
        orders_path = "../data/orders.json"
        if os.path.exists(orders_path):
            with open(orders_path, "r") as f:
                orders = json.load(f)
                for o in orders:
                    db.add(OrderModel(
                        order_id=o.get("order_id") or o.get("id"),
                        customer_id=o.get("customer_id"),
                        status=o.get("status"),
                        amount=float(o.get("amount") or o.get("total") or 0.0),
                        currency=o.get("currency", "INR"),
                        created_at=o.get("created_at") or o.get("date", "")
                    ))
            db.commit()
            print("📦 Seeded orders into SQLite database.")

    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()