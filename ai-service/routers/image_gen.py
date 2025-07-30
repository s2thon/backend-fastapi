# ai-service/routers/image_gen.py

from fastapi import APIRouter
from pydantic import BaseModel
# Servislerimizi import ediyoruz
from services.image_gen import create_image_as_base64
# ... (diğer importlar)

router = APIRouter()

class PreviewRequest(BaseModel):
    product_name: str

@router.post("/preview-image", tags=["Image Generation"])
async def preview_image(req: PreviewRequest):
    """
    Sadece bir ürün görseli oluşturur ve önizleme için Base64 formatında geri döndürür.
    Bu aşamada hiçbir yere kayıt yapılmaz.
    """
    try:
        prompt = f"High-quality product shot of {req.product_name}, white background, commercial photography, 4k"
        
        # Servisi çağır ve doğrudan Base64 data URL'ini al
        base64_data_url = create_image_as_base64(prompt)



        return {
            "message": "Preview generated successfully. This image is not saved.",
            "image_data_url": base64_data_url
        }
        
    except Exception as e:
        return {"error": str(e)}, 500
    