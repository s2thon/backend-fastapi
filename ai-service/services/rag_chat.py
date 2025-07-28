# RAG pipeline (chatbot)

import os
from dotenv import load_dotenv
import google.generativeai as genai

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

import google.generativeai as genai

# .env dosyasını yükle
load_dotenv()

# Gemini API yapılandırması
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel("gemini-1.5-flash")  # veya "gemini-1.5-flash"

# Embedding nesnesi
embedding = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Dökümanlardan vektör veritabanı oluştur (tek seferlik)
def build_vector_store():
    # Çoklu dosyaları buraya ekleyebilirsin
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
    vectorstore.save_local("embeddings/vector_store")


# Vektör veritabanını yükle
db = FAISS.load_local("embeddings/vector_store", embedding, allow_dangerous_deserialization=True)


# Sorgu için RAG Chatbot (RAG logic burada)
def rag_chat(user_input: str) -> str:

    # Kullanıcı mesajına en yakın döküman parçalarını al
    docs = db.similarity_search(user_input, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    # Prompt oluştur
    prompt = f"""
Aşağıdaki bilgileri kullanarak kullanıcı sorusunu yanıtla. Bilgiler yetmezse spekülasyon yapma.

Bilgi:
{context}

Soru:
{user_input}

Cevap:
"""

    # Gemini ile yanıt al
    try:
        response = llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[AI Hatası]: {str(e)}"


# 🛠 Bu dosya direkt çalıştırılırsa embedding üret
if __name__ == "__main__":
    build_vector_store()
    print("✅ Vektör veritabanı başarıyla oluşturuldu.")
