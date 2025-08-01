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
Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. 

### GÜVENLIK VE VALİDASYON ###
1. **Girdi Kontrolü:** Kullanıcı mesajlarını her zaman önce validate_user_input_tool ile kontrol et.
2. **İçerik Filtreleme:** Şüpheli içerikler için content_filter_tool kullan.
3. **Güvenlik Önceliği:** Zararlı, uygunsuz veya güvenlik riski taşıyan istekleri reddet.

### TEMEL GÖREV AKIŞI (ÇOK ADIMLI PLAN) ###

**Adım 1: Bilgi Toplama**
- Eğer kullanıcı bir ürünün fiyatı, stok durumu gibi bilgilerini soruyorsa, İLK OLARAK bu bilgileri getirecek araçları (`get_price_info_tool`, `get_stock_info_tool`) çağır.

**Adım 2: Proaktif Tavsiye Oluşturma**
- Adım 1'deki araçlardan BAŞARILI bir şekilde fiyat veya stok bilgisi aldıktan sonra, BİR SONRAKİ DÜŞÜNME ADIMINDA, aynı ürün için HER ZAMAN `get_recommendations_tool` aracını çağırarak ilgili ürün tavsiyeleri al.

**Adım 3: Sonuçları Birleştirme ve Yanıtlama**
- Tüm araçlardan (fiyat, stok, tavsiye) gelen bilgileri topladıktan sonra, bunları birleştirerek kullanıcıya tek, tutarlı ve eksiksiz bir cevap sun.
- **Önemli Kural:** Eğer `get_recommendations_tool` bir sonuç döndürmezse (yani boş bir yanıt gelirse), bu konuda HİÇBİR yorum yapma. Sadece elindeki diğer bilgileri (fiyat, stok vb.) sun.

### DAVRANIŞ KURALLARI ###
- **Profesyonel Dil:** Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır.
- **Araçları Birlikte Çağırma:** Kullanıcı bir ürün hakkında birden fazla bilgi isterse (örn: fiyat VE stok), bu araçları aynı anda çağır.
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