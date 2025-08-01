import os
import base64
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from supabase import create_client, Client
from functools import lru_cache
from urllib.parse import quote_plus

# --- 1. İstemci Başlatma ve Yönetim ---

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# Global değişkenler: Biri veritabanı havuzu, diğeri Supabase'in genel istemcisi için
db_pool = None
supabase: Client = None

def initialize_clients():
    """
    Uygulama başladığında çalıştırılacak olan her iki istemciyi de başlatır.
    - Psycopg2 Bağlantı Havuzu: Verimli, doğrudan SQL sorguları için.
    - Supabase Client: Storage gibi yüksek seviyeli işlemler için.
    """
    global db_pool, supabase

    # --- Psycopg2 Bağlantı Havuzunu Başlat ---
    if db_pool is None:
        try:
            user = os.getenv("USER")
            password = os.getenv("PASSWORD")
            host = os.getenv("HOST")
            port = os.getenv("PORT")
            dbname = os.getenv("DBNAME")

            if not all([user, password, host, port, dbname]):
                raise ValueError("USER, PASSWORD, HOST, PORT ve DBNAME .env dosyasında tanımlı olmalı!")
            

            # --- ANA DÜZELTME BURADA ---
            # Şifredeki '@' gibi özel karakterleri güvenli formata dönüştür.
            encoded_password = quote_plus(password)

            db_url = f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"

            db_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=db_url)
            print("✅ Veritabanı bağlantı havuzu (psycopg2) başarıyla başlatıldı.")
        except (ValueError, psycopg2.Error) as e:
            print(f"❌ Veritabanı bağlantı havuzu başlatılamadı: {e}")
            db_pool = None

    # --- Supabase Python İstemcisini Başlat ---
    if supabase is None:
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL ve SUPABASE_KEY .env dosyasında tanımlı olmalı!")
            supabase = create_client(supabase_url, supabase_key)
            print("✅ Supabase istemcisi (Storage için) başarıyla oluşturuldu.")
        except (ValueError, Exception) as e:
            print(f"❌ Supabase istemcisi oluşturulurken hata: {e}")
            supabase = None


def get_db_connection():
    """
    Bağlantı havuzundan geçerli bir veritabanı bağlantısı alır.
    Bağlantının kopuk olup olmadığını kontrol eder ve gerekirse yeniler.
    """
    if not db_pool:
        raise ConnectionError("Veritabanı havuzu başlatılmamış veya kullanılamıyor.")
    
    conn = db_pool.getconn()
    try:
        # Bağlantının hala canlı olup olmadığını kontrol etmenin en basit yolu
        # boş bir sorgu çalıştırmaktır.
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        # Eğer buraya kadar hata almadıysak, bağlantı sağlamdır.
        return conn
    except psycopg2.OperationalError:
        # Bağlantı kopmuş! Havuzdan bu bozuk bağlantıyı kaldır ve yenisini al.
        print("⚠️ Kopuk veritabanı bağlantısı tespit edildi. Yenileniyor...")
        db_pool.putconn(conn, close=True) # close=True ile bağlantıyı tamamen kapat
        return db_pool.getconn() # Yeni bir bağlantı al ve döndür
    except Exception as e:
        # Beklenmedik başka bir hata olursa, bağlantıyı geri bırak ve hatayı yükselt
        release_db_connection(conn)
        raise e


def release_db_connection(conn):
    """Kullanılan bir veritabanı bağlantısını havuza geri bırakır."""
    if db_pool:
        db_pool.putconn(conn)




def shutdown_clients():
    """Uygulama kapandığında tüm bağlantıları ve istemcileri kapatır."""
    global db_pool, supabase
    if db_pool:
        db_pool.closeall()
        print("ℹ️ Tüm veritabanı bağlantıları kapatıldı.")
        db_pool = None
    supabase = None # Supabase istemcisinin özel bir kapatma metodu yoktur.
    print("ℹ️ Supabase istemcisi temizlendi.")




# --- 2. LangGraph İçin Veritabanı Araç Fonksiyonları (Doğrudan SQL) ---

@lru_cache(maxsize=128)
def get_price_info(product_name: str) -> str:
    """Bir ürünün fiyatını veritabanından alır."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT price FROM product WHERE unaccent(product_name) ILIKE unaccent(%s) LIMIT 1"
            cursor.execute(query, (f'%{product_name}%',))
            result = cursor.fetchone()
            
            if result and result[0] is not None:
                return f"'{product_name}' ürününün güncel fiyatı {result[0]:.2f} TL'dir."
            else:
                return f"Üzgünüm, sistemimizde '{product_name}' adlı bir ürün bulunamadı veya fiyat bilgisi mevcut değil. Lütfen ürün adını kontrol edip tekrar deneyin veya farklı bir ürün sorgulaması yapın."
    except Exception as e:
        return f"Fiyat bilgisi alınırken bir veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)



@lru_cache(maxsize=128)
def get_stock_info(product_name: str) -> str:
    """Bir ürünün stok adedini veritabanından alır."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT quantity_in_stock FROM product WHERE unaccent(product_name) ILIKE unaccent(%s) LIMIT 1"
            cursor.execute(query, (f'%{product_name}%',))
            result = cursor.fetchone()
            
            if result and result[0] is not None:
                if result[0] > 0:
                    return f"Evet, '{product_name}' ürününden stoklarımızda {result[0]} adet mevcuttur."
                else:
                    return f"Üzgünüz, '{product_name}' ürünü şu anda stoklarımızda tükenmiştir."
            else:
                return f"'{product_name}' adında bir ürün bulunamadı."
    except Exception as e:
        return f"Stok bilgisi alınırken bir veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)



@lru_cache(maxsize=128)
def get_payment_amount(order_id: int) -> str:
    """Belirtilen sipariş ID'sine ait ödeme tutarını alır."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT amount FROM payment WHERE order_id = %s LIMIT 1"
            cursor.execute(query, (order_id,))
            result = cursor.fetchone()
            
            if result and result[0] is not None:
                return f"'{order_id}' numaralı siparişin ödeme tutarı {result[0]:.2f} TL'dir."
            else:
                return f"'{order_id}' numaralı sipariş için ödeme bilgisi bulunamadı."
    except Exception as e:
        return f"Ödeme bilgisi alınırken bir veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)



@lru_cache(maxsize=128)
def get_item_status(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki belirli bir ürünün durumunu alır."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            SELECT oi.item_status 
            FROM order_item AS oi
            JOIN product AS p ON oi.product_id = p.id
            WHERE oi.order_id = %s AND unaccent(p.product_name) ILIKE unaccent(%s)
            LIMIT 1;
            """
            cursor.execute(query, (order_id, f'%{product_name}%'))
            result = cursor.fetchone()
            
            if result and result[0]:
                return f"'{order_id}' numaralı siparişinizdeki '{product_name}' ürününün durumu: {result[0]}."
            else:
                return f"'{order_id}' numaralı siparişinizde '{product_name}' adında bir ürün bulunamadı."
    except Exception as e:
        return f"Ürün durumu alınırken bir veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)



@lru_cache(maxsize=128)
def get_refund_status(order_id: int, product_name: str) -> str:
    """Belirli bir siparişteki belirli bir ürünün iade durumunu alır."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            SELECT oi.refund_status 
            FROM order_item AS oi
            JOIN product AS p ON oi.product_id = p.id
            WHERE oi.order_id = %s AND unaccent(p.product_name) ILIKE unaccent(%s)
            LIMIT 1;
            """
            cursor.execute(query, (order_id, f'%{product_name}%'))
            result = cursor.fetchone()
            
            if result and result[0]:
                return f"'{order_id}' numaralı siparişinizdeki '{product_name}' ürününün iade durumu: {result[0]}."
            else:
                return f"'{order_id}' numaralı siparişinizde '{product_name}' ürünü için iade bilgisi bulunamadı."
    except Exception as e:
        return f"İade durumu alınırken bir veritabanı hatası oluştu: {str(e)}"
    finally:
        if conn:
            release_db_connection(conn)


@lru_cache(maxsize=128)
def get_product_recommendations(product_name: str) -> str:
    """
    Bir ürüne benzer veya onunla ilişkili diğer ürünleri önerir.
    Eğer öneri bulunamazsa veya bir hata olursa, boş bir string döndürerek "sessiz" kalır.
    """
    conn = None
    try:
        conn = get_db_connection()
        # Hata ayıklama için ekstra log
        print(f"🔍 Öneri için ürün aranıyor: '{product_name}'")
        
        with conn.cursor() as cursor:
            # 1. Verilen ürünün kategorisini bul
            query_category = """
            SELECT category_id FROM product WHERE unaccent(product_name) ILIKE unaccent(%s) LIMIT 1
            """
            cursor.execute(query_category, (f'%{product_name}%',))
            category_result = cursor.fetchone()

            # Ürün veya kategori bulunamazsa sessizce çık
            if not category_result:
                print(f"⚠️ Kategori bulunamadı: '{product_name}'")
                return ""

            category_id = category_result[0]
            print(f"✅ Kategori bulundu: {category_id}")

            # 2. Aynı kategorideki diğer 3 popüler ürünü bul (kendisi hariç)
            query_recommendations = """
            SELECT product_name FROM product 
            WHERE category_id = %s AND unaccent(product_name) NOT ILIKE unaccent(%s)
            ORDER BY quantity_in_stock DESC, product_name
            LIMIT 3;
            """
            cursor.execute(query_recommendations, (category_id, f'%{product_name}%'))
            recommendations = cursor.fetchall()

            # Öneri bulunamazsa sessizce çık
            if not recommendations:
                print(f"⚠️ Bu kategoride başka ürün bulunamadı: {category_id}")
                return ""

            recommended_names = [rec[0] for rec in recommendations]
            result = f"Bu ürünle ilgilenenler şunları da beğendi: {', '.join(recommended_names)}."
            print(f"✅ Öneri başarılı: {result}")
            return result

    except Exception as e:
        print(f"❌ Ürün önerisi alınırken bir hata oluştu: {str(e)}")
        return ""
    finally:
        if conn:
            release_db_connection(conn)





# --- 3. Supabase Storage Fonksiyonu (Yüksek Seviye İstemci) ---

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
