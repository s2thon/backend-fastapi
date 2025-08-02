# app/nodes/__init__.py

"""
Bu __init__ dosyası, 'nodes' paketindeki tüm düğüm fonksiyonlarını bir araya getirir
ve dışarıdan kolayca erişilebilen bir 'all_nodes' sözlüğü ve 'enhanced_should_continue' 
fonksiyonu olarak sunar.
"""

# Her düğümü ve yardımcı fonksiyonu kendi modülünden import et
from .check_cache import check_cache
from .cache_final_answer import cache_final_answer
from .summarize_tool_outputs import summarize_tool_outputs
from .call_model import call_model
from .validate_input import validate_input
from .enhanced_should_continue import enhanced_should_continue

# Orkestratörde kolay kullanım için düğümleri bir SÖZLÜK içinde toplayalım.
# Anahtar: Grafikteki düğüm adı (string)
# Değer: Çalıştırılacak fonksiyonun kendisi
all_nodes = {
    "cache": check_cache,
    "validate": validate_input,
    "agent": call_model,  # Bu düğüm orkestratörde özel olarak ele alınacak
    "summarize": summarize_tool_outputs,
    "cache_and_end": cache_final_answer,
}

# Dışa aktarılacakları belirtelim.
# enhanced_should_continue bir düğüm değil, bir kenar (edge) koşulu olduğu için ayrı tutuyoruz.
__all__ = [
    "all_nodes",
    "enhanced_should_continue"
]