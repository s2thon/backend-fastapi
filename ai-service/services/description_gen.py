# LLM açıklama üretimi

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_description(title, category, brand):
    prompt = f"""
    Ürün adı: {title}
    Kategori: {category}
    Marka: {brand}

    Yukarıdaki bilgilerle SEO uyumlu, yaratıcı ve ikna edici bir ürün açıklaması yaz.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI Hatası: {str(e)}"
