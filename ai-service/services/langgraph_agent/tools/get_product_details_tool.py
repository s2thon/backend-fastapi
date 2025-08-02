from langchain_core.tools import tool
# DİKKAT: Göreceli import. `tools` klasöründen bir üste çıkıp `supabase_client`'ı bulur.
from ...supabase_client import get_product_details_with_recommendations

@tool
def get_product_details_tool(product_name: str) -> str:
    """
    Kullanıcı bir ürün veya ürünler hakkında bilgi (fiyat, stok) veya tavsiye istediğinde kullanılır.
    Bu araç, ürün detaylarını ve eğer uygunsa tavsiyeleri tek seferde getirir.
    """
    print(f"🕵️‍♂️ Ürün Detayları Aracı Çağrıldı. Argüman: '{product_name}'")
    # Orijinal kodunuzda bu fonksiyon adı farklıydı, tutarlılık için düzelttim.
    return get_product_details_with_recommendations(product_name)