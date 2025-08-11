from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from fastapi import FastAPI, HTTPException

from api.match import CorpusIndex, build_index, topk_lexical, topk_semantic
from api.split import sentence_alignment
from api.data import load_wikipedia_docs
from api.models.response import CompareMethodResult, CompareResponse, DocSentences, SentencePair
from api.models.request import CompareRequest
from utils.config import TOP_K_MAX

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Letrus - Detector de plágio")


@lru_cache(maxsize=1)
def get_index() -> CorpusIndex:
    docs = load_wikipedia_docs()
    ids = [d.id for d in docs]
    titles = [d.title for d in docs]
    texts = [d.text for d in docs]
    logger.info("Building corpus index: %d docs", len(docs))
    return build_index(ids, titles, texts)


@app.get("/health")
async def health():
    idx = get_index()
    return {"status": "ok", "corpus_size": len(idx.ids)}


@app.post("/compare", response_model=CompareResponse)
async def compare(payload: CompareRequest) -> CompareResponse:
    if payload.top_k > TOP_K_MAX:
        raise HTTPException(status_code=400, detail=f"top_k máximo é {TOP_K_MAX}")

    idx = get_index()
    k = min(payload.top_k, len(idx.ids))

    lex_docs = topk_lexical(idx, payload.text, k)
    sem_docs = topk_semantic(idx, payload.text, k)

    def build_doc_groups(doc_ids: List[int]) -> List[DocSentences]:
        if not payload.detail:
            return []
        groups: List[DocSentences] = []
        for doc_id in doc_ids:
            pos = idx.ids.index(doc_id)
            title = idx.titles[pos]
            text = idx.texts[pos]
            sent_align = sentence_alignment(idx, payload.text, text, top_n=5)
            sentences = [
                SentencePair(
                    doc_sentence=m["doc_sentence"],
                    doc_start=m["doc_start"],
                    doc_end=m["doc_end"],
                    query_sentence=m["query_sentence"],
                    query_start=m["query_start"],
                    query_end=m["query_end"],
                    score=m["score"],
                )
                for m in sent_align
            ]
            # ordenar sentenças por score desc
            sentences.sort(key=lambda s: s.score, reverse=True)
            groups.append(DocSentences(doc_id=doc_id, doc_title=title, sentences=sentences))
        return groups

    items = [
        CompareMethodResult(method="lexical", docs=build_doc_groups([d for d, _ in lex_docs])),
        CompareMethodResult(method="semantic", docs=build_doc_groups([d for d, _ in sem_docs])),
    ]

    return CompareResponse(query_len=len(payload.text), corpus_size=len(idx.ids), items=items)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
