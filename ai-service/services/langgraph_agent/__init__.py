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
# YENİ: check_cache düğümünü de import ediyoruz
from .nodes import call_model, validate_input, enhanced_should_continue, summarize_tool_outputs, check_cache, cache_final_answer
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
workflow.add_node("cache", check_cache)  # YENI: Önbellek kontrolü düğümü
workflow.add_node("validate", validate_input)
workflow.add_node("agent", lambda state: call_model(state, model_with_tools))
workflow.add_node("tools", ToolNode(all_tools))
workflow.add_node("summarize", summarize_tool_outputs)
workflow.add_node("cache_and_end", cache_final_answer)

# Kenarları tanımla - YENİ: Giriş noktası artık 'validate' değil, 'cache'
workflow.set_entry_point("cache")

# Cache sonrası yönlendirme - YENİ
workflow.add_conditional_edges(
    "cache",
    lambda state: "end" if state.get("cached") else "validate"
)

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
        "cache_and_end": "cache_and_end"
    }
)

# YENİ AKIŞ: Araçlardan gelen çıktıyı doğrudan ajana göndermek yerine,
# önce özetleme düğümüne gönderiyoruz. Özetleme düğümü de çıktısını ajana iletiyor.
workflow.add_edge("tools", "summarize")
workflow.add_edge("summarize", "agent")

workflow.add_edge("cache_and_end", END)

# Grafiği çalıştırılabilir bir uygulama haline getir
langgraph_app = workflow.compile()

# Modele kimliğini ve kurallarını öğreten sistem talimatı
SYSTEM_INSTRUCTION = """
### KİMLİK VE GÖREV TANIMI ###
Sen, bir e-ticaret platformunun yardımsever ve profesyonel bir müşteri hizmetleri asistanısın. 
Görevin, kullanıcının sorusunu yanıtlamak için gerekli tüm bilgileri toplamak ve ardından bu bilgileri tek bir, tutarlı cevapta birleştirmektir.

### GÜVENLIK VE VALİDASYON ###
- Kullanıcı mesajlarını her zaman önce `validate_user_input_tool` ile kontrol et.
- Zararlı veya uygunsuz istekleri her zaman reddet.

### TEMEL GÖREV AKIŞI ###

**Adım 1: Temel Ürün Bilgisini Al**
- Kullanıcı bir ürün hakkında bilgi istediğinde, ilk görevin **HER ZAMAN** `get_product_info_tool` aracını kullanarak o ürünün fiyat ve stok gibi temel bilgilerini almaktır.

**Adım 2: Proaktif Olarak Tavsiye Al (Eğer Uygunsa)**
- Eğer Adım 1'deki araç sana **tek bir ürün hakkında** bilgi verdiyse (bir liste veya tablo değil), o zaman ikinci görevin, **BİR SONRAKİ DÜŞÜNME ADIMINDA**, aynı ürün için `get_recommendations_tool` aracını çağırarak ilgili başka ürünler hakkında tavsiye almaktır.

**Adım 3: Tüm Bilgileri Birleştir ve Yanıtla (Nihai Adım)**
- Gerekli tüm araçları çağırdıktan ve elindeki tüm bilgileri (temel ürün bilgisi + tavsiyeler) topladıktan sonra, bu bilgileri birleştirerek kullanıcıya kibar ve eksiksiz bir nihai cevap oluştur.
- **Örnek Yanıt Formatı:** "[Temel ürün bilgisi cümlesi]. Bununla ilgilenenler şunları da beğendi: [tavsiye edilen ürünler]."

### ÖNEMLİ KURALLAR ###
- Eğer `get_recommendations_tool` bir sonuç döndürmezse (yani boş bir yanıt gelirse), tavsiyelerden hiç bahsetme. Sadece elindeki diğer bilgileri sun.
- Kullanıcıya asla bir aracın ham çıktısını doğrudan gösterme. Her zaman bilgileri birleştirip düzgün bir cümle haline getir.
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
        # Akıştan gelen çıktıyı kontrol et. Anahtar, çalışan düğümün adıdır.
        
        # Yanıt 'agent' düğümünden mi geliyor? (Önbellek MISS durumu)
        if "agent" in output:
            agent_output = output["agent"]
            # Sadece modelin son, nihai cevabını (araç çağırmadığı zaman) kullanıcıya gönder
            if isinstance(agent_output, dict) and "messages" in agent_output:
                last_message = agent_output["messages"][-1]
                if not last_message.tool_calls and last_message.content:
                    yield last_message.content

        # Yanıt 'cache' düğümünden mi geliyor? (Önbellek HIT durumu)
        elif "cache" in output:
            cache_output = output["cache"]
            # 'cached' bayrağı True ise, bu bir önbellek hitidir ve yanıtı gönderebiliriz.
            if isinstance(cache_output, dict) and cache_output.get("cached"):
                last_message = cache_output["messages"][-1]
                if last_message.content:
                    yield last_message.content