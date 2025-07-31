# Bu dosya, FAISS vektör veritabanını başlatmaktan ve diğer modüllerin kullanımına hazır bir db nesnesi sunmaktan sorumludur.

import os
from dotenv import load_dotenv

# Gerekli LangChain kütüphaneleri
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Ortam değişkenlerini yükle
load_dotenv()

# Embedding modelini (metinleri vektöre çeviren model) yükle
try:
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
except Exception as e:
    print(f"❌ Embedding modeli başlatılamadı: {e}")
    embedding_model = None

def load_or_create_vector_store():
    """
    Vektör veritabanını diskten yükler. Eğer mevcut değilse,
    belirtilen dokümanlardan yeni bir tane oluşturur ve kaydeder.
    """
    if not embedding_model:
        print("⚠️ Embedding modeli olmadan vektör deposu yüklenemez.")
        return None

    vector_store_path = "embeddings/vector_store"

    try:
        if not os.path.exists(os.path.join(vector_store_path, "index.faiss")):
            print("Vektör veritabanı bulunamadı, sıfırdan oluşturuluyor...")
            
            file_paths = ["data/documents/faq.txt", "data/documents/policy.txt"]
            docs = []
            for path in file_paths:
                loader = TextLoader(path, encoding="utf-8")
                docs.extend(loader.load())
            
            splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_documents(docs)
            
            vector_db = FAISS.from_documents(chunks, embedding_model)
            vector_db.save_local(vector_store_path)
            print("✅ Vektör veritabanı başarıyla oluşturuldu ve kaydedildi.")
            return vector_db
        else:
            print("Mevcut vektör veritabanı yükleniyor...")
            vector_db = FAISS.load_local(
                vector_store_path, 
                embedding_model, 
                allow_dangerous_deserialization=True
            )
            print("✅ Vektör veritabanı başarıyla yüklendi.")
            return vector_db
    except Exception as e:
        print(f"❌ Vektör veritabanı yüklenirken kritik bir hata oluştu: {e}")
        return None

# Ana uygulama tarafından içe aktarılacak olan global 'db' nesnesi
db = load_or_create_vector_store()