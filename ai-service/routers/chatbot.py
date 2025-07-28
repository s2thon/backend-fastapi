# /chat

from fastapi import APIRouter
from pydantic import BaseModel
from services.chatbot import get_chat_response

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat(request: ChatRequest):
    response = get_chat_response(request.message)
    return {"response": response}
