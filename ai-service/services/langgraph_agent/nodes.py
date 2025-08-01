# Bu dosya, grafiğin mantığını içeren düğüm fonksiyonlarını (call_model, should_continue) barındırır.

import json
from typing import Literal, Dict, Any
import time
import re
import hashlib
import os
from typing import Literal, Dict, Any
from threading import Lock

from .graph_state import GraphState
from langchain_core.messages import ToolMessage, SystemMessage, AIMessage, HumanMessage

class PersistentCacheManager:
    # 1 günlükj cache süresi (TTL) ve maksimum önbellek boyutu
    # Bu değerler, uygulama başlatıldığında ayarlanır ve değiştirilebilir.
    # TTL: 86400 saniye (1 gün)
    # max_size: 100 öğe
    def __init__(self, cache_file='faq_cache.json', ttl=86400, max_size=100):
        self.cache_file = cache_file
        self.ttl = ttl
        self.max_size = max_size
        self._cache = self._load_cache()
        self._lock = Lock()  # Dosya işlemlerini thread-safe yapmak için

    def _load_cache(self) -> dict:
        """JSON dosyasından önbelleği yükler."""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Dosya bozuksa veya okunamıyorsa boş bir önbellekle başla
            return {}

    def _save_cache(self):
        """Önbelleği JSON dosyasına kaydeder."""
        with self._lock:
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, indent=4)
            except IOError as e:
                print(f"❌ Önbellek dosyası yazılamadı: {e}")

    def get(self, key: str) -> Any | None:
        """Önbellekten bir değer alır ve TTL kontrolü yapar."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        cached_response, timestamp = entry['response'], entry['timestamp']
        
        # TTL kontrolü - önbellek süresi dolmuş mu?
        if time.time() - timestamp > self.ttl:
            print(f"⏳ Önbellek süresi doldu: '{key}'")
            del self._cache[key]
            self._save_cache()
            return None
            
        return cached_response

    def set(self, key: str, value: Any):
        """Önbelleğe yeni bir değer ekler ve boyut kontrolü yapar."""
        # Önbellek boyut kontrolü
        if len(self._cache) >= self.max_size and key not in self._cache:
            # En eski girdiyi bul ve sil
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]
        
        self._cache[key] = {
            "response": value,
            "timestamp": time.time()
        }
        self._save_cache()


# Bu nesne, uygulama çalıştığı sürece bir kez oluşturulur ve kullanılır.
cache_manager = PersistentCacheManager()

def normalize_query(query: str) -> str:
    """
    Kullanıcı sorgusunu önbellek araması için normalleştir.
    Noktalama işaretlerini kaldır, lowercase yap.
    """
    # Noktalama işaretlerini kaldır
    normalized = re.sub(r'[^\w\s]', '', query.lower())
    # Gereksiz boşlukları temizle
    normalized = " ".join(normalized.split())
    return normalized

def generate_query_hash(query: str) -> str:
    """Normalleştirilmiş sorgudan benzersiz bir hash oluştur."""
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def check_cache(state: GraphState) -> dict:
    """
    Sık sorulan sorular için önbellek kontrolü.
    Eğer soru daha önce sorulmuş ve cevabı önbellekte varsa,
    grafiği LLM'e yönlendirmeden hemen cevabı döndürür.
    
    Önbellek hit olursa büyük bir performans ve maliyet kazancı sağlar.
    """
    # Son kullanıcı mesajını al
    last_message = next((msg for msg in reversed(state["messages"]) if hasattr(msg, 'content')), None)
    if not last_message or not last_message.content or len(last_message.content) < 5:
        return {}
    
    query = last_message.content
    query_hash = generate_query_hash(query)
    
    cached_response = cache_manager.get(query_hash)
    
    if cached_response:
        print(f"🎯 Önbellek HIT: '{query}'")
        return {
            "messages": [AIMessage(content=f"{cached_response}")],
            "cached": True
        }
    
    print(f"❓ Önbellek MISS: '{query}'")
    return {}

# YENİ: Önbelleğe yazma işini yapan özel bir düğüm
def cache_final_answer(state: GraphState) -> dict:
    """
    Grafiğin sonunda, nihai AI yanıtını önbelleğe alır.
    """

    # 1. Cevabı oluşturmak için hangi araçların kullanıldığını bul.
    # Sohbet geçmişinde geriye doğru giderek tool_calls içeren son AIMessage'ı bul.
    tool_calls = []
    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and message.tool_calls:
            tool_calls = message.tool_calls
            break
    
    # 2. Kullanılan araçların isimlerini bir listeye al.
    called_tool_names = {call['name'] for call in tool_calls}
    
    # 3. Eğer stok sorgulama aracı kullanıldıysa, önbelleğe ALMA.
    if 'get_stock_info_tool' in called_tool_names:
        print("ℹ️ Yanıt, anlık stok bilgisi içerdiği için önbelleğe alınmayacak.")
        return {} # Fonksiyonu burada sonlandır.
        
    # 4. Stok aracı kullanılmadıysa, normal önbelleğe alma işlemini yap.
    last_message = state["messages"][-1]


    final_content = last_message.content

    # Hata veya olumsuz sonuç belirten anahtar kelimeleri tanımla
    # Bu liste, önbelleğe alınmasını istemediğimiz durumları kapsar.
    error_keywords = [
        "sorun yaşandı",
        "hata oluştu",
        "bulunamadı",
        "başvurun",  # "sistem yöneticisine başvurun" gibi ifadeler için
        "üzgünüm"   # "Üzgünüm, ... gibi ifadeler için"
    ]


    if isinstance(last_message, AIMessage) and last_message.content:
        if any(keyword in final_content.lower() for keyword in error_keywords):
            # Ekrana log basarken yanıtın sadece bir kısmını göstererek terminali temiz tutalım.
            print(f"🚫 Hatalı/olumsuz yanıt önbelleğe alınmayacak: '{final_content[:70]}...'")
            return {}  # Önbelleğe almadan fonksiyonu sonlandır

        # 4. Yanıt temizse, normal önbelleğe alma işlemini yap
        # Artık stok kontrolü gibi eski mantıklara gerek yok.
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if user_messages:
            last_user_query = user_messages[-1].content
            query_hash = generate_query_hash(last_user_query)
            cache_manager.set(query_hash, final_content)
            print(f"💾 Önbelleğe eklendi: '{last_user_query}'")
                
    return {}


def summarize_tool_outputs(state: GraphState):
    """
    Araçlardan gelen çıktıları akıllıca birleştirir.
    - Başarılı sonuçları listeler.
    - "Bulunamadı" veya "tükendi" gibi bilgilendirici ama "başarısız" olmayan sonuçları doğru şekilde ekler.
    - Tavsiye aracından gelen boş sonuçları tamamen görmezden gelerek sessiz kalmasını sağlar.
    - Gerçek veritabanı hatalarını belirtir.
    """
    messages = state["messages"]
    
    # Sadece bu döngüyle ilgili ToolMessage'ları al
    last_agent_message = next((msg for msg in reversed(messages) if hasattr(msg, 'tool_calls') and msg.tool_calls), None)
    if not last_agent_message:
        return {}
    tool_call_ids = {tc['id'] for tc in last_agent_message.tool_calls}
    tool_outputs = [msg for msg in messages if isinstance(msg, ToolMessage) and msg.tool_call_id in tool_call_ids]
    
    if not tool_outputs:
        return {}

    summary_lines = []
    for output in tool_outputs:
        content = output.content.strip() if output.content else ""
        tool_name = output.name

        # 1. Tavsiye aracından gelen boş cevabı tamamen yoksay.
        if tool_name == 'get_recommendations_tool' and not content:
            continue  # Bu çıktıyı özete hiç ekleme.

        # 2. Gerçek bir veritabanı hatası varsa belirt.
        if "hatası oluştu" in content:
            summary_lines.append(f"- {tool_name} kullanılırken bir sorun yaşandı.")
        # 3. Anlamlı bir sonuç varsa (boş değilse) ekle.
        #    Bu, "stok tükendi" veya "ürün bulunamadı" gibi geçerli bilgileri de kapsar.
        elif content:
            summary_lines.append(f"- {content}")

    # Özetlenecek anlamlı bir bilgi yoksa, sonraki adımı karıştırmamak için boş dön.
    if not summary_lines:
        return {}

    summary = "Araçlardan şu bilgiler toplandı:\n" + "\n".join(summary_lines)
    
    print(f"📋 Akıllı Özetleme Tamamlandı:\n{summary}")

    return {"messages": [SystemMessage(content=summary)]}


def call_model(state: GraphState, model_with_tools):
    """
    LLM'i (yapay zeka modelini) çağıran ana düğüm.
    Modeli dışarıdan parametre olarak alarak daha esnek bir yapı sunar.
    """
    # Mevcut sohbet geçmişini al
    messages = state["messages"]
    # Modeli bu geçmişle çağır ve yanıtını al
    response = model_with_tools.invoke(messages)
    # Gelen yanıtı mesaj listesine eklenmek üzere döndür
    return {"messages": [response]}

def validate_input(state: GraphState) -> dict:
    """
    Kullanıcı girdisini doğrular ve temizler.
    Zararlı içerik, çok uzun mesajlar veya boş girdileri kontrol eder.
    """
    last_message = state["messages"][-1]
    content = last_message.content
    
    # Boş girdi kontrolü
    if not content or content.strip() == "":
        return {
            "messages": [
                {"role": "assistant", "content": "Lütfen bir soru veya mesaj yazın."}
            ],
            "validation_error": True
        }
    
    # Çok uzun mesaj kontrolü
    if len(content) > 1000:
        return {
            "messages": [
                {"role": "assistant", "content": "Mesajınız çok uzun. Lütfen daha kısa bir mesaj gönderin."}
            ],
            "validation_error": True
        }
    
    # Zararlı içerik kontrolü (geliştirilmiş)
    harmful_keywords = ["hack", "spam", "virus", "malware", "phishing", "scam"]
    if any(keyword in content.lower() for keyword in harmful_keywords):
        return {
            "messages": [
                {"role": "assistant", "content": "Bu tür içerikler için yardım sağlayamam. Lütfen uygun bir soru sorun."}
            ],
            "validation_error": True
        }
    
    # Rate limiting kontrolü (IP bazlı veya session bazlı)
    if len(content.split()) > 200:  # Çok fazla kelime
        return {
            "messages": [
                {"role": "assistant", "content": "Lütfen daha kısa ve öz bir mesaj gönderin."}
            ],
            "validation_error": True
        }
    
    # Başarılı validasyon
    return {
        "validated": True,
        "validation_error": False
    }

def enhanced_should_continue(state: GraphState) -> Literal["tools", "error", "cache_and_end"]:
    """
    Basitleştirilmiş karar verme mantığı - sadece tools, error, veya end.
    """
    if state.get("cached") or state.get("validation_error"):
        return "cache_and_end"
    
    last_message = state["messages"][-1]

    if state.get("error"):
        return "error"
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    return "cache_and_end"




