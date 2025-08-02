import re
from langchain_core.tools import tool

@tool
def validate_user_input_tool(user_message: str) -> str:
    """
    Kullanıcı girdisini doğrular ve potansiyel sorunları tespit eder.
    Bu araç, zararlı içerik, spam veya uygunsuz istekleri filtrelemek için kullanılır.
    """
    # ... (fonksiyonun geri kalanı aynı, değişiklik yok) ...
    print(f"🔍 Girdi Validasyon Aracı Çağrıldı. Mesaj uzunluğu: {len(user_message)}")
    if not user_message or user_message.strip() == "":
        return "HATA: Boş mesaj tespit edildi."
    if len(user_message) > 1000:
        return "HATA: Mesaj çok uzun."
    harmful_patterns = ["hack", "spam", "virus", "malware", "phishing", "scam", "illegal", "bomb", "weapon", "drug", "suicide"]
    if any(pattern in user_message.lower() for pattern in harmful_patterns):
        return "HATA: Zararlı veya uygunsuz içerik tespit edildi."
    if re.search(r'(.)\1{10,}', user_message):
        return "HATA: Spam benzeri içerik tespit edildi."
    suspicious_patterns = ["select ", "drop ", "insert ", "update ", "delete ", "union ", "script>", "javascript:", "eval(", "exec("]
    if any(pattern in user_message.lower() for pattern in suspicious_patterns):
        return "HATA: Güvenlik riski tespit edildi."
    return "GEÇERLİ: Kullanıcı girdisi tüm validasyon kontrollerini geçti."