import os
import requests
import base64  # <-- Base64 çevirimi için bu kütüphaneyi import ediyoruz
from dotenv import load_dotenv

load_dotenv()
STABILITY_KEY = os.getenv("STABILITY_API_KEY")

def create_image_as_base64(prompt: str) -> str:
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    
    headers = {
        "Authorization": f"Bearer {STABILITY_KEY}",
        # Accept başlığı artık 'application/json' değil, doğrudan resim verisi beklediğimizi belirtir.
        "Accept": "image/*"
    }

    payload = {
        "prompt": prompt,
        # 1. output_format'ı API'nin kabul ettiği bir değere değiştiriyoruz. 'png' iyi bir seçim.
        "output_format": "png", 
        "model": "stable-diffusion-xl-1.0-v1",
        "aspect_ratio": "1:1"
    }

    print("📡 Stability AI'ye MULTIPART/FORM-DATA istek gönderiliyor (yanıt olarak PNG bekleniyor)...")
    
    res = requests.post(url, headers=headers, data=payload, files={"none": ""})
    
    if res.status_code != 200:
        print("❌ API ERROR:", res.text)
        raise Exception(f"Image generation failed with status {res.status_code}: {res.text}")

    # 2. Yanıt artık JSON değil, bu yüzden res.content ile ham (binary) veriyi alıyoruz.
    image_bytes = res.content
    
    # 3. Aldığımız ham byte'ları Base64 formatına kendimiz çeviriyoruz.
    #    b64encode() byte alır, byte döndürür. Bunu string'e çevirmek için .decode('utf-8') kullanırız.
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    print("✅ Görsel başarıyla alındı ve Base64'e çevrildi.")
        
    return f"data:image/png;base64,{base64_image}"
