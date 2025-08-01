# Bu dosya, projenin orkestratörüdür. 
# Diğer modüllerden aldığı hazır bileşenleri (model, araçlar, düğümler) birleştirerek LangGraph uygulamasını oluşturur ve çalıştırır.

import os
from dotenv import load_dotenv

# LangChain ve LangGraph temel bileşenleri
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Kendi oluşturduğumuz modüller (artık hepsi aynı paketin içinde)
from .tools import all_tools
from .nodes import call_model, validate_input, enhanced_should_continue
from .graph_state import GraphState

load_dotenv()

# 1. Modeli Yapılandır
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.1,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
# Modeli, tools.py'dan gelen araçları kullanabilecek şekilde bağla
model_with_tools = model.bind_tools(all_tools)

# 2. Gelişmiş Grafiği Oluştur
workflow = StateGraph(GraphState)

# Düğümleri ekle
workflow.add_node("validate", validate_input)
workflow.add_node("agent", lambda state: call_model(state, model_with_tools))
workflow.add_node("tools", ToolNode(all_tools))

# Kenarları tanımla
workflow.set_entry_point("validate")

# Validasyon sonrası yönlendirme
workflow.add_conditional_edges(
    "validate",
    lambda state: "agent" if not state.get("validation_error") else "end"
)

# Ana ajan karar verme
workflow.add_conditional_edges(
    "agent", 
    enhanced_should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

workflow.add_edge("tools", "agent")

# Grafiği çalıştırılabilir bir uygulama haline getir
langgraph_app = workflow.compile()

# Modele kimliğini ve kurallarını öğreten sistem talimatı
SYSTEM_INSTRUCTION = """
### KİMLİK VE GÖREV TANIMI ###
Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. 

### GÜVENLIK VE VALİDASYON ###
1. **Girdi Kontrolü:** Kullanıcı mesajlarını her zaman önce validate_user_input_tool ile kontrol et.
2. **İçerik Filtreleme:** Şüpheli içerikler için content_filter_tool kullan.
3. **Güvenlik Önceliği:** Zararlı, uygunsuz veya güvenlik riski taşıyan istekleri reddet.

### DAVRANIŞ KURALLARI ###
1. **Profesyonel Dil:** Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır.
2. **Araç Kullanım Önceliği:** Kullanıcı bir ürünün fiyatını, stokunu, sipariş durumunu sorduğunda araçları kullan.
3. **Güvenlik Odaklı:** Her türlü güvenlik tehdidine karşı proaktif ol.
"""

# 3. FastAPI Router'ı Tarafından Çağrılacak Ana Fonksiyon
async def run_langgraph_chat_async(user_input: str):
    """
    LangGraph uygulamasını çalıştırır ve yanıtları akış halinde döndürür.
    Sohbeti sistem talimatı ile başlatır.
    """
    inputs = {
        "messages": [
            SystemMessage(content=SYSTEM_INSTRUCTION),
            HumanMessage(content=user_input)
        ]
    }
    # .astream() metodu, yanıtın adımlarını asenkron bir akış olarak almanızı sağlar
    async for output in langgraph_app.astream(inputs):
        if "agent" in output:
            last_message = output["agent"]["messages"][-1]
            # Sadece modelin son, nihai cevabını (araç çağırmadığı zaman) kullanıcıya gönder
            if not last_message.tool_calls and last_message.content:
                yield last_message.content