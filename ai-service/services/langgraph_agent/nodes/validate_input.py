# app/nodes/validate_input.py

from langchain_core.messages import AIMessage
from ..graph_state import GraphState

def validate_input(state: GraphState) -> dict:
    """
    Kullanıcı girdisini doğrular. Zararlı/uygunsuz içerik, küfür, çok uzun mesajlar 
    veya boş girdileri kontrol ederek grafiği erken sonlandırabilir.
    """
    print("\n--- 🛡️ Gelişmiş Girdi Validasyonu Devrede ---")
    
    # State'ten son kullanıcı mesajını al
    last_message = state["messages"][-1]
    # Mesajın içeriğini güvenli bir şekilde al
    content = last_message.content if hasattr(last_message, 'content') else ""
    
    error_message = None

    # 1. Boş Mesaj Kontrolü
    if not content or not content.strip():
        error_message = "Lütfen bir soru veya mesaj yazın."
    
    # 2. Uzunluk Kontrolü
    elif len(content) > 1000:
        error_message = "Mesajınız çok uzun. Lütfen daha kısa bir mesaj gönderin."
    
    # 3. Zararlı Anahtar Kelime Kontrolü
    else:
        harmful_keywords = ["hack", "spam", "virus", "malware", "phishing", "scam"]
        if any(keyword in content.lower() for keyword in harmful_keywords):
            error_message = "Bu tür içerikler için yardım sağlayamam. Lütfen uygun bir soru sorun."
    
    # --- YENİ EKLENEN KÜFÜR KONTROLÜ ---
    # `error_message` henüz ayarlanmadıysa bu kontrolü yap
    if not error_message:
        # Kendi küfür listenizi buraya ekleyebilir veya genişletebilirsiniz
        profanity_words = [
            "amk", "mk", "siktir", "aq", "aptal", "salak", "gerizekalı", "pezevenk",
            "orospu", "kahpe", "ibne", "piç", "yavşak", "göt", "sikerim", "sikeyim",
            "ananı", "babanı", "sikik", "amına", "götveren", "şerefsiz", "bok", "sıçmak",
            "zavallı", "dangalak", "mal", "öküz", "eşşek", "keriz", "kaltak", "puşt"
        ]
        # Metni küçük harfe çevirerek ve kelimelere ayırarak daha iyi bir kontrol yapalım
        message_words = set(content.lower().split())
        
        # Kelime listesinde küfür olup olmadığını kontrol et
        if not message_words.isdisjoint(profanity_words):
             error_message = "Üzgünüm, bu tür bir ifadeye yanıt veremem. Lütfen daha uygun bir dil kullanın."
    # --- KONTROL SONU ---


    # Eğer herhangi bir kontrol sonucunda hata bulunduysa, grafiği sonlandıracak mesajı hazırla
    if error_message:
        print(f"❌ Validasyon Başarısız: {error_message}")
        return {
            "messages": [AIMessage(content=error_message)],
            "validation_error": True # Bu state, grafiğin durmasını sağlar
        }
    
    print("✅ Validasyon Başarılı.")
    # Hiçbir sorun yoksa, hata olmadığını belirterek devam et
    return {"validation_error": False}