# ai-service/routers/image_gen.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import base64
import hashlib
from ..services.image_gen import create_image_as_base64
from ..services.supabase_client import get_or_upload_image_url
# YENİ: Güvenlik bağımlılığı importu
from ..services.langgraph_agent.security import get_current_user_claims, UserClaims

router = APIRouter()

class PreviewRequest(BaseModel):
    product_name: str

class SaveImageRequest(BaseModel):
    base64_data_url: str

@router.post("/preview-image", tags=["Image Generation"])
async def preview_image(
    req: PreviewRequest,
    # YENİ: Güvenlik katmanı eklendi.
    claims: UserClaims = Depends(get_current_user_claims)
):
    """Kimliği doğrulanmış satıcı için bir görsel önizlemesi oluşturur."""
    try:
        print(f"Seller (ID: {claims.user_id}) is previewing an image for: {req.product_name}")
        prompt = f"High-quality product shot of {req.product_name}, white background, commercial photography, 4k"
        base64_data_url = create_image_as_base64(prompt)
        return {
            "message": "Preview generated successfully. This image is not saved.",
            "image_data_url": base64_data_url
        }
    except Exception as e:
        return {"error": str(e)}, 500

@router.post("/save-image", tags=["Image Generation"])
async def save_image(
    req: SaveImageRequest,
    # YENİ: Güvenlik katmanı eklendi.
    claims: UserClaims = Depends(get_current_user_claims)
):
    """
    Kimliği doğrulanmış bir satıcıdan gelen görseli Supabase'e kaydeder.
    Görsel, satıcının kimliğiyle ilişkilendirilebilir.
    """
    try:
        base64_data_url = req.base64_data_url
        header, encoded_data = base64_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)
        
        hasher = hashlib.sha256()
        hasher.update(image_bytes)
        file_hash = hasher.hexdigest()

        # GÜNCELLEME: Dosya adını daha anlamlı hale getiriyoruz.
        # Örneğin: "seller_123_a1b2c3d4.png"
        # Bu, Supabase'de dosyaların kime ait olduğunu anlamayı kolaylaştırır.
        file_name = f"seller_{claims.user_id}_{file_hash[:16]}.png"

        print(f"Saving image from seller (ID: {claims.user_id}) to Supabase as '{file_name}'...")
        
        public_url = get_or_upload_image_url(
            base64_data_url=base64_data_url,
            file_name=file_name
        )
        return {
            "message": "Image from preview saved successfully.",
            "image_url": public_url
        }
    except Exception as e:
        return {"error": str(e)}, 500