# ai-service/routers/image_gen.py

from fastapi import APIRouter
from pydantic import BaseModel
import base64
import hashlib
# Servislerimizi import ediyoruz
from services.image_gen import create_image_as_base64
# ... (diğer importlar)
from services.supabase_client import get_or_upload_image_url 

router = APIRouter()

class PreviewRequest(BaseModel):
    product_name: str


# Kaydedilecek görselin Base64 verisini taşıyan model
class SaveImageRequest(BaseModel):
    base64_data_url: str

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


@router.post("/save-image", tags=["Image Generation"])
async def save_image(req: SaveImageRequest):
    """
    Frontend'den gelen Base64 formatındaki bir görseli alır.
    Bu görseli içeriğine göre benzersiz bir isimle Supabase Storage'a kaydeder
    ve herkesin erişebileceği (public) URL'ini döndürür.
    """
    try:
        # 1. Adım: İstekten gelen Base64 verisini al.
        base64_data_url = req.base64_data_url

        # 2. Adım: Görselin içeriğine göre benzersiz bir dosya adı oluştur (SHA-256 Hash).
        # Bu, kullanıcının aynı önizlemeyi birden fazla kez kaydetmesini engeller.
        header, encoded_data = base64_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)
        
        hasher = hashlib.sha256()
        hasher.update(image_bytes)
        file_name = f"{hasher.hexdigest()}.png"

        # 3. Adım: Görseli Supabase'e yükle (veya zaten varsa mevcut URL'ini al).
        print(f"💾 Önizlemeden gelen görsel '{file_name}' adıyla Supabase'e kaydediliyor...")
        public_url = get_or_upload_image_url(
            base64_data_url=base64_data_url,
            file_name=file_name
        )

        # 4. Adım: Başarılı yanıtı ve kalıcı public URL'i döndür.
        return {
            "message": "Image from preview saved successfully.",
            "image_url": public_url
        }
        
    except Exception as e:
        return {"error": str(e)}, 500