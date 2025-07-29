import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_supabase_connection():
    return psycopg2.connect(
        host=os.getenv("HOST"),
        port=os.getenv("PORT"),
        dbname=os.getenv("DBNAME"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )

def get_stock_info(product_name: str) -> str:
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()

        query = """
        SELECT quantity_in_stock
        FROM product
        WHERE LOWER(product_name) LIKE %s
        LIMIT 1
        """
        cursor.execute(query, (f"%{product_name.lower()}%",))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return f"'{product_name}' ürününden stokta {result[0]} adet bulunmaktadır."
        else:
            return f"'{product_name}' ürünü veritabanında bulunamadı."

    except Exception as e:
        return f"Veritabanı hatası: {str(e)}"
