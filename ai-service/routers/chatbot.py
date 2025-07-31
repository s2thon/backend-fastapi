# /chat

from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

# YENİ: Eski rag_chat yerine, yeni langgraph servisini içe aktarıyoruz.
# Fonksiyon adı da doğal olarak değişti.
from services.rag_chat_langgraph import run_langgraph_chat_async

# Router'ı tanımlıyoruz
router = APIRouter(
    prefix="/chat",
    # GÜNCELLEME: Tag'i, yeni teknolojiyi yansıtacak şekilde daha açıklayıcı hale getirdik.
    tags=["Chatbot (LangGraph)"]
)

# İstek modelimiz (request body) aynı kalıyor, çünkü hala sadece bir mesaj alıyoruz.
class ChatRequest(BaseModel):
    message: str

# GÜNCELLEME: Endpoint yolunu, sadece RAG'ı değil, daha genel bir "çağırma"
# işlemini yansıttığı için '/invoke' olarak değiştirmek daha iyi bir isimlendirmedir.
@router.post("/invoke")
async def invoke_chat_stream(request: ChatRequest):
    """
    Kullanıcı girdisini alır ve LangGraph tabanlı ajan'ı çalıştırır.
    Cevabı, üretildiği anda parça parça bir metin akışı olarak döndürür.
    
    Bu yöntem, LangGraph'ın araçları kullandığı ve düşündüğü süreçte bile
    kullanıcıya nihai yanıtı hızlıca ulaştırarak mükemmel bir kullanıcı deneyimi sunar.
    
    Test etmek için `curl` gibi bir araç kullanın:
    curl -N -X POST "http://127.0.0.1:8000/chat/invoke" \
    -H "Content-Type: application/json" \
    -d '{"message": "iade politikanız nedir?"}'
    """
    try:
        # ANA DEĞİŞİKLİK: Çağrılan fonksiyonu yeni LangGraph fonksiyonu ile değiştirdik.
        # Geri kalan her şey aynı, çünkü her iki fonksiyon da asenkron jeneratör.
        return StreamingResponse(
            run_langgraph_chat_async(request.message), 
            media_type="text/plain; charset=utf-8"
        )
    except Exception as e:
        # Olası hataları yakalamak için basit bir hata yönetimi
        # (Örn: LangGraph servisi bir hata fırlatırsa)
        print(f"Hata - /chat/invoke: {e}")
        # Hata durumunda tek seferlik bir yanıt döndürebiliriz.
        # StreamingResponse'a bir hata mesajı listesi de verebiliriz.
        return StreamingResponse(
            ["Üzgünüz, isteğiniz işlenirken bir hata oluştu."], 
            status_code=500,
            media_type="text/plain; charset=utf-8"
        )






















# # --- YENİ VE ÖNERİLEN ENDPOINT ---
# @router.post("/rag")
# async def chat_with_context_stream(request: ChatRequest):
#     """
#     Kullanıcı girdisini alır ve cevabı bir metin akışı olarak döndürür.
    
#     Bu yöntem, LLM'in yanıtı işlenirken kullanıcıya anında geri bildirim 
#     sağlayarak "hissedilen performansı" ciddi şekilde artırır.
    
#     Test etmek için `curl` gibi bir araç kullanın:
#     curl -N -X POST "http://127.0.0.1:8001/chat/rag_stream" \
#     -H "Content-Type: application/json" \
#     -d '{"message": "iPhone 14 Pro fiyatı ne kadar?"}'
#     """
#     # rag_chat_async fonksiyonu bir "asenkron jeneratör"dür.
#     # StreamingResponse, bu jeneratörden gelen her parçayı ("yield" edilen her şeyi)
#     # yanıt olarak anında istemciye (kullanıcıya) gönderir.
#     return StreamingResponse(rag_chat_async(request.message), media_type="text/plain; charset=utf-8")