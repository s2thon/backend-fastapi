# Python'un hafif ve modern bir versiyonunu temel al
FROM python:3.11-slim

# Konteyner içinde çalışacağımız dizini belirle
WORKDIR /app

# Sadece bağımlılık dosyasını kopyala. Bu, Docker'ın önbellekleme mekanizmasını
# daha verimli kullanmasını sağlar. Kod değişse bile bağımlılıklar değişmediyse
# bu adımı tekrar çalıştırmaz.
COPY requirements.txt .

# requirements.txt içindeki tüm Python kütüphanelerini kur
RUN pip install --no-cache-dir -r requirements.txt

# Bağımlılıklar kurulduktan sonra, projenin geri kalan tüm kodunu kopyala
COPY . .

# FastAPI'nin 8001 portunda çalışacağını Docker'a bildir
EXPOSE 8001

# Konteyner başladığında çalıştırılacak olan ana komut
# Uvicorn'u, konteyner dışından gelen isteklere izin verecek şekilde (--host 0.0.0.0) başlatır
CMD ["uvicorn", "ai-service.main:app", "--host", "0.0.0.0", "--port", "8001"]