import requests
from bs4 import BeautifulSoup
import statistics

# NOT: Gerçek projede proxy ve headers ile birlikte çalıştırılmalı
def scrape_trendyol_prices(product_name: str):
    search_query = product_name.replace(" ", "+")
    url = f"https://www.trendyol.com/sr?q={search_query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")

    prices = []
    for div in soup.select(".prc-box-dscntd"):
        try:
            price_text = div.text.strip().replace(".", "").replace(",", ".").replace("TL", "")
            price = float(price_text)
            if price > 50:
                prices.append(price)
        except:
            continue
    return prices[:10]




def scrape_hepsiburada_prices(product_name: str):
    search_query = product_name.replace(" ", "+")
    url = f"https://www.hepsiburada.com/ara?q={search_query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")

    prices = []
    for div in soup.select("div[class*='productListContent'] span[class*='price']"):
        text = div.get_text(strip=True)
        text = text.replace(".", "").replace(",", ".").replace("TL", "").strip()
        try:
            price = float(text)
            if price > 50:
                prices.append(price)
        except:
            continue

    return prices[:10]  # İlk 10 fiyatı döndür




def analyze_market_price(product_name: str, category: str, seller_price: float):
    prices_trendyol = scrape_trendyol_prices(product_name)
    prices_hepsiburada = scrape_hepsiburada_prices(product_name)

    scraped_prices = prices_trendyol + prices_hepsiburada

    if not scraped_prices:
        return {"error": "Piyasa fiyatları bulunamadı."}

    import statistics
    avg = statistics.mean(scraped_prices)
    diff = seller_price - avg
    diff_percent = (diff / avg) * 100

    if diff_percent > 10:
        comment = "Fiyatınız ortalamanın üstünde. Rekabetçi olmayabilir."
    elif diff_percent < -10:
        comment = "Fiyatınız ortalamanın altında. Karlılık düşük olabilir."
    else:
        comment = "Fiyatınız piyasa ortalamasına uygun."

    return {
        "product_name": product_name,
        "scraped_prices": scraped_prices,
        "average_price": round(avg, 2),
        "seller_price": round(seller_price, 2),
        "difference_percent": round(diff_percent, 2),
        "comment": comment
    }

