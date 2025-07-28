import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")  # veya flash

def get_chat_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text.strip()
    except Exception as e:
        return f"Hata: {str(e)}"
