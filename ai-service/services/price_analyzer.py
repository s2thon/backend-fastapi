def analyze_price(product_name: str, price: float):
    # Mock fiyat verisi (dış API yerine)
    competitor_prices = [420.0, 455.0, 470.0]
    avg_price = sum(competitor_prices) / len(competitor_prices)
    min_price = min(competitor_prices)

    recommended_price = round(avg_price * 0.97, 2) if price > avg_price else price

    return {
        "product_name": product_name,
        "your_price": price,
        "avg_competitor_price": avg_price,
        "min_competitor_price": min_price,
        "recommended_price": recommended_price,
        "message": (
            "Fiyatın rakiplerden yüksek, düşürmen önerilir."
            if price > avg_price else "Fiyatın rekabetçi görünüyor."
        )
    }
