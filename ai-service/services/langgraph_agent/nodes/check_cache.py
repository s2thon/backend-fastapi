import hashlib
import re
from langchain_core.messages import AIMessage

# DİKKAT: Göreceli importlar
from .persistent_cache import PersistentCacheManager
from ..graph_state import GraphState

# Bu nesne, uygulama çalıştığı sürece bir kez oluşturulur ve tüm cache düğümleri tarafından kullanılır.
cache_manager = PersistentCacheManager()

def normalize_query(query: str) -> str:
    """Kullanıcı sorgusunu önbellek araması için normalleştirir."""
    normalized = re.sub(r'[^\w\s]', '', query.lower())
    return " ".join(normalized.split())

def generate_query_hash(query: str) -> str:
    """Normalleştirilmiş sorgudan benzersiz bir hash oluşturur."""
    return hashlib.md5(normalize_query(query).encode('utf-8')).hexdigest()

def check_cache(state: GraphState) -> dict:
    """Sık sorulan sorular için önbellek kontrolü yapar."""
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) and hasattr(last_message, 'content'):
        query = last_message.content
        query_hash = generate_query_hash(query)
        cached_response = cache_manager.get(query_hash)
        
        if cached_response:
            print(f"🎯 Önbellek HIT: '{query}'")
            return {
                "messages": [AIMessage(content=f"{cached_response}")],
                "cached": True
            }
        
        print(f"❓ Önbellek MISS: '{query}'")
    return {}