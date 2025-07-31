# Bu dosya, LangGraph ajanının kullanabileceği tüm araçları (@tool) tanımlar ve tek bir all_tools listesinde toplar.

from langchain_core.tools import tool

# Gerekli fonksiyonları ve nesneleri diğer modüllerden al
from .supabase_client import (
    get_price_info,
    get_stock_info,
    get_payment_amount,
    get_item_status,
    get_refund_status
)
from .vector_store import db # Kullanıma hazır veritabanı nesnesini al

@tool
def get_price_info_tool(product_name: str) -> str:
    """Bir ürünün fiyatını öğrenmek için kullanılır."""
    return get_price_info(product_name)

@tool
def get_stock_info_tool(product_name: str) -> str:
    """Bir ürünün stokta kaç adet olduğunu öğrenmek için kullanılır."""
    return get_stock_info(product_name)

@tool
def get_payment_amount_tool(order_id: int) -> str:
    """Bir siparişin toplam ödeme tutarını öğrenmek için kullanılır."""
    return get_payment_amount(order_id)

@tool
def get_item_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün durumunu öğrenmek için kullanılır."""
    return get_item_status(order_id, product_name)

@tool
def get_refund_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün iade durumunu öğrenmek için kullanılır."""
    return get_refund_status(order_id, product_name)

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

# Diğer modüllerin kullanması için tüm araçları tek bir listede topla
all_tools = [
    get_price_info_tool,
    get_stock_info_tool,
    get_payment_amount_tool,
    get_item_status_tool,
    get_refund_status_tool,
    search_documents_tool,
]