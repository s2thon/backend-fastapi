from langchain_core.tools import tool
from ...supabase_client import get_item_status

@tool
def get_item_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün durumunu öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Ürün Durumu Aracı Çağrıldı. Argümanlar: order_id={order_id}, product_name='{product_name}'")
    return get_item_status(order_id, product_name)