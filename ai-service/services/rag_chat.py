# RAG pipeline (chatbot)

import os

from dotenv import load_dotenv
import google.generativeai as genai

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from ai_service.services.supabase_client import get_stock_info



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
        "ai-service/data/documents/faq.txt",
        "ai-service/data/documents/policy.txt",
    ]

    docs = []
    for path in file_paths:
        loader = TextLoader(path, encoding="utf-8")
        docs.extend(loader.load())

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    vectorstore = FAISS.from_documents(chunks, embedding)
    vectorstore.save_local("ai-service/embeddings/vector_store")

# Vektör veritabanını yükle (eğer yoksa oluştur)
if not os.path.exists("ai-service/embeddings/vector_store/index.faiss"):
    build_vector_store()

db = FAISS.load_local("ai-service/embeddings/vector_store", embedding, allow_dangerous_deserialization=True)


# ✅ Ürün adını mesajdan çıkart
def extract_product_name(message: str) -> str:
    stop_words = ["stok", "stokta", "var mı", "kaldı mı", "ne kadar", "ürün", "adet"]
    lowered = message.lower()
    for word in stop_words:
        lowered = lowered.replace(word, "")
    return lowered.strip()

# ✅ Ana RAG fonksiyonu
def rag_chat(user_input: str) -> str:
    # Supabase kontrolü
    if "stok" in user_input.lower():
        product_name = extract_product_name(user_input)
        if product_name:
            return get_stock_info(product_name)

    # RAG dosyalarından veri getir
    docs = db.similarity_search(user_input, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
Aşağıdaki bilgileri kullanarak kullanıcı sorusunu yanıtla. Bilgiler yetmezse spekülasyon yapma.

Bilgi:
{context}

Soru:
{user_input}

Cevap:
    """

    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[AI Hatası]: {str(e)}"

# Embedding dosyasını başlatmak için
if __name__ == "__main__":
    build_vector_store()
    print("✅ Vektör veritabanı başarıyla oluşturuldu.")
