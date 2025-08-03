from langchain_core.tools import tool
# DİKKAT: Artık `db`'yi aynı klasördeki `vector_store`'dan alıyoruz.
from ..vector_store import db

@tool
def search_documents_tool(query: str) -> str:
    """
    Kullanıcının iade politikası, kargo süreci, şirket hakkındaki genel bilgiler, 
    kullanım koşulları veya sıkça sorulan sorular (SSS) gibi genel bir sorusu olduğunda kullanılır.
    Ürün fiyatı, stok durumu gibi spesifik veritabanı bilgileri için KULLANILMAZ.
    """
    try:
        if not db:
            return "Belge arama servisi şu anda kullanılamıyor."
        
        print(f"📄 Belge araması (RAG) yapılıyor: '{query}'")
        docs = db.similarity_search(query, k=3)
        
        if not docs:
            return "Belgelerde bu konuyla ilgili bir bilgi bulunamadı."
            
        context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        return f"Konuyla ilgili belgelerden şu bilgiler bulundu:\n\n{context}"
    
    except Exception as e:
        print(f"❌ Belge arama sırasında hata: {e}")
        return "Belgeleri ararken bir sorunla karşılaşıldı. Lütfen daha sonra tekrar deneyin."