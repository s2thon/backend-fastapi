# app/tools/__init__.py

"""
Bu __init__ dosyası, 'tools' paketindeki tüm araçları bir araya getirir
ve dışarıdan kolayca erişilebilen tek bir 'all_tools' listesi olarak sunar.
"""

# Her aracı kendi özel modülünden import et
from .get_product_details_tool import get_product_details_tool
from .get_payment_amount_tool import get_payment_amount_tool
from .get_item_status_tool import get_item_status_tool
from .get_refund_status_tool import get_refund_status_tool
from .search_documents_tool import search_documents_tool
from .validate_user_input_tool import validate_user_input_tool
from .content_filter_tool import content_filter_tool

# Diğer modüllerin (orkestratör gibi) kullanması için tüm araçları tek bir listede topla
all_tools = [
    get_product_details_tool,
    get_payment_amount_tool,
    get_item_status_tool,
    get_refund_status_tool,
    search_documents_tool,
    validate_user_input_tool,
    content_filter_tool,
]

# İyi bir pratik olarak, dışa aktarılacakları __all__ listesinde belirtelim.
# "from .tools import *" kullanıldığında sadece all_tools'un import edilmesini sağlar.
__all__ = ["all_tools"]