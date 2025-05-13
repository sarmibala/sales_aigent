# app/main.py

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
import os
import httpx
import json
import traceback

from app.models import EmbedRequest, BulkEmbedRequest, ChatRequest
from app.embedding import process_pdf
from app.chat import chat_with_gpt
from app.bulk_embed import process_bulk_embedding
from app.fetch_and_cache_products_from_crest_api import fetch_and_cache_products_from_crest_api
from app.routers import product
from app.db.database import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Flooring AI Chatbot API",
    description="This API allows users to embed flooring brochures and chat with a GPT-based assistant to get flooring recommendations.",
    version="1.0.0"
)

app.include_router(product.router)

@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "Flooring AI backend is running"}

@app.post("/embed/", tags=["Embeddings"], summary="Embed PDF brochure")
def embed_pdf(request: EmbedRequest):
    return process_pdf(request.file_path, request.index_name.value)

@app.post("/bulk-embed/", tags=["Embeddings"], summary="Embed multiple brochures from Excel")
def bulk_embed(request: BulkEmbedRequest):
    return process_bulk_embedding(request.excel_url, request.index_name.value)

@app.post("/chat/", tags=["Chat"], summary="Ask a flooring-related question")
async def chat(request: ChatRequest):
    try:
        response = chat_with_gpt(request.message, request.index_name.value)
        return {"reply": response}
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/chat-ui/", response_class=HTMLResponse, tags=["UI"])
def chat_ui():
    file_path = os.path.join(os.path.dirname(__file__), "chat.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

@app.websocket("/ws/chat/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # Extract message and index_name from the JSON payload
            user_message = payload.get("message")
            index_name = payload.get("index_name")

            if not user_message or not index_name:
                await websocket.send_text("Error: 'message' and 'index_name' are required.")
                continue

            reply = chat_with_gpt(user_message, index_name)
            await websocket.send_text(reply)

        except Exception as e:
            print(f"[WebSocket] Error: {e}")
            await websocket.send_text(f"Internal server error: {str(e)}")
            break

@app.get("/fetch-products")
async def fetch_products():
    timeout = httpx.Timeout(30.0)
    PRODUCTS_CREST_API_BASE_URL = os.getenv("PRODUCTS_CREST_API_BASE_URL")

    PRODUCTS_CREST_API_BASE_URL = f'{PRODUCTS_CREST_API_BASE_URL}api/GetProductsByBrandCodeSite/MohawkGroup/SoftSurface'

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(PRODUCTS_CREST_API_BASE_URL)
        response.raise_for_status()
        data = response.json()

    # Extract unique collection names
    collection_names = set()
    for item in data:
        collection_names.add(item.get('collectionName'))

    # Convert set to sorted list for display
    unique_collections = sorted(collection_names)

    sorted_collections = sorted(unique_collections)

    print(f"Found {len(sorted_collections)} unique Collection names")
    print(f"collection_names_from_excel_product_data ==> {sorted_collections}")

    # Return as API response
    return {"unique_collections": sorted_collections}

@app.get("/fetch-products-from-crest-api")
async def fetch_and_cache_products_from_crest_api():
    return await fetch_and_cache_products_from_crest_api()