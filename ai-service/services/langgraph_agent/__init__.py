# Bu dosya, projenin orkestratörüdür. 
# Diğer modüllerden aldığı hazır bileşenleri (model, araçlar, düğümler) birleştirerek LangGraph uygulamasını oluşturur ve çalıştırır.

import os
from dotenv import load_dotenv

# LangChain ve LangGraph temel bileşenleri
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode

# Kendi oluşturduğumuz modüller (artık hepsi aynı paketin içinde)
from .tools import all_tools
# GÜNCELLEME: Yeni ve güvenli araç çalıştırıcı düğümümüzü import ediyoruz.
from .nodes import all_nodes, enhanced_should_continue
from .nodes.tool_executor import execute_tools 
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



for name, node_function in all_nodes.items():
    if name == "agent":
        # LAMBDA TUZAĞINA KARŞI DÜZELTME:
        # node_func=node_function, lambda'nın her döngüdeki doğru fonksiyonu
        # anında yakalamasını sağlar.
        workflow.add_node(
            name,
            lambda state, node_func=node_function: node_func(state, model_with_tools)
        )
    else:
        # Standart düğümler için de aynı güvenlik önlemini almak iyi bir pratiktir.
        workflow.add_node(
            name,
            lambda state, node_func=node_function: node_func(state)
        )

# YENİ VE GÜVENLİ YÖNTEMİ EKLİYORUZ:
# "tools" adındaki düğüm artık, state'ten user_id'yi okuyup güvenli fonksiyonları çağıran
# bizim özel 'execute_tools' fonksiyonumuzdur.
workflow.add_node("tools", execute_tools)


# --- GRAF AKIŞINI TAMAMEN YENİDEN YAPIYORUZ ---

# 1. GİRİŞ NOKTASI: Her zaman önce önbelleği kontrol et.
workflow.set_entry_point("cache")


# 2. Önbellek Sonrası: Eğer önbellekte varsa (HIT), bitir. Yoksa (MISS), validasyona git.
workflow.add_conditional_edges(
    "cache",
    lambda state: END if state.get("cached") else "validate"
)

# 3. Validasyon Sonrası: Eğer hata varsa, bitir. Yoksa, ŞİMDİ zorunlu RAG aramasını yap.
workflow.add_conditional_edges(
    "validate",
    lambda state: END if state.get("validation_error") else "agent"
)




# 5. Agent Karar Anı: Agent, elindeki RAG sonucuna göre karar verir.
#    - Ya cevap yeterlidir ve sonlandırır.
#    - Ya da ek bilgi (örn: ürün detayı) için başka bir araç kullanır.
workflow.add_conditional_edges(
    "agent", 
    enhanced_should_continue,
    {
        "tools": "tools",
        "cache_and_end": "cache_and_end"
    }
)



# 6. Standart Araç Döngüsü: Bu kısım, ikincil araçlar (örn: get_product_details) için kullanılır.
# önce özetleme düğümüne gönderiyoruz. Özetleme düğümü de çıktısını ajana iletiyor.
workflow.add_edge("tools", "summarize")
workflow.add_edge("summarize", "agent")

workflow.add_edge("cache_and_end", END)



# Grafiği çalıştırılabilir bir uygulama haline getir
langgraph_app = workflow.compile()



# Modele kimliğini ve kurallarını öğreten sistem talimatı
SYSTEM_INSTRUCTION = """
### TEMEL KURAL ###
Senin TEK bir görevin var: Kullanıcının sorusunu analiz edip doğru aracı seçmek.
Aşağıdaki iki seçenekten birini UYGULAMAK ZORUNDASIN:

**Seçenek 1 (Spesifik Ürün Sorgusu):**
- **EĞER** kullanıcı mesajı, 'iPhone' veya 'MacBook' veya 'Playstation' gibi spesifik ve tanınabilir bir ürün adı içeriyorsa, **O ZAMAN** `get_product_details_tool` aracını çağır.

**Seçenek 2 (Diğer Tüm Durumlar - Varsayılan):**
- **EĞER** kullanıcı mesajı yukarıdaki kurala uymuyorsa, yani spesifik bir ürün adı İÇERMİYORSA, o zaman bu soru bir politika veya genel bir sorudur. Bu durumda **MUTLAKA** `search_documents_tool` aracını kullanmalısın.
- "Fiyatlandırma", "Stok", "İade", "Kargo", "Garanti" gibi genel kavramlar her zaman bu seçeneğe girer.

Bu iki kuralın dışında bir varsayımda bulunma. Bir soru spesifik bir ürün adı içermiyorsa, cevap her zaman belgelerdedir.
"""



# 3. FastAPI Router'ı Tarafından Çağrılacak Ana Fonksiyon
# GÜNCELLEME: Fonksiyon artık sadece bir string değil, user_id'yi de içeren tam bir state dict'i alıyor.
async def run_langgraph_chat_async(initial_state: dict):
    """
    LangGraph uygulamasını çalıştırır ve yanıtları akış halinde döndürür.
    Sohbeti, router'dan gelen başlangıç state'i ve sistem talimatı ile başlatır.
    """
    inputs = initial_state.copy()
    inputs["messages"] = [SystemMessage(content=SYSTEM_INSTRUCTION)] + inputs["messages"]


    # .astream() metodu, yanıtın adımlarını asenkron bir akış olarak almanızı sağlar
    async for output in langgraph_app.astream(inputs):
        # Akıştan gelen çıktıyı kontrol et. Anahtar, çalışan düğümün adıdır.
        
        # Yanıt 'agent' düğümünden mi geliyor? (Önbellek MISS durumu)
        for key, value in output.items():
            if key == "agent" and isinstance(value, dict) and "messages" in value:
                last_message: BaseMessage = value["messages"][-1]
                # --- ANA GÜNCELLEME BURADA ---
                # Yanıtı göndermeden önce, mesajın bir AIMessage olduğundan emin oluyoruz
                # ve bu mesajın araç çağırmadığını kontrol ediyoruz.
                if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                    if last_message.content:
                        yield last_message.content

            elif key == "cache" and isinstance(value, dict) and value.get("cached"):
                last_message: BaseMessage = value["messages"][-1]
                # Önbellekten gelen mesajın içeriği varsa doğrudan gönderilebilir.
                if last_message.content:
                    yield last_message.content

            # --- YENİ EKLENEN BLOK ---
            # 'validate' düğümünden bir çıktı geldi mi diye kontrol et.
            elif key == "validate" and isinstance(value, dict) and value.get("validation_error"):
                # Eğer 'validation_error' True ise, biliyoruz ki 'validate_input' düğümü
                # 'messages' listesine bir hata mesajı eklemiştir.
                last_message: BaseMessage = value["messages"][-1]
                
                # Bu hata mesajının içeriğini alıp frontend'e gönder.
                if last_message.content:
                    yield last_message.content
            # --- YENİ BLOK SONU ---