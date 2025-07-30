# services/db_pool.py

import os
import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()

# Uygulama boyunca yaşayacak olan bağlantı havuzumuz.
# minconn=1, maxconn=10 -> Başlangıçta 1, en fazla 10 bağlantı aç.
db_pool = None

def initialize_pool():
    """Uygulama başlatıldığında çağrılacak olan fonksiyon."""
    global db_pool
    if db_pool is None:
        try:
            print("🗄️ Veritabanı bağlantı havuzu oluşturuluyor...")
            db_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10, # İhtiyacınıza göre ayarlayın
                host=os.getenv("HOST"),
                port=os.getenv("PORT"),
                dbname=os.getenv("DBNAME"),
                user=os.getenv("USER"),
                password=os.getenv("PASSWORD")
            )
            print("✅ Veritabanı bağlantı havuzu başarıyla oluşturuldu.")
        except Exception as e:
            print(f"❌ Veritabanı havuzu oluşturulurken hata: {e}")
            db_pool = None

def get_db_connection():
    """Havuzdan bir veritabanı bağlantısı alır."""
    if db_pool is None:
        raise ConnectionError("Veritabanı havuzu başlatılmamış!")
    return db_pool.getconn()

def release_db_connection(conn):
    """Kullanılan bir bağlantıyı havuza geri bırakır."""
    if db_pool:
        db_pool.putconn(conn)

# Uygulama ilk yüklendiğinde havuzu başlat
initialize_pool()