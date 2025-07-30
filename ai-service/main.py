# FastAPI app

from fastapi import FastAPI
from routers import description, chatbot, price_analyzer, image_gen

app = FastAPI(title="AI Microservice")

app.include_router(description.router)
app.include_router(chatbot.router)
app.include_router(price_analyzer.router)
app.include_router(image_gen.router)

@app.get("/")
def read_root():
    return {"status": "AI Microservice Running"}
