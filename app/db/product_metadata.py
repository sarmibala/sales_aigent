from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.product import Product

def search_product_metadata(session: Session, filters: dict, limit=5):
    print(f"[DB] Searching with filters: {filters}")
    conditions = []
    for field, value in filters.items():
        if hasattr(Product, field):
            conditions.append(getattr(Product, field).ilike(f"%{value}%"))

    if not conditions:
        return []

    return session.query(Product).filter(and_(*conditions)).limit(limit).all()
