import psycopg2
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import base64

load_dotenv()

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL ve SUPABASE_KEY .env dosyasında tanımlı olmalı!")

try:
    # Bu 'supabase' nesnesi hem veritabanı hem de depolama için kullanılacak.
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase istemcisi (Veritabanı & Depolama) başarıyla oluşturuldu.")
except Exception as e:
    print(f"❌ Supabase istemcisi oluşturulurken hata: {e}")
    supabase = None

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
        WHERE product_name 
        ILIKE %s LIMIT 1
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

def upload_image_from_base64(base64_data_url: str, file_name: str) -> str:
    """
    Verilen Base64 data URL'ini çözüp Supabase Storage'a yükler.
    """

    if not supabase:
        raise ConnectionError("Supabase Storage istemcisi düzgün başlatılamadı.")

    try:
        # "data:image/png;base64," kısmını ayıkla
        header, encoded_data = base64_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)

        # 'product-images' bucket'ına resmi yüklüyoruz.
        supabase.storage.from_("product-images").upload(
            file=image_bytes, 
            path=file_name, 
            file_options={"content-type": "image/png"}
        )
        
        # Yüklenen resmin genel (public) URL'ini alıyoruz.
        public_url = supabase.storage.from_("product-images").get_public_url(file_name)
        
        print(f"✅ Görsel Supabase Storage'a yüklendi. URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Supabase Storage yükleme hatası: {e}")
        raise
