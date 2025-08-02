# app/nodes/validate_input.py

from langchain_core.messages import AIMessage
from ..graph_state import GraphState

def validate_input(state: GraphState) -> dict:
    """
    Kullanıcı girdisini doğrular. Zararlı/uygunsuz içerik, çok uzun mesajlar 
    veya boş girdileri kontrol ederek grafiği erken sonlandırabilir.
    """
    print("🛡️ Girdi Validasyonu Başladı...")
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, 'content') else ""
    
    error_message = None

    if not content or not content.strip():
        error_message = "Lütfen bir soru veya mesaj yazın."
    elif len(content) > 1000:
        error_message = "Mesajınız çok uzun. Lütfen daha kısa bir mesaj gönderin."
    else:
        harmful_keywords = ["hack", "spam", "virus", "malware", "phishing", "scam"]
        if any(keyword in content.lower() for keyword in harmful_keywords):
            error_message = "Bu tür içerikler için yardım sağlayamam. Lütfen uygun bir soru sorun."

    if error_message:
        print(f"❌ Validasyon Başarısız: {error_message}")
        return {
            "messages": [AIMessage(content=error_message)],
            "validation_error": True
        }
    
    print("✅ Validasyon Başarılı.")
    # validation_error'ı False olarak ayarlamak, koşullu kenarlarda kontrolü kolaylaştırır.
    return {"validation_error": False}