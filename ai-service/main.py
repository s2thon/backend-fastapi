# FastAPI app

from fastapi import FastAPI
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

app.include_router(description.router)
app.include_router(chatbot.router)
app.include_router(price_analyzer.router)
app.include_router(image_gen.router)

@app.get("/")
def read_root():
    return {"status": "AI Microservice Running"}
