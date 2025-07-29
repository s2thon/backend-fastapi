# /chat

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chatbot import get_chat_response
from services.rag_chat import rag_chat  

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat(request: ChatRequest):
    response = get_chat_response(request.message)
    return {"response": response}

@router.post("/rag")
def chat_with_context(request: ChatRequest):
    response = rag_chat(request.message)
    return {"response": response}
