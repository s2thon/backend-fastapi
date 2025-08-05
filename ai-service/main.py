# FastAPI app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import description, chatbot, price_analyzer, image_gen

from contextlib import asynccontextmanager


# Rotalarınızı ve veritabanı havuzu fonksiyonlarını import edin
from .services.supabase_client import initialize_clients, shutdown_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlatıldığında veritabanı havuzunu başlat
    print("🗄️ Uygulama başlatılıyor, veritabanı havuzu oluşturuluyor...")
    initialize_clients()

    yield

    # Uygulama kapatıldığında veritabanı havuzunu kapat
    print("🗄️ Uygulama kapanıyor, veritabanı havuzu kapatılıyor...")
    shutdown_clients()


app = FastAPI(
    title="AI Microservice",
    description="AI Microservice for various AI tasks",
    version="1.0.0",
    lifespan=lifespan    
)


# --- KRİTİK DÜZELTME 2: CORS AYARLARI EKLENDİ ---
# Bu blok, başka servislerden (örneğin Spring Boot) gelen isteklere izin verir.
# Bu olmadan, servisler birbiriyle konuşamaz.
origins = ["*"]  # Tüm kaynaklara izin ver. Daha güvenli bir ortam için buraya
                 # Spring Boot servisinin public URL'sini ekleyebilirsin,
                 # ama iç ağda "*" genellikle yeterlidir.


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Tüm metodlara izin ver (GET, POST, vb.)
    allow_headers=["*"],  # Tüm başlıklara izin ver
)
# --- CORS AYARLARI BİTTİ ---



app.include_router(description.router)
app.include_router(chatbot.router)
app.include_router(price_analyzer.router)
app.include_router(image_gen.router)

@app.get("/")
def read_root():
    return {"status": "AI Microservice Running"}
