# Gerekli kütüphaneleri ve modülleri içe aktarıyoruz
import os
import operator
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv

# LangChain'in temel bileşenleri
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool

# Google Generative AI entegrasyonları
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# LangGraph'ın temel yapı taşları
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode # YENİ IMPORT

# Vektör veritabanı için gerekli LangChain community bileşenleri
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

# Kendi yazdığımız veritabanı fonksiyonları (araç olacaklar)
from services.supabase_client import (
    get_price_info,
    get_stock_info,
    get_payment_amount,
    get_item_status,
    get_refund_status,
)

# --- 1. UYGULAMA BAŞLANGIÇ KONFİGÜRASYONU ---

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# Embedding modelini (metinleri vektöre çeviren model) yükle
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Vektör veritabanının diskteki yolunu belirt
# Projenizin kök dizinine göre bu yolu ayarlamanız gerekebilir.
vector_store_path = "embeddings/vector_store"

# Vektör veritabanını yükle veya eğer mevcut değilse oluştur
try:
    if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
        print("Vektör veritabanı bulunamadı, sıfırdan oluşturuluyor...")
        
        # Bilgi alınacak dokümanların yolları
        file_paths = ["data/documents/faq.txt", "data/documents/policy.txt"]
        docs = []
        for path in file_paths:
            loader = TextLoader(path, encoding="utf-8")
            docs.extend(loader.load())
        
        # Dokümanları daha küçük parçalara (chunk) ayır
        splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        
        # Parçalardan FAISS vektör veritabanını oluştur ve diske kaydet
        db = FAISS.from_documents(chunks, embedding_model)
        db.save_local(vector_store_path)
        print("✅ Vektör veritabanı başarıyla oluşturuldu ve kaydedildi.")
    else:
        print("Mevcut vektör veritabanı yükleniyor...")
        db = FAISS.load_local(
            vector_store_path, 
            embedding_model, 
            allow_dangerous_deserialization=True # Güvenli bir ortamda çalıştırdığınızdan emin olun
        )
        print("✅ Vektör veritabanı başarıyla yüklendi.")
except Exception as e:
    print(f"❌ Vektör veritabanı yüklenirken kritik bir hata oluştu: {e}")
    db = None # Hata durumunda db'yi None yap

# --- 2. SİSTEM TALİMATI VE ARAÇ (TOOL) TANIMLAMALARI ---

# Modele kimliğini ve davranış kurallarını öğreten sistem talimatı
SYSTEM_INSTRUCTION = """
### KİMLİK VE GÖREV TANIMI ###
Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. Görevin, kullanıcılardan gelen soruları sana verilen araçları kullanarak doğru bir şekilde yanıtlamaktır.

### DAVRANIŞ KURALLARI ###
1.  **Profesyonel Dil:** Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır.
2.  **Araç Kullanım Önceliği:** Kullanıcı bir ürünün fiyatını, stokunu, sipariş durumunu, iade detayını veya iade/kargo gibi genel politikaları sorduğunda, bu bilgileri tahmin etmek yerine sana verilen araçları ('tools') kullanmak zorundasın. Eğer soruya uygun bir araç varsa, mutlaka kullan.
3.  **Net ve Odaklı Cevap:** Sadece sorulan soruya odaklan. Araçlardan gelen bilgiyi temiz ve anlaşılır bir şekilde kullanıcıya sun.
"""

# Fonksiyonları LangGraph'ın anlayacağı 'araçlara' dönüştürüyoruz.
# Her aracın docstring'i, modelin o aracı ne zaman kullanacağını anlaması için kritiktir.

@tool
def get_price_info_tool(product_name: str) -> str:
    """Bir ürünün fiyatını öğrenmek için kullanılır. Ürünün adını parametre olarak alır."""
    return get_price_info(product_name)

@tool
def get_stock_info_tool(product_name: str) -> str:
    """Bir ürünün stokta kaç adet olduğunu öğrenmek için kullanılır. Ürünün adını parametre olarak alır."""
    return get_stock_info(product_name)

@tool
def get_payment_amount_tool(order_id: int) -> str:
    """Bir siparişin toplam ödeme tutarını öğrenmek için kullanılır. Sipariş ID'sini parametre olarak alır."""
    return get_payment_amount(order_id)

@tool
def get_item_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün durumunu (kargolandı, hazırlanıyor vb.) öğrenmek için kullanılır. Sipariş ID'si ve ürün adı gereklidir."""
    return get_item_status(order_id, product_name)

@tool
def get_refund_status_tool(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki bir ürünün iade durumunu (onaylandı, bekleniyor vb.) öğrenmek için kullanılır. Sipariş ID'si ve ürün adı gereklidir."""
    return get_refund_status(order_id, product_name)

@tool
def search_documents_tool(query: str) -> str:
    """
    Kullanıcının iade politikası, kargo süreci, şirket hakkındaki genel bilgiler, 
    kullanım koşulları veya sıkça sorulan sorular (SSS) gibi genel bir sorusu olduğunda kullanılır.
    Ürün fiyatı, stok durumu, sipariş durumu veya iade durumu gibi spesifik veritabanı bilgileri için KULLANILMAZ.
    Sadece genel ve politikaya dayalı sorular için bu aracı kullan.
    """
    if not db:
        return "Belge veritabanı şu anda kullanılamıyor."
    
    print(f"📄 Belge araması (RAG) yapılıyor: '{query}'")
    docs = db.similarity_search(query, k=3)
    
    if not docs:
        return "Belgelerde bu konuyla ilgili bir bilgi bulunamadı."
        
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)
    return f"Konuyla ilgili belgelerden şu bilgiler bulundu:\n\n{context}"


# Tüm araçları bir listeye ve bu listeyi çalıştıracak bir ToolExecutor'a ekleyelim
tools = [
    get_price_info_tool, 
    get_stock_info_tool, 
    get_payment_amount_tool, 
    get_item_status_tool, 
    get_refund_status_tool,
    search_documents_tool, # Yeni RAG aracımızı da listeye ekledik
]

# --- 3. MODEL VE GRAFİK (LANGGRAPH) YAPILANDIRMASI ---

# Modeli streaming (akış) ve araç kullanımı için yapılandır
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    temperature=0.1, 
    google_api_key=os.getenv("GEMINI_API_KEY") # API Anahtarını doğrudan veriyoruz
)
model_with_tools = model.bind_tools(tools)

# Grafiğimizin durumunu (hafızasını) tanımlayan yapı
class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

# Grafiğin karar verme ve işlem yapma düğümleri (node'lar)
def should_continue(state: GraphState) -> Literal["tools", "end"]:
    """Modelin son çıktısını analiz eder: Araç mı çağıracak, yoksa konuşma bitti mi?"""
    if state["messages"][-1].tool_calls:
        return "tools"
    return "end"

def call_model(state: GraphState):
    """LLM'i (yapay zeka modelini) çağıran ana düğüm."""
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# --- 4. GRAFİĞİ OLUŞTURMA VE DERLEME ---

workflow = StateGraph(GraphState)

# Düğümleri (node) grafiğe ekle
workflow.add_node("agent", call_model)
# --- DEĞİŞİKLİK: Manuel call_tools fonksiyonu yerine hazır ToolNode kullanıyoruz ---
# Bu, kodu daha temiz ve kütüphane güncellemelerine daha dayanıklı hale getirir.
workflow.add_node("tools", ToolNode(tools))

# Grafiğin başlangıç noktasını belirle
workflow.set_entry_point("agent")

# Kenarları (edge) ve karar mekanizmasını tanımla
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    },
)
workflow.add_edge("tools", "agent")

# Grafiği çalıştırılabilir bir uygulama haline getir
langgraph_app = workflow.compile()

# --- 5. ASENKRON ÇALIŞTIRMA FONKSİYONU ---

async def run_langgraph_chat_async(user_input: str):
    """
    LangGraph uygulamasını çalıştırır ve yanıtları FastAPI için akış halinde döndürür.
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
        # Akıştan gelen her adımdaki son mesajı kontrol et
        if "agent" in output:
            last_message = output["agent"]["messages"][-1]
            # Sadece modelin son, nihai cevabını (araç çağırmadığı zaman) kullanıcıya gönder
            if not last_message.tool_calls and last_message.content:
                yield last_message.content