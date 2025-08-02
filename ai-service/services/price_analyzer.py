import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()  # .env'deki değişkenleri yükle

# Bu yardımcı fonksiyon, genel bir iş yaptığı için user_id'ye ihtiyaç duymaz ve değiştirilmez.
def fetch_google_prices(product_name: str):
    print("➡️ fetch_google_prices() çalıştı")
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("❌ SERPAPI_KEY .env dosyasında tanımlı değil!")

    url = "https://serpapi.com/search"
    params = {
        "q": product_name,
        "engine": "google_shopping",
        "api_key": api_key,
        "hl": "tr"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        print("🟡 İstek URL:", response.url)
    except requests.exceptions.RequestException as e:
        print("❌ SERPAPI isteği başarısız:", e)
        return []

    try:
        data = response.json()
    except Exception as e:
        print("❌ JSON parse hatası:", e)
        return []

    prices = []
    for item in data.get("shopping_results", []):
        price_str = item.get("price")
        if not price_str:
            continue
        try:
            price_str = re.sub(r"[^\d.]", "", price_str)
            prices.append(float(price_str))
        except Exception as e:
            print(f"⚠️ Fiyat ayrıştırılamadı: {price_str} → {e}")
            continue

    print("📊 Çekilen fiyatlar:", prices)
    return prices


# GÜNCELLEME: Fonksiyon imzasına 'user_id' eklendi.
# Router'dan gelen 'product' Pydantic modelini ve 'user_id'yi kabul eder.
def analyze_product_price(product, user_id: str):
    """
    Bir ürünün fiyatını analiz eder ve rekabetçiliği hakkında geri bildirimde bulunur.
    Artık bu analizi hangi kullanıcının (satıcının) istediğini bilir.
    """
    # YENİ: Hangi satıcının hangi ürün için analiz istediğini loglayalım.
    # Bu, satıcı bazlı kullanım limitleri koymak veya istatistik tutmak için kullanılabilir.
    print(f"Fiyat analizi isteği geldi. Satıcı ID: {user_id}, Ürün: {product.product_name}, Fiyat: {product.price}₺")
    
    competitor_prices = fetch_google_prices(product.product_name)
    if not competitor_prices:
        return {"error": "Rakip fiyatlar alınamadı. Ürün adıyla eşleşen sonuç bulunamadı veya API başarısız oldu."}

    # --- Aykırı Değer Temizleme Mantığı (Değişiklik Yok) ---
    print(f"📊 Orijinal veri ({len(competitor_prices)} adet): {competitor_prices}")
    if len(competitor_prices) > 15:
        sorted_prices = sorted(competitor_prices)
        filtered_prices = sorted_prices[5:-4]
        print(f"✂️ Aykırı değerler temizlendi.")
    else:
        print(f"⚠️ Veri sayısı ({len(competitor_prices)}) aykırı değerleri temizlemek için yetersiz.")
        filtered_prices = competitor_prices

    if not filtered_prices:
        return {"error": "Aykırı değerler temizlendikten sonra analiz edilecek yeterli veri kalmadı."}
    
    # --- Hesaplama ve Mesajlaşma Mantığı (Değişiklik Yok) ---
    avg_price = round(sum(filtered_prices) / len(filtered_prices), 2)
    min_price = min(filtered_prices)
    your_price = product.price
    status, message = "", ""

    if your_price > avg_price * 1.1:
        status = "ÇOK YÜKSEK"
        message = (f"Fiyatınız (₺{your_price}) piyasa ortalamasının (₺{avg_price}) belirgin şekilde üzerinde. "
                   "Rekabette geri kalmamak için ciddi bir indirim yapmanız önerilir.")
    elif your_price > avg_price:
        status = "YÜKSEK"
        message = (f"Fiyatınız (₺{your_price}) piyasa ortalamasının (₺{avg_price}) üzerinde. "
                   "Daha fazla müşteri çekmek için fiyatınızı düşünebilirsiniz.")
    elif your_price >= min_price:
        status = "İDEAL"
        message = (f"Fiyatınız (₺{your_price}) rekabetçi bir aralıkta. Piyasadaki en düşük fiyat (₺{min_price}) "
                   "ile ortalama fiyat (₺{avg_price}) arasında konumlanıyorsunuz. Harika iş!")
    else:
        status = "ÇOK DÜŞÜK"
        message = (f"Fiyatınız (₺{your_price}) piyasadaki en düşük fiyattan (₺{min_price}) bile daha ucuz. "
                   "Bu durum pazar payı kazanmanızı sağlayabilir ancak kâr marjınızı kontrol ettiğinizden emin olun.")

    recommended_price = your_price if status == "İDEAL" else round(avg_price * 0.97, 2)
    
    print(f"✅ Analiz tamamlandı | Satıcı ID: {user_id} | Durum: {status}")

    return {
        "product_name": product.product_name,
        "your_price": your_price,
        "status": status,
        "competitor_analysis": {
            "avg_competitor_price": avg_price,
            "min_competitor_price": min_price,
            "competitor_count": len(filtered_prices) 
        },
        "recommended_price": recommended_price,
        "message": message
    }