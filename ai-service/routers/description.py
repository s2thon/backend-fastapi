# ai-service/routers/description.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..services.description_gen import generate_description
# YENİ: Güvenlik bağımlılığı importu
from ..services.langgraph_agent.security import get_current_user_claims, UserClaims

router = APIRouter()

class Product(BaseModel):
    title: str
    category: str

@router.post("/generate-description", tags=["Product Description"])
def gen_desc(
    product: Product,
    # YENİ: Bu endpoint'i sadece JWT'si geçerli olanlar kullanabilir.
    claims: UserClaims = Depends(get_current_user_claims)
):
    """
    Kimliği doğrulanmış bir satıcı için ürün açıklaması oluşturur.
    İşlemi yapan satıcının user_id'si denetim ve gelecekteki özellikler için kullanılabilir.
    """
    # GÜNCELLEME: Servis fonksiyonuna, işlemi yapan kullanıcının kim olduğu bilgisini de iletiyoruz.
    # Not: generate_description fonksiyonunun kendisini de user_id alacak şekilde güncellemeniz gerekir.
    print(f"Seller (ID: {claims.user_id}) is generating a description for: {product.title}")
    
    desc = generate_description(
        product.title, 
        product.category, 
        user_id=claims.user_id # <-- Servise user_id'yi de geçin
    )
    return {"description": desc}