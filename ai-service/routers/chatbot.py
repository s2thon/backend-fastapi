# ai-service/routers/chatbot.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

# GÜNCELLEME: Güvenlik ve state yönetimi için yeni importlar
from ..services.langgraph_agent.security import get_current_user_claims, UserClaims
from ..services.langgraph_agent.graph_state import GraphState
from ..services.langgraph_agent import run_langgraph_chat_async
from langchain_core.messages import HumanMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# Endpoint artık Spring Boot'tan gelen /api/ai/chat-invoke isteğini karşılayacak
@router.post("/chat-invoke", tags=["Chatbot (LangGraph)"])
async def invoke_chat_stream(
    request: ChatRequest,
    # YENİ: Token'ı doğrulayan ve kullanıcı bilgilerini getiren güvenlik bağımlılığı
    claims: UserClaims = Depends(get_current_user_claims)
):
    """
    JWT ile kimliği doğrulanmış bir kullanıcının girdisini alır, LangGraph'ı çalıştırır
    ve cevabı bir akış olarak döndürür. user_id, grafın state'ine eklenir.
    """
    try:
        # GÜNCELLEME: LangGraph'i başlatırken state'e kullanıcı kimliğini ekliyoruz.
        # Bu, graf içindeki tüm veritabanı sorgularının bu kullanıcıya özel yapılmasını sağlar.
        initial_state = GraphState(
            messages=[HumanMessage(content=request.message)],
            user_id=claims.user_id 
        )

        return StreamingResponse(
            # GÜNCELLEME: Servis fonksiyonu artık mesaj yerine tüm başlangıç state'ini alıyor.
            run_langgraph_chat_async(initial_state), 
            media_type="text/plain; charset=utf-8"
        )
    except Exception as e:
        print(f"Hata - /chat-invoke: {e}")
        return StreamingResponse(
            ["Üzgünüz, isteğiniz işlenirken bir hata oluştu."], 
            status_code=500,
            media_type="text/plain; charset=utf-8"
        )