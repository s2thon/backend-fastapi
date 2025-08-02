from langchain_core.tools import tool

@tool  
def content_filter_tool(text: str) -> str:
    """
    Metin içeriğini analiz eder ve uygunluk seviyesini değerlendirir.
    """
    # ... (fonksiyonun geri kalanı aynı, değişiklik yok) ...
    print(f"🛡️ İçerik Filtre Aracı Çağrıldı.")
    score = 100
    issues = []
    profanity_words = ["aptl", "sktir", "amk", "mk"]
    found_profanity = [word for word in profanity_words if word in text.lower()]
    if found_profanity:
        score -= 30
        issues.append(f"Uygunsuz dil tespit edildi: {', '.join(found_profanity)}")
    aggressive_indicators = ["zorla", "hemen", "acil", "!!!", "???"]
    found_aggressive = [indicator for indicator in aggressive_indicators if indicator in text.lower()]
    if found_aggressive:
        score -= 10
        issues.append("Agresif ton tespit edildi")
    if score >= 80:
        return "İÇERİK UYGUN: Metin analizi başarılı."
    elif score >= 60:
        return f"İÇERİK ŞÜPHELI: {', '.join(issues)}. Dikkatli yanıt verilmeli."
    else:
        return f"İÇERİK UYGUNSUZ: {', '.join(issues)}. İstek reddedilmelidir."