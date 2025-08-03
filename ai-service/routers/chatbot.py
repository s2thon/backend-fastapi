# ai-service/routers/chatbot.py

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse 
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
    Kullanıcı girdisini alır, LangGraph'ı çalıştırır ve cevabı tek bir JSON nesnesi
    olarak döndürür.
    """
    try:
        # LangGraph'i başlatırken state'e kullanıcı kimliğini ekliyoruz.
        initial_state = GraphState(
            messages=[HumanMessage(content=request.message)],
            user_id=claims.user_id 
        )

        # --- DEĞİŞİKLİK BURADA BAŞLIYOR ---

        # 1. LangGraph'tan gelen tüm metin parçalarını (stream) bir listede topla.
        final_result_chunks = []
        async for chunk in run_langgraph_chat_async(initial_state):
             # Gelen chunk'ların string olduğunu varsayıyoruz.
             # Eğer dict ise (örn: {"content": "..."}), o zaman chunk['content'] kullanın.
             final_result_chunks.append(str(chunk))

        # 2. Tüm parçaları tek bir metin dizesinde birleştir.
        final_output_text = "".join(final_result_chunks)

        # 3. Frontend'in beklediği formatta bir JSON nesnesi oluştur.
        #    Gerçek cevabı "output" alanına koyuyoruz.
        final_response_obj = {
            "output": final_output_text,
            "suggestions": [] # Örnek öneriler
        }

        # 4. StreamingResponse yerine, oluşturduğumuz JSON nesnesini döndür.
        return JSONResponse(content=final_response_obj)
    
        # --- DEĞİŞİKLİK BURADA BİTİYOR ---

    except Exception as e:
        print(f"Hata - /chat-invoke: {e}")
        # Hata durumunda da standart bir JSON formatında yanıt dönmek en iyisidir.
        return JSONResponse(
            status_code=500,
            content={
                "output": "Üzgünüz, isteğiniz işlenirken beklenmedik bir hata oluştu. Lütfen tekrar deneyin.",
                "suggestions": []
            }
        )