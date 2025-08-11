from __future__ import annotations
import numpy as np

from typing                          import List
from dataclasses                     import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class CorpusIndex:
    ids: List[int]
    titles: List[str | None]
    texts: List[str]
    tfidf_word_vectorizer: TfidfVectorizer
    tfidf_word_matrix: np.ndarray
    tfidf_char_vectorizer: TfidfVectorizer | None
    tfidf_char_matrix: np.ndarray | None
    embed_matrix: np.ndarray