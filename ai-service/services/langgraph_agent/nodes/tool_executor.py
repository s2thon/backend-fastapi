# backend-fastapi/services/langgraph_agent/nodes/tool_executor.py

from ..graph_state import GraphState
from ....services import supabase_client  # supabase_client.py dosyasını import ediyoruz
from langchain_core.messages import AIMessage, ToolMessage
from ..tools.search_documents_tool import search_documents_tool

def execute_tools(state: GraphState) -> dict:
    """
    Bu düğüm, standart ToolNode'un yerine geçer.
    Modelin çağırmak istediği araçları, state'ten aldığı 'user_id' ile birlikte 
    güvenli bir şekilde çalıştırır.
    """
    print("\n--- 🛠️  Güvenli Araç Çalıştırma Düğümü (execute_tools) Devrede ---")
    
    messages = state["messages"]
    last_message = messages[-1]
    
    user_id = state.get("user_id")
    if not user_id:
        raise ValueError("Tool execution failed: User ID is missing from the state.")

    print(f"Kullanıcı Kimliği: {user_id}")



    # --- ANA GÜNCELLEME BURADA ---
    # Döngüye girmeden önce, son mesajın bir AIMessage olduğunu ve araç çağrıları içerdiğini kontrol et.
    # Bu, beklenmedik mesaj tiplerine karşı bir koruma sağlar.
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        # Bu durum normalde oluşmamalıdır, ama bir güvenlik önlemidir.
        return {}
    # --- GÜNCELLEME SONU ---




    tool_outputs = []
    for tool_call in last_message.tool_calls:
        # LLM'in çağırdığı aracın adı, sizin tools/ dizinindeki fonksiyon adınızla eşleşir.
        tool_name = tool_call["name"]
        args = tool_call["args"]
        response = ""
        
        print(f"⚡️ Araç Çağrılıyor: '{tool_name}' | Argümanlar: {args}")

        try:
            # === GÜVENLİK KONTROL NOKTASI ===
            # Hangi araç çağrıldıysa, ona uygun ve GÜVENLİ supabase_client fonksiyonunu çağır.

            
            if tool_name == "get_payment_amount_tool":
                response = supabase_client.get_payment_amount(
                    order_id=args.get("order_id"),
                    user_id=user_id  # GÜVENLİK: user_id'yi state'ten ekle
                )
            elif tool_name == "get_item_status_tool":
                response = supabase_client.get_item_status(
                    order_id=args.get("order_id"),
                    product_name=args.get("product_name"),
                    user_id=user_id  # GÜVENLİK: user_id'yi state'ten ekle
                )
            elif tool_name == "get_refund_status_tool":
                response = supabase_client.get_refund_status(
                    order_id=args.get("order_id"),
                    product_name=args.get("product_name"),
                    user_id=user_id  # GÜVENLİK: user_id'yi state'ten ekle
                )
            elif tool_name == "get_product_details_tool":
                 # Bu araç genel bir arama yaptığı için user_id gerektirmez.
                 response = supabase_client.get_product_details_with_recommendations(
                     product_name=args.get("product_name")
                 )

            # --- YENİ EKLENEN BLOK ---
            # Agent, "search_documents_tool" aracını çağırdığında bu blok çalışacak.
            elif tool_name == "search_documents_tool":
                # 'search_documents_tool' fonksiyonu 'query' adında bir argüman bekliyor.
                response = search_documents_tool(args.get("query"))
            # ---------------------------


            # DİKKAT: Diğer araçlarınız (search_documents_tool vb.) user_id gerektiriyorsa,
            # onları da buraya `elif` bloğu olarak eklemelisiniz.
            else:
                response = f"Hata: '{tool_name}' adında bilinmeyen veya bu düğümde tanımlanmamış bir araç çağrıldı."
        
        except Exception as e:
            print(f"❌ Araç çalıştırılırken hata oluştu: {e}")
            response = f"'{tool_name}' aracı çalıştırılırken bir hata oluştu: {e}"

        tool_outputs.append(ToolMessage(content=str(response), tool_call_id=tool_call["id"]))

    return {"messages": tool_outputs}