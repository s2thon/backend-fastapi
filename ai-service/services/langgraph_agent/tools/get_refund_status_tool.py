from langchain_core.tools import tool
from ...supabase_client import get_refund_status

@tool
def get_refund_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün iade durumunu öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ İade Durumu Aracı Çağrıldı. Argümanlar: order_id={order_id}, product_name='{product_name}'")
    return get_refund_status(order_id, product_name)