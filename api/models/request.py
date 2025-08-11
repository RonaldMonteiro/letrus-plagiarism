from __future__ import annotations

from pydantic   import BaseModel


class CompareRequest(BaseModel):
    text: str
    top_k: int = 5
    detail: bool = True  # se False, retorna estrutura sem matches