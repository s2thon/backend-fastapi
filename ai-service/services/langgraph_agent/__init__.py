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
from .nodes import should_continue, call_model
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

# 2. Grafiği Oluştur ve Düğümleri Birleştir
workflow = StateGraph(GraphState)

# Düğümleri ekle:
# - 'agent' düğümü, modelimizi çağıran fonksiyondur.
# - 'tools' düğümü, LangGraph'ın hazır aracıdır ve tüm araçlarımızı çalıştırır.
workflow.add_node("agent", lambda state: call_model(state, model_with_tools))
workflow.add_node("tools", ToolNode(all_tools))

# Kenarları ve akışı tanımla
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")

# Grafiği çalıştırılabilir bir uygulama haline getir
langgraph_app = workflow.compile()

# Modele kimliğini ve kurallarını öğreten sistem talimatı
SYSTEM_INSTRUCTION = """
### KİMLİK VE GÖREV TANIMI ###
Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. Görevin, kullanıcılardan gelen soruları sana verilen araçları kullanarak doğru bir şekilde yanıtlamaktır.

### DAVRANIŞ KURALLARI ###
1.  **Profesyonel Dil:** Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır.
2.  **Araç Kullanım Önceliği:** Kullanıcı bir ürünün fiyatını, stokunu, sipariş durumunu, iade detayını veya iade/kargo gibi genel politikaları sorduğunda, bu bilgileri tahmin etmek yerine sana verilen araçları ('tools') kullanmak zorundasın.
3.  **Net ve Odaklı Cevap:** Sadece sorulan soruya odaklan. Araçlardan gelen bilgiyi temiz ve anlaşılır bir şekilde kullanıcıya sun.
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