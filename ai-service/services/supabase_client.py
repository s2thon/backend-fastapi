import psycopg2
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import base64
# Yeni havuz fonksiyonlarımızı import edelim
from .db_pool import get_db_connection, release_db_connection
from functools import lru_cache

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




# LRU Cache (Least Recently Used Cache) decorator'ı ile fonksiyonu sarmala
# maxsize: hafızada en fazla kaç sonucu tutacağı
@lru_cache(maxsize=128)
def get_stock_info(product_name: str) -> str:
    try:
        conn = get_db_connection()
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

        if result:
            return f"'{product_name}' ürününden stokta {result[0]} adet bulunmaktadır."
        else:
            return f"'{product_name}' ürünü veritabanında bulunamadı."

    except Exception as e:
        return f"Veritabanı hatası: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)

# ... (Mevcut import'larınız ve Supabase istemci kurulumunuz) ...




@lru_cache(maxsize=128)
def get_price_info(product_name: str) -> str:
    """Belirtilen ürünün fiyat bilgisini veritabanından alır ve bir metin olarak döndürür."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT price 
        FROM product 
        WHERE product_name 
        ILIKE %s LIMIT 1
        """
        cursor.execute(query, (f"%{product_name.lower()}%",))
        result = cursor.fetchone()

        cursor.close()

        if result and result[0] is not None:
            # Fiyatı formatlayarak döndürelim
            return f"'{product_name}' ürününün fiyatı {result[0]:.2f} TL'dir."
        else:
            return f"'{product_name}' ürününün fiyat bilgisi bulunamadı."
        
    except Exception as e:
        return f"Fiyat bilgisi alınırken veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)


def get_or_upload_image_url(base64_data_url: str, file_name: str) -> str:
    """
    Verilen 'file_name' ile bir görselin Supabase Storage'da olup olmadığını kontrol eder.
    - Varsa: Mevcut görselin public URL'ini döndürür.
    - Yoksa: Verilen Base64 verisini kullanarak görseli yükler ve yeni URL'i döndürür.
    """
    if not supabase:
        raise ConnectionError("Supabase Storage istemcisi düzgün başlatılamadı.")

    bucket_name = "product-images"

    try:
        # 1. Adım: Dosyanın bucket'ta var olup olmadığını kontrol et
        # list() metodu, belirtilen yolda arama yapar. Eşleşen dosya varsa dolu bir liste, yoksa boş bir liste döner.
        existing_files = supabase.storage.from_(bucket_name).list(
            path="",  # Kök dizinde arama yapmak için boş bırakılır
            options={"search": file_name} # HATA BURADA DÜZELTİLDİ
        )

        if existing_files:
            # 2. Adım: Dosya zaten var. Yükleme yapma, sadece URL'i al.
            print(f"✅ Görsel '{file_name}' zaten mevcut. Mevcut URL kullanılıyor.")
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
            return public_url

        # 3. Adım: Dosya mevcut değil. Yükleme işlemini gerçekleştir.
        print(f"🖼️ Görsel '{file_name}' bulunamadı. Yeni yükleme işlemi başlatılıyor...")
        
        # "data:image/png;base64," kısmını ayıkla
        header, encoded_data = base64_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)

        # 'product-images' bucket'ına resmi yüklüyoruz.
        supabase.storage.from_(bucket_name).upload(
            file=image_bytes,
            path=file_name,
            file_options={"content-type": "image/png"} # veya header'dan mime type alabilirsiniz
        )

        # Yüklenen resmin genel (public) URL'ini alıyoruz.
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)

        print(f"✅ Görsel Supabase Storage'a başarıyla yüklendi. URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Supabase Storage işlemi sırasında hata: {e}")
        # Hata durumunda, belki de dosya zaten var ama başka bir sorun oldu.
        # Bu durumu daha detaylı ele almak gerekebilir.
        # Örneğin, 'Duplicate' hatası alırsanız bu da dosyanın var olduğu anlamına gelir.
        if "Duplicate" in str(e):
             print("⚠️ Yükleme hatası 'Duplicate' içeriyor. Dosya muhtemelen zaten var. URL yeniden alınıyor.")
             return supabase.storage.from_(bucket_name).get_public_url(file_name)
        raise e
