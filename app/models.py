from pydantic import BaseModel

# Define the ChatRequest model
class ChatRequest(BaseModel):
    message: str