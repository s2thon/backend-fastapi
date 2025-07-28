# /chat

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chatbot import get_chat_response
from services.rag_chat import rag_chat  
from services.price_scraper import analyze_market_price

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

class PriceAnalysisRequest(BaseModel):
    product_name: str
    price: float
    category: str = "Genel"  # opsiyonel


@router.post("/price-analysis")
def price_analysis_endpoint(payload: PriceAnalysisRequest):
    try:
        result = analyze_market_price(payload.product_name, payload.category, payload.price)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))