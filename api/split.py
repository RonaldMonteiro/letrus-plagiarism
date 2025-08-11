from __future__ import annotations

import logging
from typing import List
import re

from sklearn.metrics.pairwise import cosine_similarity
from models.corpus import CorpusIndex

logger = logging.getLogger(__name__)

_SENT_SPLIT_RE = re.compile(r'(?<=[\.!?])\s+(?=[A-ZÁÉÍÓÚÀÂÊÔÃÕÜ0-9])')


def _split_sentences_with_offsets(text: str) -> List[tuple[str, int, int]]:
    parts: List[tuple[str, int, int]] = []
    start = 0
    for match in _SENT_SPLIT_RE.finditer(text):
        end = match.start()
        sent = text[start:end].strip()
        if sent:
            parts.append((sent, start, end))
        start = match.end()
    if start < len(text):
        tail = text[start:].strip()
        if tail:
            parts.append((tail, start, len(text)))
    return parts

def sentence_alignment(index: CorpusIndex, query: str, doc_text: str, top_n: int = 5) -> List[dict]:
    q_sents = _split_sentences_with_offsets(query)
    d_sents = _split_sentences_with_offsets(doc_text)
    if not q_sents or not d_sents:
        return []
    q_texts = [s for s, _, _ in q_sents]
    d_texts = [s for s, _, _ in d_sents]
    q_vecs = index.tfidf_word_vectorizer.transform(q_texts)
    d_vecs = index.tfidf_word_vectorizer.transform(d_texts)
    sims = cosine_similarity(q_vecs, d_vecs)
    pairs = []
    for qi in range(sims.shape[0]):
        for di in range(sims.shape[1]):
            sc = sims[qi, di]
            if sc > 0:
                pairs.append((sc, qi, di))
    pairs.sort(reverse=True)
    used_q, used_d = set(), set()
    results = []
    for sc, qi, di in pairs:
        if qi in used_q or di in used_d:
            continue
        q_sent, q_start, q_end = q_sents[qi]
        d_sent, d_start, d_end = d_sents[di]
        results.append({
            'doc_sentence': d_sent,
            'doc_start': d_start,
            'doc_end': d_end,
            'query_sentence': q_sent,
            'query_start': q_start,
            'query_end': q_end,
            'score': float(sc)
        })
        used_q.add(qi)
        used_d.add(di)
        if len(results) >= top_n:
            break
    return results