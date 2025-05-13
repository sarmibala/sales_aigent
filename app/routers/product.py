# app/routers/product.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.schemas.product import ProductSchema
from app.services import product_service
from app.db.database import get_db
from typing import List
from app.services.product_service import upsert_products_from_excel

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductSchema)
def create_product(product: ProductSchema, db: Session = Depends(get_db)):
    return product_service.create_product(db, product)

@router.get("/", response_model=List[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    return product_service.get_all_products(db)

@router.post("/upload-excel", summary="Upload product Excel and upsert into DB")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")
    result = await upsert_products_from_excel(file, db)
    return result