# app/nodes/enhanced_should_continue.py

from typing import Literal
from ..graph_state import GraphState
from langchain_core.messages import AIMessage

def enhanced_should_continue(state: GraphState) -> Literal["tools", "cache_and_end"]:
    """
    Modelin yanıtını analiz ederek bir sonraki adıma karar verir.
    - Eğer model araç kullanmak istiyorsa 'tools' yoluna yönlendirir.
    - Eğer model nihai bir yanıt verdiyse 'cache_and_end' yoluna yönlendirir.
    - AI'ın son yanıtında araç çağrısı olup olmadığını GÜVENLİ bir şekilde kontrol eder.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # --- ANA GÜNCELLEME BURADA ---
    # .tool_calls özelliğine erişmeden önce, son mesajın bir AIMessage olduğundan
    # ve tool_calls özelliğinin dolu olduğundan emin oluyoruz.
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Eğer bu koşul doğruysa, güvenle "tools" düğümüne gidebiliriz.
        return "tools"
    # --- GÜNCELLEME SONU ---
    
    # Eğer yukarıdaki koşul sağlanmazsa, araç çağrısı yoktur, bitirebiliriz.
    return "cache_and_end"