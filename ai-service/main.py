# FastAPI app

from fastapi import FastAPI
from routers import description, chatbot

app = FastAPI(title="AI Microservice")

app.include_router(description.router)
app.include_router(chatbot.router)

@app.get("/")
def read_root():
    return {"status": "AI Microservice Running"}
