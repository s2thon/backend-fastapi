# Bu dosya, FAISS vektör veritabanını başlatmaktan ve diğer modüllerin kullanımına hazır bir db nesnesi sunmaktan sorumludur.

import os
from dotenv import load_dotenv
from pathlib import Path

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

    

    # --- KESİN ÇÖZÜM BURADA ---
    # Bu dosyanın tam yolunu al: C:\...\backend-fastapi\ai-service\services\vector_store.py
    this_file_path = Path(__file__).resolve()

    # 'ai-service' klasörünü bulana kadar yukarı çık.
    project_root = this_file_path
    while project_root.name != 'ai-service':
        project_root = project_root.parent
        if project_root == project_root.parent: # Kök dizine ulaşıldı ve bulunamadı
            raise FileNotFoundError("Proje kök dizini 'ai-service' bulunamadı.")
            
    # Artık tüm yolları bu doğru kök dizine göre hesaplıyoruz.
    vector_store_path = project_root / "embeddings" / "vector_store"
    documents_dir_path = project_root / "data" / "documents"
    # --- DÜZELTME SONU ---

    try:
        if not (vector_store_path / "index.faiss").exists():
            print(f"Vektör veritabanı bulunamadı, '{vector_store_path}' konumunda oluşturuluyor...")
            
            file_paths = [
                documents_dir_path / "faq.txt", 
                documents_dir_path / "policy.txt"
            ]
            
            docs = []
            for path in file_paths:
                if not path.exists():
                    print(f"⚠️ Uyarı: Belge dosyası bulunamadı, atlanıyor: {path}")
                    continue
                
                print(f"✅ Belge yükleniyor: {path}")
                loader = TextLoader(str(path), encoding="utf-8")
                docs.extend(loader.load())

            if not docs:
                print("❌ Yüklenecek hiçbir belge dosyası bulunamadı. Vektör deposu oluşturulamıyor.")
                return None
            
            splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_documents(docs)
            
            vector_db = FAISS.from_documents(chunks, embedding_model)
            vector_db.save_local(str(vector_store_path))
            print(f"✅ Vektör veritabanı başarıyla oluşturuldu ve '{vector_store_path}' konumuna kaydedildi.")
            return vector_db
        else:
            print(f"Mevcut vektör veritabanı '{vector_store_path}' konumundan yükleniyor...")
            vector_db = FAISS.load_local(
                str(vector_store_path), 
                embedding_model, 
                allow_dangerous_deserialization=True
            )
            print("✅ Vektör veritabanı başarıyla yüklendi.")
            return vector_db
    except Exception as e:
        print(f"❌ Vektör veritabanı yüklenirken kritik bir hata oluştu: {e}")
        return None

db = load_or_create_vector_store()