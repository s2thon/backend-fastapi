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



# 🔁 1. USD→TRY kuru çekme fonksiyonu
def get_usd_to_try_rate():
    try:
        res = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=TRY", timeout=5)
        data = res.json()
        return data["rates"]["TRY"]
    except Exception as e:
        print("❌ Kur verisi alınamadı:", e)
        return None




# 🧠 analyze_product_price içinde:
def analyze_product_price(product):
    print(f"📥 Analiz başlatıldı: {product.product_name} | {product.price}₺")

    usd_to_try = get_usd_to_try_rate()
    if usd_to_try is None:
        return {"error": "Döviz kuru alınamadı, işlem iptal edildi."}
    print(f"💱 1 USD = {usd_to_try} TRY")

    competitor_prices_usd = fetch_google_prices(product.product_name)
    if not competitor_prices_usd:
        return {"error": "Rakip fiyatlar alınamadı. Ürün adıyla eşleşen sonuç bulunamadı veya API başarısız oldu."}

    # 🔄 Dolar fiyatlarını TL'ye çevir
    competitor_prices = [round(price * usd_to_try, 2) for price in competitor_prices_usd]
    print("📊 TL'ye çevrilen fiyatlar:", competitor_prices)

    avg = sum(competitor_prices) / len(competitor_prices)
    min_price = min(competitor_prices)
    recommended_price = round(avg * 0.97, 2) if product.price > avg else product.price

    print(f"✅ Ortalama TL fiyat: {avg} | En düşük: {min_price} | Önerilen: {recommended_price}")

    return {
        "product_name": product.product_name,
        "your_price": product.price,
        "avg_competitor_price": avg,
        "min_competitor_price": min_price,
        "recommended_price": recommended_price,
        "message": (
            "Fiyatın rakiplerden yüksek, düşürmen önerilir."
            if product.price > avg else "Fiyatın rekabetçi görünüyor."
        )
    }
