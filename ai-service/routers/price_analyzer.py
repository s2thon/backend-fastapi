from fastapi import APIRouter
from pydantic import BaseModel
from services.price_analyzer import analyze_product_price

router = APIRouter()

class PriceRequest(BaseModel):
    product_name: str
    price: float

@router.post("/analyze-price")
def analyze_price_endpoint(req: PriceRequest):
    return analyze_product_price(req)
