# /chat

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_chat import rag_chat_async
from fastapi.responses import StreamingResponse

# Router'ı tanımlıyoruz
router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)



class ChatRequest(BaseModel):
    message: str



# @router.post("/rag")
# def chat_with_context(request: ChatRequest):
#     response = rag_chat(request.message)
#     return {"response": response}



# --- YENİ VE ÖNERİLEN ENDPOINT ---
@router.post("/rag")
async def chat_with_context_stream(request: ChatRequest):
    """
    Kullanıcı girdisini alır ve cevabı bir metin akışı olarak döndürür.
    
    Bu yöntem, LLM'in yanıtı işlenirken kullanıcıya anında geri bildirim 
    sağlayarak "hissedilen performansı" ciddi şekilde artırır.
    
    Test etmek için `curl` gibi bir araç kullanın:
    curl -N -X POST "http://127.0.0.1:8001/chat/rag_stream" \
    -H "Content-Type: application/json" \
    -d '{"message": "iPhone 14 Pro fiyatı ne kadar?"}'
    """
    # rag_chat_async fonksiyonu bir "asenkron jeneratör"dür.
    # StreamingResponse, bu jeneratörden gelen her parçayı ("yield" edilen her şeyi)
    # yanıt olarak anında istemciye (kullanıcıya) gönderir.
    return StreamingResponse(rag_chat_async(request.message), media_type="text/plain; charset=utf-8")