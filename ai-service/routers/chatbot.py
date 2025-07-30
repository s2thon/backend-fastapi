# /chat

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_chat import rag_chat  

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/rag")
def chat_with_context(request: ChatRequest):
    response = rag_chat(request.message)
    return {"response": response}
