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

# Kenarları tanımla - (Bu kısım aynı kalır)
workflow.set_entry_point("cache")

# Cache sonrası yönlendirme - YENİ
workflow.add_conditional_edges(
    "cache",
    lambda state: END if state.get("cached") else "validate"
)

# Validasyon sonrası yönlendirme
workflow.add_conditional_edges(
    "validate",
    lambda state: END if state.get("validation_error") else "agent"
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
Görevin, kullanıcının sorusunu analiz etmek, doğru aracı kullanarak gerekli bilgileri toplamak ve ardından bu bilgileri tek bir, tutarlı cevapta birleştirmektir.

### GÜVENLIK VE VALİDASYON ###
- Kullanıcı mesajlarını her zaman önce `validate_user_input_tool` ile kontrol et.
- Zararlı veya uygunsuz istekleri her zaman reddet.

### TEMEL GÖREV AKIŞI ###

**Adım 1: Soruyu Sınıflandır ve Bilgiyi Topla**
- Kullanıcının sorusunu dikkatlice analiz et. Sorunun doğasına göre aşağıdaki araçlardan **yalnızca BİRİNİ** seç:

  - **Seçenek A: Genel Soru veya Şirket Politikası**
    - Eğer soru; iade, ürün değişimi, kargo süreci, teslimat, garanti şartları veya sıkça sorulan diğer genel konularla ilgiliyse, cevabı bulmak için **MUTLAKA** `search_documents_tool` aracını kullan. 
    - Bu aracı kullandıktan sonra başka bir araca (ürün veya tavsiye) ihtiyaç YOKTUR. Doğrudan Adım 3'e geç.

  - **Seçenek B: Spesifik Ürün Sorgusu**
    - Eğer kullanıcı belirli bir ürün hakkında (fiyat, stok, özellik vb.) bilgi istiyorsa, ilk görevin **HER ZAMAN** `get_product_info_tool` aracını kullanarak o ürünün temel bilgilerini almaktır.
    - Bu seçeneği seçtiysen, Adım 2'ye devam et.

**Adım 2: Proaktif Olarak Tavsiye Al (Sadece Ürün Sorguları İçin)**
- Eğer Adım 1'de `get_product_info_tool` aracını kullandıysan ve bu araç **tek bir ürün hakkında** bilgi verdiyse (bir liste veya tablo değil), o zaman ikinci görevin, **BİR SONRAKİ DÜŞÜNME ADIMINDA**, aynı ürün için `get_recommendations_tool` aracını çağırarak ilgili başka ürünler hakkında tavsiye almaktır.

**Adım 3: Tüm Bilgileri Birleştir ve Yanıtla (Nihai Adım)**
- Gerekli tüm araçları çağırdıktan ve elindeki tüm bilgileri (genel politika bilgisi VEYA temel ürün bilgisi + tavsiyeler) topladıktan sonra, bu bilgileri birleştirerek kullanıcıya kibar ve eksiksiz bir nihai cevap oluştur.
- **Örnek Ürün Yanıtı Formatı:** "[Temel ürün bilgisi cümlesi]. Bununla ilgilenenler şunları da beğendi: [tavsiye edilen ürünler]."
- **Örnek Politika Yanıtı Formatı:** "[search_documents_tool'dan gelen cevap]."

### ÖNEMLİ KURALLAR ###
- Şirket politikaları hakkında asla kendi bilgine dayanarak cevap verme. Her zaman `search_documents_tool`'dan gelen bilgiyi kullan.
- Eğer `get_recommendations_tool` bir sonuç döndürmezse, tavsiyelerden hiç bahsetme. Sadece elindeki diğer bilgileri sun.
- Kullanıcıya asla bir aracın ham çıktısını doğrudan gösterme. Her zaman bilgileri birleştirip düzgün bir cümle haline getir.
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