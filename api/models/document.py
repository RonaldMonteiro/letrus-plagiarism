from __future__  import annotations
from dataclasses import dataclass
from typing      import Optional


@dataclass
class Document:
    id: int
    title: Optional[str]
    text: str