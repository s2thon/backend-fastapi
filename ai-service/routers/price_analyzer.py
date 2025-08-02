# ai-service/routers/price_analyzer.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..services.price_analyzer import analyze_product_price
# YENİ: Güvenlik bağımlılığı importu
from ..services.langgraph_agent.security import get_current_user_claims, UserClaims

router = APIRouter()

class PriceRequest(BaseModel):
    product_name: str
    price: float

@router.post("/analyze-price", tags=["Price Analysis"])
def analyze_price_endpoint(
    req: PriceRequest,
    # YENİ: Güvenlik katmanı eklendi.
    claims: UserClaims = Depends(get_current_user_claims)
):
    """Kimliği doğrulanmış bir satıcı için fiyat analizi yapar."""
    print(f"Seller (ID: {claims.user_id}) is analyzing price for: {req.product_name}")
    
    # GÜNCELLEME: Servis katmanına user_id'yi de iletin.
    # Not: analyze_product_price fonksiyonunu da user_id alacak şekilde güncellemeniz gerekir.
    return analyze_product_price(req, user_id=claims.user_id)