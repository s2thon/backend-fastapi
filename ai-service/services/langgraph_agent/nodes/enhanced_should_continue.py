# app/nodes/enhanced_should_continue.py

from typing import Literal
from ..graph_state import GraphState

def enhanced_should_continue(state: GraphState) -> Literal["tools", "cache_and_end"]:
    """
    Modelin yanıtını analiz ederek bir sonraki adıma karar verir.
    - Eğer model araç kullanmak istiyorsa 'tools' yoluna yönlendirir.
    - Eğer model nihai bir yanıt verdiyse 'cache_and_end' yoluna yönlendirir.
    """
    print("🚦 Karar Aşaması: Devam mı, Tamam mı?")
    last_message = state["messages"][-1]

    # Modelin son mesajı araç çağırma talimatı içeriyorsa 'tools' düğümüne git
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(" karar -> Araç Kullanılacak.")
        return "tools"
    
    # Model araç çağırmadıysa, bu nihai bir yanıttır, 'cache_and_end' düğümüne git
    print(" karar -> Nihai Yanıt, Döngü Bitiyor.")
    return "cache_and_end"