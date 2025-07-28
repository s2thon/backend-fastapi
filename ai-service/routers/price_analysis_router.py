from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.price_scraper import analyze_market_price

router = APIRouter()

class PriceAnalysisRequest(BaseModel):
    product_name: str
    price: float
    category: str = "Genel"

@router.post("/price-analysis")
def price_analysis(payload: PriceAnalysisRequest):
    try:
        result = analyze_market_price(
            payload.product_name,
            payload.category,
            payload.price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
