# Bu dosya, LangGraph ajanının kullanabileceği tüm araçları (@tool) tanımlar ve tek bir all_tools listesinde toplar.

from langchain_core.tools import tool

# Gerekli fonksiyonları ve nesneleri diğer modüllerden al
from ..supabase_client import (
    get_price_info,
    get_stock_info,
    get_payment_amount,
    get_item_status,
    get_refund_status,
    get_product_recommendations # <-- YENİ
)
from .vector_store import db # Kullanıma hazır veritabanı nesnesini al

@tool
def get_price_info_tool(product_name: str) -> str:
    """Bir ürünün fiyatını öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Fiyat Aracı Çağrıldı. Gelen Argüman: '{product_name}'")
    return get_price_info(product_name)

@tool
def get_stock_info_tool(product_name: str) -> str:
    """Bir ürünün stokta kaç adet olduğunu öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Stok Aracı Çağrıldı. Gelen Argüman: '{product_name}'")
    return get_stock_info(product_name)

@tool
def get_payment_amount_tool(order_id: int) -> str:
    """Bir siparişin toplam ödeme tutarını öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Ödeme Tutarı Aracı Çağrıldı. Gelen Argüman: '{order_id}'")
    return get_payment_amount(order_id)

@tool
def get_item_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün durumunu öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Ürün Durumu Aracı Çağrıldı. Gelen Argümanlar: order_id={order_id}, product_name='{product_name}'")
    return get_item_status(order_id, product_name)

@tool
def get_refund_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün iade durumunu öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ İade Durumu Aracı Çağrıldı. Gelen Argümanlar: order_id={order_id}, product_name='{product_name}'")
    return get_refund_status(order_id, product_name)

@tool
def get_recommendations_tool(product_name: str) -> str:
    """
    Bir ürünle ilgili başka ürünler önermek için kullanılır. 
    Kullanıcı bir ürün hakkında bilgi aldıktan sonra bu aracı çağırarak proaktif olarak çapraz satış fırsatı yaratabilirsin.
    """
    print(f"💡 Tavsiye Aracı Çağrıldı. Gelen Argüman: '{product_name}'")
    result = get_product_recommendations(product_name)
    print(f"💡 Tavsiye Sonucu: '{result}'") # Boş string mi geliyor?
    return result

@tool
def search_documents_tool(query: str) -> str:
    """
    Kullanıcının iade politikası, kargo süreci, şirket hakkındaki genel bilgiler, 
    kullanım koşulları veya sıkça sorulan sorular (SSS) gibi genel bir sorusu olduğunda kullanılır.
    Ürün fiyatı, stok durumu gibi spesifik veritabanı bilgileri için KULLANILMAZ.
    """
    if not db:
        return "Belge arama servisi şu anda kullanılamıyor."
    
    print(f"📄 Belge araması (RAG) yapılıyor: '{query}'")
    docs = db.similarity_search(query, k=3)
    
    if not docs:
        return "Belgelerde bu konuyla ilgili bir bilgi bulunamadı."
        
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)
    return f"Konuyla ilgili belgelerden şu bilgiler bulundu:\n\n{context}"

@tool
def validate_user_input_tool(user_message: str) -> str:
    """
    Kullanıcı girdisini doğrular ve potansiyel sorunları tespit eder.
    Bu araç, zararlı içerik, spam veya uygunsuz istekleri filtrelemek için kullanılır.
    """
    print(f"🔍 Girdi Validasyon Aracı Çağrıldı. Mesaj uzunluğu: {len(user_message)}")
    
    # Boş girdi kontrolü
    if not user_message or user_message.strip() == "":
        return "HATA: Boş mesaj tespit edildi. Kullanıcıdan geçerli bir soru istenmelidir."
    
    # Uzunluk kontrolü
    if len(user_message) > 1000:
        return "HATA: Mesaj çok uzun. Kullanıcıdan daha kısa bir mesaj istenmelidir."
    
    # Zararlı içerik kontrolü
    harmful_patterns = [
        "hack", "spam", "virus", "malware", "phishing", "scam",
        "illegal", "bomb", "weapon", "drug", "suicide"
    ]
    
    if any(pattern in user_message.lower() for pattern in harmful_patterns):
        return "HATA: Zararlı veya uygunsuz içerik tespit edildi. Bu tür sorulara yardım sağlanamaz."
    
    # Spam kontrolü (tekrarlayan karakterler)
    import re
    if re.search(r'(.)\1{10,}', user_message):  # Aynı karakter 10+ kez tekrarlanıyor
        return "HATA: Spam benzeri içerik tespit edildi."
    
    # SQL injection veya kod injection attempts
    suspicious_patterns = [
        "select ", "drop ", "insert ", "update ", "delete ",
        "union ", "script>", "javascript:", "eval(", "exec("
    ]
    
    if any(pattern in user_message.lower() for pattern in suspicious_patterns):
        return "HATA: Güvenlik riski tespit edildi. Bu tür sorgular kabul edilemez."
    
    return "GEÇERLİ: Kullanıcı girdisi tüm validasyon kontrollerini geçti."

@tool  
def content_filter_tool(text: str) -> str:
    """
    Metin içeriğini analiz eder ve uygunluk seviyesini değerlendirir.
    """
    print(f"🛡️ İçerik Filtre Aracı Çağrıldı.")
    
    # Pozitif skorlama sistemi
    score = 100
    issues = []
    
    # Küfür kontrolü (Türkçe)
    profanity_words = ["aptl", "sktir", "amk", "mk"]  # Örnek, daha kapsamlı olabilir
    found_profanity = [word for word in profanity_words if word in text.lower()]
    if found_profanity:
        score -= 30
        issues.append(f"Uygunsuz dil tespit edildi: {', '.join(found_profanity)}")
    
    # Agresif ton kontrolü
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

# Diğer modüllerin kullanması için tüm araçları tek bir listede topla
all_tools = [
    get_price_info_tool,
    get_stock_info_tool,
    get_payment_amount_tool,
    get_item_status_tool,
    get_refund_status_tool,
    get_recommendations_tool, # <-- YENİ
    search_documents_tool,
    validate_user_input_tool,  # YENİ
    content_filter_tool,       # YENİ
]