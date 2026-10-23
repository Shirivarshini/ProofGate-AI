from sqlalchemy import Column, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OrderModel(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    status = Column(String)
    amount = Column(Float)
    currency = Column(String, default="INR")
    created_at = Column(String)

class CustomerModel(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String, primary_key=True, index=True)
    tool_name = Column(String)
    decision = Column(String)
    reason_codes = Column(Text)
    timestamp = Column(String)

class TokenStoreModel(Base):
    __tablename__ = "token_store"

    token = Column(String, primary_key=True, index=True)
    order_id = Column(String)
    is_spent = Column(Boolean, default=False)