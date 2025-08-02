# app/nodes/call_model.py

from ..graph_state import GraphState

def call_model(state: GraphState, model_with_tools):
    """
    LLM'i (yapay zeka modelini) çağıran ana düğüm.
    Modeli dışarıdan parametre olarak alarak daha esnek bir yapı sunar.
    Bu düğüm, orkestratörde lambda ile sarılarak model parametresini alır.
    """
    print("🤖 Model Çağrılıyor...")
    
    # Mevcut sohbet geçmişini al
    messages = state["messages"]
    
    # Modeli bu geçmişle çağır ve yanıtını al
    response = model_with_tools.invoke(messages)
    
    # Gelen yanıtı mesaj listesine eklenmek üzere döndür
    return {"messages": [response]}