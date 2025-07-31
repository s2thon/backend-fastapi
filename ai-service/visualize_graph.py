# Bu betik, rag_chat_langgraph.py içinde derlenmiş olan 
# langgraph uygulamasını içe aktarır ve şemasını bir resim dosyası olarak kaydeder.

from services.rag_chat_langgraph import langgraph_app

try:
    print("🖼️ LangGraph şeması oluşturuluyor...")

    # Derlenmiş grafiğin çizilebilir bir temsilini al ve PNG olarak kaydet
    # draw_mermaid_png() en güzel görseli verir.
    image_bytes = langgraph_app.get_graph().draw_mermaid_png()

    # Resim verisini bir dosyaya yaz
    with open("langgraph_schema.png", "wb") as f:
        f.write(image_bytes)

    print("✅ Şema başarıyla 'langgraph_schema.png' dosyasına kaydedildi!")

except Exception as e:
    print(f"❌ Şema oluşturulurken bir hata oluştu: {e}")
    print("ℹ️ Gerekli kütüphaneleri kurduğunuzdan emin olun: pip install 'langgraph[draw]' playwright && playwright install")