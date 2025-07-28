# FastAPI app

from fastapi import FastAPI
from routers import description, chatbot, price_analysis_router

app = FastAPI(title="AI Microservice")

app.include_router(description.router)
app.include_router(chatbot.router)
app.include_router(price_analysis_router.router)

@app.get("/")
def read_root():
    return {"status": "AI Microservice Running"}
