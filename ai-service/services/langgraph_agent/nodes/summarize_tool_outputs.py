# app/nodes/summarize_tool_outputs.py

from langchain_core.messages import SystemMessage, ToolMessage
from ..graph_state import GraphState

def summarize_tool_outputs(state: GraphState):
    """
    Araçlardan gelen çıktıları akıllıca birleştirir ve bir sistem mesajı oluşturur.
    - Başarılı sonuçları listeler.
    - "Bulunamadı" veya "tükendi" gibi bilgilendirici sonuçları doğru şekilde ekler.
    - Tavsiye aracından gelen boş sonuçları tamamen görmezden gelir.
    - Gerçek veritabanı hatalarını belirtir.
    """
    messages = state["messages"]
    
    # Sadece bu döngüyle ilgili ToolMessage'ları al
    # Geriye doğru giderek tool_calls içeren son AIMessage'ı bul
    last_agent_message = next((msg for msg in reversed(messages) if hasattr(msg, 'tool_calls') and msg.tool_calls), None)
    if not last_agent_message:
        return {} # İlişkili araç çağrısı bulunamadı
        
    tool_call_ids = {tc['id'] for tc in last_agent_message.tool_calls}
    # Sadece bu çağrılara ait ToolMessage'ları filtrele
    tool_outputs = [msg for msg in messages if isinstance(msg, ToolMessage) and msg.tool_call_id in tool_call_ids]
    
    if not tool_outputs:
        return {} # Özetlenecek çıktı yok

    summary_lines = []
    for output in tool_outputs:
        content = output.content.strip() if output.content else ""
        tool_name = output.name

        # Orijinal kodunuzda bu araçlar vardı, isimleri kontrol edin
        if tool_name == 'get_recommendations_tool' and not content:
            continue  # Tavsiye aracından gelen boş cevabı tamamen yoksay

        if "hatası oluştu" in content.lower():
            summary_lines.append(f"- '{tool_name}' kullanılırken bir sorun yaşandı.")
        elif content:
            summary_lines.append(f"- {content}")

    # Özetlenecek anlamlı bir bilgi yoksa, sonraki adımı karıştırmamak için boş dön.
    if not summary_lines:
        return {}

    summary = "Araçlardan şu bilgiler toplandı:\n" + "\n".join(summary_lines)
    print(f"📋 Akıllı Özetleme Tamamlandı:\n{summary}")

    return {"messages": [SystemMessage(content=summary)]}