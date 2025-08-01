# Bu dosya, tüm grafiğin paylaştığı durum (hafıza) yapısını tanımlar.

import operator
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """
    LangGraph akışının durumunu (hafızasını) tanımlayan yapı.
    Sohbet geçmişini bir mesaj listesi olarak tutar.
    'operator.add' sayesinde, her adımda yeni mesajlar listeye eklenir.
    """
    messages: Annotated[list[BaseMessage], operator.add]
    validated: bool = False
    validation_error: bool = False
    error: dict = None
    formatted: bool = False
    user_intent: str = None
    cached: bool = False