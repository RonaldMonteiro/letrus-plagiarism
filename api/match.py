from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from api.models.corpus import CorpusIndex
from utils.config import LEXICAL_CHAR_WEIGHT
from utils.encoder import SemanticEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

encoder = SemanticEncoder()


def build_index(ids: List[int], titles: List[str | None], texts: List[str]) -> CorpusIndex:
    # Word-level TF-IDF (inclui unigrams e bigrams, mantém termos raros min_df=1, sublinear_tf)
    tfidf_word = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=60000, sublinear_tf=True)
    tfidf_word_matrix = tfidf_word.fit_transform(texts)

    # Char n-grams (wb para respeitar fronteiras; 3-5 captura radicais e variações pequenas)
    tfidf_char = None
    tfidf_char_matrix = None
    if LEXICAL_CHAR_WEIGHT > 0:
        tfidf_char = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), min_df=1, max_features=60000, sublinear_tf=True)
        tfidf_char_matrix = tfidf_char.fit_transform(texts)

    # Embeddings
    embed_matrix = encoder.encode(texts)

    return CorpusIndex(
        ids=ids,
        titles=titles,
        texts=texts,
        tfidf_word_vectorizer=tfidf_word,
        tfidf_word_matrix=tfidf_word_matrix,
        tfidf_char_vectorizer=tfidf_char,
        tfidf_char_matrix=tfidf_char_matrix,
        embed_matrix=embed_matrix,
    )


def _combine_lexical_scores(word_scores: np.ndarray, char_scores: np.ndarray | None) -> np.ndarray:
    if char_scores is None or LEXICAL_CHAR_WEIGHT <= 0:
        return word_scores
    w = max(0.0, min(1.0, LEXICAL_CHAR_WEIGHT))
    return (1 - w) * word_scores + w * char_scores


def topk_lexical(index: CorpusIndex, query: str, k: int = 5) -> List[Tuple[int, float]]:
    # Word scores
    q_word = index.tfidf_word_vectorizer.transform([query])
    word_sims = cosine_similarity(q_word, index.tfidf_word_matrix).ravel()
    # Char scores (optional)
    char_sims = None
    if index.tfidf_char_vectorizer is not None and index.tfidf_char_matrix is not None:
        q_char = index.tfidf_char_vectorizer.transform([query])
        char_sims = cosine_similarity(q_char, index.tfidf_char_matrix).ravel()
    sims = _combine_lexical_scores(word_sims, char_sims)
    top_idx = np.argsort(-sims)[:k]
    return [(int(index.ids[i]), float(sims[i])) for i in top_idx]


def topk_semantic(index: CorpusIndex, query: str, k: int = 5) -> List[Tuple[int, float]]:
    q_vec = encoder.encode([query])[0].reshape(1, -1)
    sims = cosine_similarity(q_vec, index.embed_matrix).ravel()
    top_idx = np.argsort(-sims)[:k]
    return [(int(index.ids[i]), float(sims[i])) for i in top_idx]