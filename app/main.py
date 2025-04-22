from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from app.models import ChatRequest
from app.embedding import process_pdf
from app.chat import chat_with_gpt
from app.bulk_embed import process_bulk_embedding
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

@app.get("/", tags=["Health"])
def root():
    return {"status": "Flooring AI backend is running"}

@app.post("/embed/", tags=["Embeddings"], summary="Embed PDF brochure")
def embed_pdf(file_path: str):
    return process_pdf(file_path)

@app.post("/bulk-embed/", tags=["Embeddings"], summary="Embed multiple brochures from Excel")
def bulk_embed(excel_url: str):
    return process_bulk_embedding(excel_url)

@app.post("/chat/", tags=["Chat"], summary="Ask a flooring-related question")
async def chat(request: ChatRequest):
    user_message = request.message
    response = chat_with_gpt(user_message)
    return {"reply": response}

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
            print(f"[WebSocket] Received: {data}")
            reply = chat_with_gpt(data)
            await websocket.send_text(reply)
        except Exception as e:
            print(f"[WebSocket] Error: {e}")
            break