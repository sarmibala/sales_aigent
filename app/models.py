# app/models.py

from pydantic import BaseModel
from enum import Enum

class IndexName(str, Enum):
    all_products = "all-products"
    soft_surface = "soft-surface"
    hard_surface = "hard-surface"

class EmbedRequest(BaseModel):
    file_path: str
    index_name: IndexName

class BulkEmbedRequest(BaseModel):
    excel_url: str
    index_name: IndexName

class ChatRequest(BaseModel):
    message: str
    index_name: IndexName