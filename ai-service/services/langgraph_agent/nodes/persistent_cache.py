import json
import os
import time
from threading import Lock

class PersistentCacheManager:
    """JSON dosyası tabanlı, TTL ve boyut sınırlı bir önbellek yöneticisi."""
    def __init__(self, cache_file='faq_cache.json', ttl=86400, max_size=100):
        self.cache_file = cache_file
        self.ttl = ttl
        self.max_size = max_size
        self._cache = self._load_cache()
        self._lock = Lock()

    def _load_cache(self) -> dict:
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_cache(self):
        with self._lock:
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, indent=4)
            except IOError as e:
                print(f"❌ Önbellek dosyası yazılamadı: {e}")

    def get(self, key: str):
        entry = self._cache.get(key)
        if not entry:
            return None
        
        if time.time() - entry['timestamp'] > self.ttl:
            print(f"⏳ Önbellek süresi doldu: '{key}'")
            del self._cache[key]
            self._save_cache()
            return None
            
        return entry['response']

    def set(self, key: str, value):
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]
        
        self._cache[key] = {
            "response": value,
            "timestamp": time.time()
        }
        self._save_cache()