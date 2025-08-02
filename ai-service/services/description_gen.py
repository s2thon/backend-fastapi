import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# GÜNCELLEME: Fonksiyon imzasına 'user_id' eklendi.
def generate_description(title: str, category: str, brand: str, user_id: str):
    """
    Verilen ürün bilgileri için yapay zeka kullanarak bir ürün açıklaması oluşturur.
    Artık bu işlemi hangi kullanıcının (satıcının) yaptığını da bilir.
    
    Args:
        title (str): Ürünün başlığı.
        category (str): Ürünün kategorisi.
        brand (str): Ürünün markası.
        user_id (str): İşlemi talep eden satıcının kimliği.
    """
    
    # YENİ: Hangi satıcının işlem yaptığını loglamak, denetlemek veya gelecekteki
    # özellikler (örn: kullanım istatistikleri) için harika bir yer.
    print(f"Açıklama oluşturma isteği geldi. Satıcı ID: {user_id}, Ürün: {title}")
    
    prompt = f"""
    Ürün adı: {title}
    Kategori: {category}
    Marka: {brand}

    Yukarıdaki bilgilerle SEO uyumlu, yaratıcı ve ikna edici bir ürün açıklaması yaz.
    """
    
    try:
        response = model.generate_content(prompt)
        # GÜNCELLEME: İsteğe bağlı olarak, oluşturulan bu açıklamayı veritabanına
        # bu user_id ile ilişkilendirerek kaydedebilirsiniz. Bu, satıcının
        # geçmişte oluşturduğu açıklamalara bakmasını sağlayabilir.
        # save_generation_to_db(user_id=user_id, product_title=title, description=response.text.strip())
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini API Hatası (Satıcı ID: {user_id}): {e}")
        return f"Yapay zeka ile açıklama oluşturulurken bir hata oluştu: {str(e)}"