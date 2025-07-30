# /services/rag_chat.py

# Gerekli kütüphaneleri içe aktarıyoruz
import os
import asyncio
import redis
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from services.supabase_client import get_stock_info, get_price_info

# --- Uygulama Başlangıcında Yapılacak Konfigürasyonlar ---

# .env dosyasını yükle
load_dotenv()

# GenerationConfig'i tanımla
generation_config = GenerationConfig(
    temperature=0.1,
    max_output_tokens=512,
)

# Gemini API'sini yapılandır
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Araç tanımlamalarını yap
tools = [
    Tool(
        function_declarations=[
            {
                "name": "get_stock_info",
                "description": "Bir ürünün stokta kaç adet olduğunu öğrenmek için kullanılır. Ürünün adını parametre olarak alır.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "product_name": {
                            "type": "STRING",
                            "description": "Stok bilgisi sorgulanacak ürünün adı (örn: 'Kırmızı Spor Ayakkabı')"
                        }
                    },
                    "required": ["product_name"]
                }
            },
            {
                "name": "get_price_info",
                "description": "Bir ürünün fiyatını öğrenmek için kullanılır. Kullanıcı 'fiyatı ne kadar', 'kaç para', 'ne gadar' gibi ifadelerle veya yazım hatalarıyla sorsa bile bu fonksiyonu kullan. Ürünün adını parametre olarak alır.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "product_name": {
                            "type": "STRING",
                            "description": "Fiyat bilgisi sorgulanacak ürünün adı (örn: 'Mavi Gömlek')"
                        }
                    },
                    "required": ["product_name"]
                }
            }
        ]
    )
]

# System Instruction'ı (Sistem Talimatı) tanımla
system_instruction = """
    ### KİMLİK VE GÖREV TANIMI ###
    Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. Senin tek görevin, kullanıcılardan gelen soruları doğru bir şekilde yanıtlamaktır.

    ### DAVRANIŞ KURALLARI ###
    1. PROFESYONEL DİL KULLANIMI: Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır. Kullanıcının kullandığı dil ne olursa olsun, sen bu profesyonel kimliğinden asla ödün verme.
    2. GİRDİYİ ANLAMA, TAKLİT ETMEME: Kullanıcılar argo, şive, yazım hataları veya günlük konuşma dili kullanabilirler. Bu tür ifadeleri anlamak senin görevin, ancak cevaplarında bunları KESİNLİKLE KULLANMAMALISIN.
    3. ARAÇ KULLANIMI ÖNCELİĞİ: Kullanıcıdan gelen soru, ürünün stok durumu, fiyatı gibi veritabanı bilgilerini içeriyorsa, bu bilgileri tahmin etmemelisin. Sana verilen fonksiyonları kullanarak cevap vermelisin.
    4. ZORUNLU FONKSİYON KULLANIMI: Eğer kullanıcı bir ürünün fiyatı veya stok durumunu soruyorsa, bu soruları belgelerden cevaplamamalısın. Bu tür bilgiler yalnızca ilgili fonksiyonlar üzerinden alınmalıdır.

    ### ÖRNEK SENARYOLAR ###
    - KULLANICI GİRDİSİ: "slm bu kırmızı ayakkabıdan elinizde var mı?"
    - DÜŞÜNCE SÜRECİN: Kullanıcı stok soruyor. get_stock_info(product_name='Kırmızı Ayakkabı') çağırmalıyım.
    - KULLANICI GİRDİSİ: "he gardas bu ipone 14 puro nun fiyatı ne gadardır"
    - DÜŞÜNCE SÜRECİN: Kullanıcı fiyat soruyor. get_price_info(product_name='iPhone 14 Pro') çağırmalıyım.
    - KULLANICI GİRDİSİ: "iade politikası hakkında bilgi alabilir miyim"
    - DÜŞÜNCE SÜRECİN: Kullanıcı genel bir politika sorusu soruyor. Bu durumda belgelerden (RAG) cevap verebilirim.
"""

# Modeli, araçları ve sistem talimatını kullanarak yapılandır
llm_with_tools = genai.GenerativeModel(
    "gemini-1.5-flash",
    tools=tools,
    system_instruction=system_instruction,
    generation_config=generation_config
)

# Embedding modelini yükle
embedding = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Vektör veritabanını yükle veya oluştur
vector_store_path = "../ai-service/embeddings/vector_store"
if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
    print("Vektör veritabanı bulunamadı, oluşturuluyor...")
    file_paths = ["data/documents/faq.txt", "data/documents/policy.txt"]
    docs = []
    for path in file_paths:
        loader = TextLoader(path, encoding="utf-8")
        docs.extend(loader.load())
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, embedding)
    vectorstore.save_local(vector_store_path)
    print("✅ Vektör veritabanı başarıyla oluşturuldu.")

db = FAISS.load_local(vector_store_path, embedding, allow_dangerous_deserialization=True)

# Uygulama genelinde kullanılacak sabitler
available_functions = {"get_stock_info": get_stock_info, "get_price_info": get_price_info}
FIYAT_KEYWORDLERI = ["fiyat", "kaç para", "ne kadar", "ücret", "tutar", "fiyati", "maliyeti"]
STOK_KEYWORDLERI = ["stok", "var mı", "kaldı mı", "mevcut", "adet", "stokta", "elde"]

# Redis istemcisini yapılandır
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Redis önbellek sunucusuna başarıyla bağlanıldı.")
except redis.exceptions.ConnectionError as e:
    print(f"❌ Redis'e bağlanılamadı: {e}. Önbellekleme devre dışı.")
    redis_client = None


# === ASENKRON VE AKIŞLI ANA CHAT FONKSİYONU ===
async def rag_chat_async(user_input: str):
    """
    Kullanıcıya yanıtı adım adım ve akış halinde döndüren asenkron fonksiyon.
    Hissedilen performansı artırır ve Redis ile önbellekleme yapar.
    """
    final_result = ""
    cache_key = f"rag_chat:{user_input.lower().strip()}"

    # 1. ADIM: ÖNBELLEĞİ KONTROL ET
    if redis_client:
        try:
            cached_response = redis_client.get(cache_key)
            if cached_response:
                print("🚀 Cevap Redis önbelleğinden anında bulundu!")
                yield cached_response
                return
        except redis.exceptions.RedisError as e:
            print(f"⚠️ Redis'ten okuma hatası: {e}. Önbellek atlanıyor.")

    # Önbellekte yoksa, kullanıcıya ilk geri bildirimi anında yap
    yield "Anlıyorum, talebinizi işleme alıyorum... \n"

    # Asenkron olay döngüsünü al ve sohbeti başlat
    loop = asyncio.get_event_loop()
    chat = llm_with_tools.start_chat()
    lower_input = user_input.lower()
    is_price_query = any(kw in lower_input for kw in FIYAT_KEYWORDLERI)
    is_stock_query = any(kw in lower_input for kw in STOK_KEYWORDLERI)

    try:
        # === 2. ADIM: HIZLI YOL (ARAÇ KULLANIMI) ===
        if is_price_query or is_stock_query:
            forced_function_name = "get_price_info" if is_price_query else "get_stock_info"
            yield f"İlgili ürün bilgisi için hazırlık yapılıyor... \n"
            
            force_tool_prompt = f"Kullanıcı sorusu: \"{user_input}\". Bu soru için `{forced_function_name}` aracını çağır."
            
            # API ÇAĞRISI (Bloklamayan şekilde)
            response = await loop.run_in_executor(None, chat.send_message, force_tool_prompt)
            response_part = response.parts[0]

        # === 3. ADIM: GENEL YOL (RAG) ===
        else:
            yield "İlgili belgeler aranıyor... \n"
            # VEKTÖR DB ARAMASI (Bloklamayan şekilde)
            docs = await loop.run_in_executor(None, db.similarity_search, user_input, 3)
            context = "\n\n".join(doc.page_content for doc in docs)
            
            general_prompt = f"Kullanıcının sorusu: \"{user_input}\"\n\nBu soruya cevap verirken aşağıdaki belgeleri kullan:\n{context}\n\nCevap:"
            yield "Yapay zeka ile cevap oluşturuluyor... \n"
            # API ÇAĞRISI (Bloklamayan şekilde)
            response = await loop.run_in_executor(None, chat.send_message, general_prompt)
            response_part = response.parts[0]

        # === 4. ADIM: YANITI İŞLEME VE DÖNDÜRME ===
        if response_part.function_call and response_part.function_call.name:
            function_call = response_part.function_call
            function_name = function_call.name
            function_args = function_call.args
            
            if function_name in available_functions:
                product_name_from_llm = function_args.get("product_name", "")
                if not product_name_from_llm:
                    final_result = "Ürün adını anlayamadım, lütfen ürünü daha net belirtir misiniz?"
                else:
                    yield f"'{product_name_from_llm}' için veritabanı sorgulanıyor... \n"
                    # VERİTABANI SORGUSU (Bloklamayan şekilde)
                    function_to_call = available_functions[function_name]
                    final_result = await loop.run_in_executor(None, function_to_call, product_name_from_llm)
            else:
                final_result = f"Hata: Sistemde tanımlı olmayan bir fonksiyon çağrıldı: {function_name}"
        else:
            final_result = response.text.strip()

        # Nihai sonucu kullanıcıya gönder
        yield final_result

    except Exception as e:
        print(f"[HATA - rag_chat_async]: {type(e).__name__} - {str(e)}")
        yield "Üzgünüm, isteğinizi işlerken beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        final_result = "" # Hata durumunda önbelleğe boş kaydedilmesin

    # === 5. ADIM: SONUCU ÖNBELLEĞE KAYDET ===
    if redis_client and final_result:
        try:
            print(f"💾 Sonuç Redis'e kaydediliyor. (Anahtar: {cache_key})")
            # ttl (time-to-live) ile önbelleğin 1 saat (3600 saniye) geçerli olmasını sağla
            redis_client.setex(cache_key, 3600, final_result)
        except redis.exceptions.RedisError as e:
            print(f"⚠️ Redis'e yazma hatası: {e}. Bu yanıt önbelleğe alınamadı.")