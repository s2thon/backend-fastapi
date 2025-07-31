# Bu dosya, grafiğin mantığını içeren düğüm fonksiyonlarını (call_model, should_continue) barındırır.

from typing import Literal
from .graph_state import GraphState

def should_continue(state: GraphState) -> Literal["tools", "end"]:
    """
    Modelin son çıktısını analiz eder: Araç mı çağıracak, yoksa konuşma bitti mi?
    """
    last_message = state["messages"][-1]
    # Eğer modelin son mesajı bir veya daha fazla araç çağrısı içeriyorsa, 'tools' düğümüne git.
    if last_message.tool_calls:
        return "tools"
    # Aksi takdirde akışı sonlandır.
    return "end"

def call_model(state: GraphState, model_with_tools):
    """
    LLM'i (yapay zeka modelini) çağıran ana düğüm.
    Modeli dışarıdan parametre olarak alarak daha esnek bir yapı sunar.
    """
    # Mevcut sohbet geçmişini al
    messages = state["messages"]
    # Modeli bu geçmişle çağır ve yanıtını al
    response = model_with_tools.invoke(messages)
    # Gelen yanıtı mesaj listesine eklenmek üzere döndür
    return {"messages": [response]}