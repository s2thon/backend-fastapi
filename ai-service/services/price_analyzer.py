import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()  # .env'deki değişkenleri yükle

api_key = os.getenv("SERPAPI_KEY")
print("✅ API KEY yüklendi:", api_key[:6], "..." if api_key else "❌ Yok")



def fetch_google_prices(product_name: str):
    print("➡️ fetch_google_prices() çalıştı")  # TEST
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
        print("🟡 İstek URL:", response.url)  # 👈 BURASI
        print("🧾 SERPAPI RAW RESPONSE:", response.text[:500])
    except requests.exceptions.RequestException as e:
        print("❌ SERPAPI isteği başarısız:", e)
        return []

    print("🧾 SERPAPI RAW RESPONSE:", response.text[:500])  # Uzunsa kes

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
            price_str = re.sub(r"[^\d.]", "", price_str)  # 🧼 Temizlik
            prices.append(float(price_str))
        except Exception as e:
            print(f"⚠️ Fiyat ayrıştırılamadı: {price_str} → {e}")
            continue

    print("📊 Çekilen fiyatlar:", prices)
    return prices


# 🧠 analyze_product_price fonksiyonunu aykırı değerleri temizleyecek şekilde güncelleyelim:
def analyze_product_price(product):
    print(f"📥 Analiz başlatıldı: {product.product_name} | {product.price}₺")

    competitor_prices = fetch_google_prices(product.product_name)
    if not competitor_prices:
        return {"error": "Rakip fiyatlar alınamadı. Ürün adıyla eşleşen sonuç bulunamadı veya API başarısız oldu."}

    # --- YENİ AYKIRI DEĞER TEMİZLEME MANTIĞI BAŞLANGICI ---
    
    print(f"📊 Orijinal veri ({len(competitor_prices)} adet): {competitor_prices}")
    
    filtered_prices = []
    # Aykırı değerleri temizlemek için en az 16 veri noktası olmalı (5 baştan + 4 sondan + en az 7 ortada)
    if len(competitor_prices) > 15:
        sorted_prices = sorted(competitor_prices)
        # Listenin başından ilk 5'i ve sonundan son 4'ü atlıyoruz.
        filtered_prices = sorted_prices[5:-4]
        print(f"✂️ Aykırı değerler (ilk 5 ve son 4) temizlendi.")
        print(f"📊 Temizlenmiş veri ({len(filtered_prices)} adet): {filtered_prices}")
    else:
        # Yeterli veri yoksa, aykırı değer temizleme işlemini atla ve orijinal veriyi kullan.
        print(f"⚠️ Veri sayısı ({len(competitor_prices)}) aykırı değerleri temizlemek için yetersiz. Orijinal veri kullanılıyor.")
        filtered_prices = competitor_prices

    # Eğer filtreleme sonrası liste boş kalırsa (çok düşük bir ihtimal ama bir güvenlik önlemi)
    if not filtered_prices:
        return {"error": "Aykırı değerler temizlendikten sonra analiz edilecek yeterli veri kalmadı."}
        
    # --- HESAPLAMALAR ARTIK "filtered_prices" ÜZERİNDEN YAPILACAK ---

    avg_price = round(sum(filtered_prices) / len(filtered_prices), 2)
    min_price = min(filtered_prices)
    your_price = product.price

    # 1. Fiyat durumunu ve mesajı belirle (Bu mantık aynı kalıyor, sadece daha temiz veriyle çalışıyor)
    status = ""
    message = ""
    
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
    else: # your_price < min_price
        status = "ÇOK DÜŞÜK"
        message = (f"Fiyatınız (₺{your_price}) piyasadaki en düşük fiyattan (₺{min_price}) bile daha ucuz. "
                   "Bu durum pazar payı kazanmanızı sağlayabilir ancak kâr marjınızı kontrol ettiğinizden emin olun.")

    # 2. Duruma göre akıllı fiyat önerisi yap
    if status == "İDEAL":
        recommended_price = your_price
    else:
        recommended_price = round(avg_price * 0.97, 2)
    
    print(f"✅ Analiz tamamlandı | Durum: {status} | Ortalama: ₺{avg_price} | En Düşük: ₺{min_price} | Öneri: ₺{recommended_price}")

    return {
        "product_name": product.product_name,
        "your_price": your_price,
        "status": status,
        "competitor_analysis": {
            "avg_competitor_price": avg_price,
            "min_competitor_price": min_price,
            # Analizde kullanılan rakip sayısını döndürmek daha doğru olur.
            "competitor_count": len(filtered_prices) 
        },
        "recommended_price": recommended_price,
        "message": message
    }
