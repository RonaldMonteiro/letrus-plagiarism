import numpy as np
from typing                import List
from utils.config          import MODEL_NAME
from sentence_transformers import SentenceTransformer


class SemanticEncoder:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name, device="cpu")

    def encode(self, texts: List[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        )