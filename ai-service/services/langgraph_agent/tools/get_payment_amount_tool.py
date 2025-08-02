from langchain_core.tools import tool
from ...supabase_client import get_payment_amount

@tool
def get_payment_amount_tool(order_id: int) -> str:
    """Bir siparişin toplam ödeme tutarını öğrenmek için kullanılır."""
    print(f"🕵️‍♂️ Ödeme Tutarı Aracı Çağrıldı. Argüman: '{order_id}'")
    return get_payment_amount(order_id)