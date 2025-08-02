from langchain_core.messages import AIMessage, HumanMessage
# DİKKAT: `check_cache` içinde oluşturulan aynı cache_manager nesnesini ve yardımcı fonksiyonları kullanıyoruz.
from .check_cache import cache_manager, generate_query_hash
from ..graph_state import GraphState

def cache_final_answer(state: GraphState) -> dict:
    """Grafiğin sonunda, nihai AI yanıtını önbelleğe alır."""
    # ... (cache_final_answer fonksiyonunun tüm içeriği buraya, değişiklik yok) ...
    tool_calls = []
    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and message.tool_calls:
            tool_calls = message.tool_calls
            break
    called_tool_names = {call['name'] for call in tool_calls}
    if 'get_stock_info_tool' in called_tool_names: # Varsayımsal stok aracı
        print("ℹ️ Yanıt, anlık bilgi içerdiği için önbelleğe alınmayacak.")
        return {}
        
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.content:
        # Hatalı/olumsuz yanıtları önbelleğe alma
        error_keywords = ["sorun", "hata", "bulunamadı", "üzgünüm"]
        if any(keyword in last_message.content.lower() for keyword in error_keywords):
            print(f"🚫 Hatalı/olumsuz yanıt önbelleğe alınmayacak.")
            return {}

        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if user_messages:
            last_user_query = user_messages[-1].content
            query_hash = generate_query_hash(last_user_query)
            cache_manager.set(query_hash, last_message.content)
            print(f"💾 Önbelleğe eklendi: '{last_user_query}'")
    return {}