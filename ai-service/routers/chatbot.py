# /chat

from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["Chatbot"])

@router.post("/")
def chatbot_response(prompt: str):
    return {"response": f"You said: {prompt}"}

