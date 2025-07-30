# RAG pipeline (chatbot)

import os

from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool
from google.generativeai.protos import Part

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from services.supabase_client import get_stock_info, get_price_info



# .env dosyasını yükle
load_dotenv()

# Gemini API yapılandırması
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel("gemini-1.5-flash")

# Embedding nesnesi
embedding = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)




# Dökümanlardan vektör veritabanı oluştur (tek seferlik)
def build_vector_store():
    file_paths = [
        "data/documents/faq.txt",
        "data/documents/policy.txt",
    ]

    docs = []
    for path in file_paths:
        loader = TextLoader(path, encoding="utf-8")
        docs.extend(loader.load())

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    vectorstore = FAISS.from_documents(chunks, embedding)
    vectorstore.save_local("../ai-service/embeddings/vector_store")

# Vektör veritabanını yükle (eğer yoksa oluştur)
if not os.path.exists("../ai-service/embeddings/vector_store/index.faiss"):
    build_vector_store()

db = FAISS.load_local("../ai-service/embeddings/vector_store", embedding, allow_dangerous_deserialization=True)


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


system_instruction = """
### KİMLİK VE GÖREV TANIMI ###
Sen, bir e-ticaret platformunun yardımsever ve profesyonel müşteri hizmetleri asistanısın. Senin tek görevin, kullanıcılardan gelen soruları doğru bir şekilde yanıtlamaktır.

### DAVRANIŞ KURALLARI ###
1. PROFESYONEL DİL KULLANIMI: Cevapların daima resmi, net, kibar ve kurumsal bir dilde olmalıdır. Kullanıcının kullandığı dil ne olursa olsun, sen bu profesyonel kimliğinden asla ödün verme.

2. GİRDİYİ ANLAMA, TAKLİT ETMEME: Kullanıcılar argo, şive, yazım hataları veya günlük konuşma dili kullanabilirler. Bu tür ifadeleri anlamak senin görevin, ancak cevaplarında bunları KESİNLİKLE KULLANMAMALISIN. Örneğin, "abi", "kardeşim", "he gardaş", "eyvallah" gibi ifadeler kullanma.

3. ARAÇ KULLANIMI ÖNCELİĞİ: Kullanıcıdan gelen soru, ürünün stok durumu, fiyatı, mevcudiyeti veya buna benzer veritabanı bilgilerini içeriyorsa, bu bilgileri tahmin etmeye çalışmamalısın. Sana verilen ilgili fonksiyonları (örneğin get_price_info, get_stock_info) kullanarak cevap vermelisin. Fonksiyonlar kullanılmadan yapılan cevaplar yanlış olur.

4. ZORUNLU FONKSİYON KULLANIMI: Eğer kullanıcı bir ürünün fiyatı, ücreti, tutarı, maliyeti, bedeli veya stok durumu, adet bilgisi, elde olup olmadığı gibi bilgileri soruyorsa, bu soruları belgelerden (faq.txt, policy.txt) cevaplamamalısın. Bu tür bilgiler yalnızca ilgili fonksiyonlar üzerinden alınmalıdır. RAG (belge arama) bu tür sorular için kullanılmamalıdır.

### ÖRNEK SENARYOLAR ###

- KULLANICI GİRDİSİ: "slm bu kırmızı ayakkabıdan elinizde var mı?"
- DÜŞÜNCE SÜRECİN: Kullanıcı bir ürünün stok durumunu soruyor. 'Kırmızı Ayakkabı' ürün adıdır. get_stock_info fonksiyonunu çağırmalıyım.
- ÇAĞRILACAK FONKSİYON: get_stock_info(product_name='Kırmızı Ayakkabı')

- KULLANICI GİRDİSİ: "he gardas bu ipone 14 puro nun fiyatı ne gadardır"
- DÜŞÜNCE SÜRECİN: Kullanıcı yazım hatalarıyla bir ürünün fiyatını soruyor. Ürün 'iPhone 14 Pro' gibi duruyor. get_price_info fonksiyonunu çağırmalıyım.
- ÇAĞRILACAK FONKSİYON: get_price_info(product_name='iPhone 14 Pro')

- KULLANICI GİRDİSİ: "iphone 14 pro'nun fiyatı ne kadar?"
- DÜŞÜNCE SÜRECİN: Kullanıcı doğrudan fiyat soruyor. Belgelerden cevap vermemeliyim. Fonksiyonu kullanmalıyım.
- ÇAĞRILACAK FONKSİYON: get_price_info(product_name='iPhone 14 Pro')

- KULLANICI GİRDİSİ: "iade politikası hakkında bilgi alabilir miyim"
- DÜŞÜNCE SÜRECİN: Kullanıcı genel bir politika sorusu soruyor. Bu durumda belgelerden (RAG) cevap verebilirim. Fonksiyon gerekmez.
- ÇAĞRILACAK FONKSİYON: Yok.

- KULLANICI GİRDİSİ: "bir ürünün fiyatını öğrenebilir miyim"
- DÜŞÜNCE SÜRECİN: Kullanıcı fiyat sormuş ama ürün adı eksik. get_price_info fonksiyonunu çağırmalı ama ürün adı alınmalı.
- YAPILACAK: Ürün adını LLM ile belirle, sonra fonksiyonu çağır.

### GENEL KURALLAR ###
- Kullanıcının sorusunu dikkatle analiz et.
- Kullanıcının dili günlük de olsa, sen daima kurumsal ve net cevap ver.

"""



# Modeli, hem araçları hem de YENİ sistem talimatını kullanacak şekilde yapılandıralım
llm_with_tools = genai.GenerativeModel(
    "gemini-1.5-flash",
    tools=tools,
    system_instruction=system_instruction # <-- BURAYA EKLİYORUZ
)

# Fonksiyon adlarını gerçek Python fonksiyonlarıyla eşleştiren bir harita
available_functions = {
    "get_stock_info": get_stock_info,
    "get_price_info": get_price_info,
}



def extract_product_name_with_llm(message: str) -> str:
    """
    Kullanıcının mesajındaki ürün adını (marka + model) çıkarmak için LLM'e kısa bir prompt gönderir.
    Geriye sadece ürün adı (örneğin: "iPhone 14 Pro") döner.
    """
    prompt = f"""
        Aşağıdaki kullanıcı mesajından sadece ürünün marka ve model adını çıkar. 
        Cevabın sadece ürün adı olsun. Başka hiçbir şey yazma. Nokta bile koyma.

        Mesaj: "{message}"

        Ürün Adı:
    """

    try:
        response = llm.generate_content(prompt)
        product_name = response.text.strip()
        
        # Temizlik: Eğer ürün adı tırnakla gelirse çıkar
        if product_name.startswith('"') and product_name.endswith('"'):
            product_name = product_name[1:-1].strip()

        return product_name
    except Exception as e:
        print(f"[extract_product_name_with_llm] Hata: {str(e)}")
        return ""





# ✅ Ana RAG fonksiyonu
from google.generativeai.protos import Part

# ... (mevcut llm, tool, db, available_functions tanımlamaları) ...

# ✅ Ana RAG fonksiyonunun SON ve DOĞRU hali
def rag_chat(user_input: str) -> str:
    # Ön işleme – Küçük harfe çevir ve temizle
    lower_input = user_input.lower()

    # ✅ 1. ADIM – Anahtar kelimeye göre ön kontrol (fonksiyon zorlaması)
    if any(kw in lower_input for kw in ["fiyat", "kaç para", "ne kadar", "ücret", "tutar", "fiyati", "maliyeti"]):
        product_name = extract_product_name_with_llm(user_input)
        if not product_name:
            return "Ürün adını anlayamadım. Lütfen daha net bir şekilde belirtir misiniz?"
        return get_price_info(product_name)

    if any(kw in lower_input for kw in ["stok", "var mı", "kaldı mı", "mevcut", "adet", "stokta", "elde"]):
        product_name = extract_product_name_with_llm(user_input)
        if not product_name:
            return "Stok bilgisi için ürün adını net olarak belirtmeniz gerekiyor."
        return get_stock_info(product_name)

    # ✅ 2. ADIM – Normal LLM & tool-based akış (genel sorular için)
    chat = llm_with_tools.start_chat()
    response = chat.send_message(user_input)
    response_part = response.parts[0]

    # ✅ 3. ADIM – LLM fonksiyon çağırmak isterse
    if response_part.function_call.name:
        function_call = response_part.function_call
        function_name = function_call.name
        function_args = function_call.args

        if function_name in available_functions:
            print(f"🧠 LLM fonksiyon çağırıyor: {function_name} → {dict(function_args)}")

            function_to_call = available_functions[function_name]
            result = function_to_call(product_name=function_args["product_name"])

            final_response = chat.send_message(
                Part(function_response={
                    "name": function_name,
                    "response": {"result": result}
                })
            )
            return final_response.text.strip()
        else:
            return f"Hata: Tanınmayan fonksiyon: {function_name}"

    # ✅ 4. ADIM – Fonksiyon çağrısı yoksa RAG'e başvur
    print("🧠 Fonksiyon çağrısı yapılmadı, RAG (belge araması) çalıştırılıyor...")
    docs = db.similarity_search(user_input, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
    Aşağıdaki bilgiler, kullanıcının sorusuna yardımcı olabilir. Eğer bilgi yetersizse, uydurma yapma.
    Bilgi:\n{context}\n
    Soru: {user_input}
    Cevap:
    """

    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[AI Hatası]: {str(e)}"
# Embedding dosyasını başlatmak için
if __name__ == "__main__":
    build_vector_store()
    print("✅ Vektör veritabanı başarıyla oluşturuldu.")
