# app/db/product_metadata.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.product import Product

def search_product_metadata(session: Session, filters: dict, limit=5):
    print(f"[DB] Searching with filters: {filters}")
    conditions = []
    for field, value in filters.items():
        if hasattr(Product, field):
            column_attr = getattr(Product, field)
            if isinstance(value, list):
                conditions.append(column_attr.in_(value))  # Handle list values
            else:
                conditions.append(column_attr.ilike(f"%{value}%"))  # Handle string values

    if not conditions:
        return []

    return session.query(Product).filter(and_(*conditions)).limit(limit).all()
