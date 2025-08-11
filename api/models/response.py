from __future__ import annotations

from pydantic   import BaseModel, Field
from typing     import List, Optional


class SentencePair(BaseModel):
    doc_sentence: str
    doc_start: int
    doc_end: int
    query_sentence: str
    query_start: int
    query_end: int
    score: float


class DocSentences(BaseModel):
    doc_id: int = Field(..., description="ID do documento")
    doc_title: Optional[str] = Field(None, description="Título do documento")
    sentences: List[SentencePair]


class CompareMethodResult(BaseModel):
    method: str
    docs: List[DocSentences]


class CompareResponse(BaseModel):
    query_len: int
    corpus_size: int
    items: List[CompareMethodResult]