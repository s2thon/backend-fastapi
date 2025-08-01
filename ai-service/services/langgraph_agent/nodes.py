# Bu dosya, grafiğin mantığını içeren düğüm fonksiyonlarını (call_model, should_continue) barındırır.

from typing import Literal
from .graph_state import GraphState



def call_model(state: GraphState, model_with_tools):
    """
    LLM'i (yapay zeka modelini) çağıran ana düğüm.
    Modeli dışarıdan parametre olarak alarak daha esnek bir yapı sunar.
    """
    # Mevcut sohbet geçmişini al
    messages = state["messages"]
    # Modeli bu geçmişle çağır ve yanıtını al
    response = model_with_tools.invoke(messages)
    # Gelen yanıtı mesaj listesine eklenmek üzere döndür
    return {"messages": [response]}

def validate_input(state: GraphState) -> dict:
    """
    Kullanıcı girdisini doğrular ve temizler.
    Zararlı içerik, çok uzun mesajlar veya boş girdileri kontrol eder.
    """
    last_message = state["messages"][-1]
    content = last_message.content
    
    # Boş girdi kontrolü
    if not content or content.strip() == "":
        return {
            "messages": [
                {"role": "assistant", "content": "Lütfen bir soru veya mesaj yazın."}
            ],
            "validation_error": True
        }
    
    # Çok uzun mesaj kontrolü
    if len(content) > 1000:
        return {
            "messages": [
                {"role": "assistant", "content": "Mesajınız çok uzun. Lütfen daha kısa bir mesaj gönderin."}
            ],
            "validation_error": True
        }
    
    # Zararlı içerik kontrolü (geliştirilmiş)
    harmful_keywords = ["hack", "spam", "virus", "malware", "phishing", "scam"]
    if any(keyword in content.lower() for keyword in harmful_keywords):
        return {
            "messages": [
                {"role": "assistant", "content": "Bu tür içerikler için yardım sağlayamam. Lütfen uygun bir soru sorun."}
            ],
            "validation_error": True
        }
    
    # Rate limiting kontrolü (IP bazlı veya session bazlı)
    if len(content.split()) > 200:  # Çok fazla kelime
        return {
            "messages": [
                {"role": "assistant", "content": "Lütfen daha kısa ve öz bir mesaj gönderin."}
            ],
            "validation_error": True
        }
    
    # Başarılı validasyon
    return {
        "validated": True,
        "validation_error": False
    }

def enhanced_should_continue(state: GraphState) -> Literal["tools", "error", "end"]:
    """
    Basitleştirilmiş karar verme mantığı - sadece tools, error, veya end.
    """
    # Validasyon hatası kontrolü
    if state.get("validation_error"):
        return "end"
    
    last_message = state["messages"][-1]
    
    # Hata kontrolü
    if state.get("error"):
        return "error"
    
    # Araç çağrısı gerekli mi?
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    return "end"




